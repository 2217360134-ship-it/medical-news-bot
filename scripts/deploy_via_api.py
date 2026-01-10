#!/usr/bin/env python3
"""
GitHub API 部署脚本
使用 Personal Access Token (PAT) 创建仓库并推送代码

使用方法:
    python scripts/deploy_via_api.py --token YOUR_TOKEN --username USERNAME --repo REPO_NAME

示例:
    python scripts/deploy_via_api.py --token ghp_xxxxxxxxxxxx --username zhangsan --repo news-bot
"""

import os
import sys
import subprocess
import argparse
import json
import requests
from pathlib import Path

# GitHub API 基础 URL
GITHUB_API_URL = "https://api.github.com"

def create_github_repo(token, username, repo_name, repo_description, private=False):
    """
    使用 GitHub API 创建仓库
    
    Args:
        token: GitHub Personal Access Token
        username: GitHub 用户名或组织名
        repo_name: 仓库名称
        repo_description: 仓库描述
        private: 是否为私有仓库
    
    Returns:
        bool: 创建是否成功
        str: 仓库 URL 或错误信息
    """
    url = f"{GITHUB_API_URL}/repos/{username}/{repo_name}"
    
    # 先检查仓库是否已存在
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    check_response = requests.get(url, headers=headers)
    
    if check_response.status_code == 200:
        print(f"⚠️  仓库 '{repo_name}' 已存在")
        return True, check_response.json().get("clone_url", "")
    elif check_response.status_code != 404:
        print(f"❌ 检查仓库失败: {check_response.status_code}")
        print(f"响应: {check_response.text}")
        return False, check_response.text
    
    # 仓库不存在，创建新仓库
    create_url = f"{GITHUB_API_URL}/user/repos"
    
    data = {
        "name": repo_name,
        "description": repo_description,
        "private": private,
        "auto_init": False,  # 不自动初始化（我们推送代码）
        "has_issues": True,
        "has_projects": True,
        "has_wiki": True
    }
    
    print(f"📦 创建仓库: {repo_name}")
    print(f"   描述: {repo_description}")
    print(f"   私有: {'是' if private else '否'}")
    
    create_response = requests.post(create_url, headers=headers, json=data)
    
    if create_response.status_code == 201:
        print("✅ 仓库创建成功")
        repo_info = create_response.json()
        return True, repo_info.get("clone_url", "")
    else:
        print(f"❌ 仓库创建失败: {create_response.status_code}")
        print(f"响应: {create_response.text}")
        return False, create_response.text

def setup_git_remote(repo_url):
    """
    配置 Git 远程仓库
    
    Args:
        repo_url: 仓库克隆 URL
    
    Returns:
        bool: 配置是否成功
    """
    print(f"🔗 配置 Git 远程仓库: {repo_url}")
    
    # 检查是否已有远程仓库
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"⚠️  已存在远程仓库: {result.stdout.strip()}")
        print(f"是否要更新远程仓库地址? (y/N): ", end="")
        response = input().strip()
        
        if response.lower() == 'y':
            subprocess.run(["git", "remote", "set-url", "origin", repo_url], check=True)
            print("✅ 远程仓库已更新")
        else:
            print("✅ 使用现有远程仓库")
    else:
        subprocess.run(["git", "remote", "add", "origin", repo_url], check=True)
        print("✅ 远程仓库已添加")
    
    return True

def push_to_github(branch="main"):
    """
    推送代码到 GitHub
    
    Args:
        branch: 分支名称
    
    Returns:
        bool: 推送是否成功
    """
    print(f"🚀 推送代码到 GitHub (分支: {branch})")
    
    try:
        # 确保在指定分支
        subprocess.run(["git", "checkout", "-B", branch], check=True, capture_output=True)
        
        # 推送代码
        subprocess.run(
            ["git", "push", "-u", "origin", branch],
            check=True,
            capture_output=True,
            text=True
        )
        
        print("✅ 代码推送成功")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 推送失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def configure_secrets_via_api(token, username, repo_name, secrets):
    """
    使用 GitHub API 配置 Secrets（可选功能）
    
    Args:
        token: GitHub Personal Access Token
        username: GitHub 用户名或组织名
        repo_name: 仓库名称
        secrets: 字典格式的 secrets {key: value}
    
    Returns:
        bool: 配置是否成功
    """
    print("\n🔐 配置 GitHub Secrets...")
    
    base_url = f"{GITHUB_API_URL}/repos/{username}/{repo_name}/actions/secrets"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    import base64
    
    for key, value in secrets.items():
        # 获取 public key（用于加密 secret）
        public_key_url = f"{base_url}/{key}/public-key"
        
        try:
            pk_response = requests.get(public_key_url, headers=headers)
            
            if pk_response.status_code != 200:
                print(f"⚠️  获取 Secret '{key}' 的公钥失败: {pk_response.status_code}")
                continue
            
            public_key = pk_response.json()
            public_key_str = public_key["key"]
            key_id = public_key["key_id"]
            
            # 加密 secret value
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend
            
            public_key_obj = serialization.load_pem_public_key(
                public_key_str.encode(),
                backend=default_backend()
            )
            
            encrypted_value = public_key_obj.encrypt(
                value.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=padding.SHA1()),
                    algorithm=padding.SHA256(),
                    label=None
                )
            )
            
            encrypted_value_b64 = base64.b64encode(encrypted_value).decode()
            
            # 创建或更新 secret
            secret_url = f"{base_url}/{key}"
            secret_data = {
                "encrypted_value": encrypted_value_b64,
                "key_id": key_id
            }
            
            secret_response = requests.put(secret_url, headers=headers, json=secret_data)
            
            if secret_response.status_code in [201, 204]:
                print(f"✅ Secret '{key}' 配置成功")
            else:
                print(f"❌ Secret '{key}' 配置失败: {secret_response.status_code}")
                print(f"响应: {secret_response.text}")
                
        except ImportError:
            print("⚠️  需要安装 cryptography 库才能加密 Secrets")
            print("运行: pip install cryptography")
            break
        except Exception as e:
            print(f"❌ 配置 Secret '{key}' 时出错: {str(e)}")
            continue
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="使用 GitHub API 部署项目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python scripts/deploy_via_api.py --token ghp_xxx --username zhangsan --repo news-bot
  
  # 创建私有仓库
  python scripts/deploy_via_api.py --token ghp_xxx --username zhangsan --repo news-bot --private
  
  # 配置 Secrets（需要安装 cryptography）
  python scripts/deploy_via_api.py --token ghp_xxx --username zhangsan --repo news-bot \\
    --set-secret EMAILS="test@example.com" \\
    --set-secret SMTP_HOST="smtp.qq.com"
        """
    )
    
    parser.add_argument(
        "--token",
        required=True,
        help="GitHub Personal Access Token"
    )
    
    parser.add_argument(
        "--username",
        required=True,
        help="GitHub 用户名或组织名"
    )
    
    parser.add_argument(
        "--repo",
        required=True,
        help="仓库名称"
    )
    
    parser.add_argument(
        "--description",
        default="自动收集医疗器械和医美相关新闻并发送邮件",
        help="仓库描述"
    )
    
    parser.add_argument(
        "--private",
        action="store_true",
        help="创建私有仓库"
    )
    
    parser.add_argument(
        "--branch",
        default="main",
        help="Git 分支名称 (默认: main)"
    )
    
    parser.add_argument(
        "--skip-push",
        action="store_true",
        help="跳过代码推送，只创建仓库"
    )
    
    parser.add_argument(
        "--set-secret",
        action="append",
        help="设置 GitHub Secret，格式: KEY=VALUE (可多次使用)",
        metavar="KEY=VALUE"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("GitHub API 部署脚本")
    print("=" * 60)
    print()
    
    # 步骤 1: 创建仓库
    success, result = create_github_repo(
        token=args.token,
        username=args.username,
        repo_name=args.repo,
        repo_description=args.description,
        private=args.private
    )
    
    if not success:
        print("\n❌ 仓库创建失败，部署终止")
        sys.exit(1)
    
    repo_url = result
    
    # 步骤 2: 配置远程仓库
    if not args.skip_push:
        if not setup_git_remote(repo_url):
            print("\n❌ 配置远程仓库失败")
            sys.exit(1)
        
        # 步骤 3: 推送代码
        if not push_to_github(branch=args.branch):
            print("\n❌ 代码推送失败")
            sys.exit(1)
    else:
        print("\n⏭️  跳过代码推送")
    
    # 步骤 4: 配置 Secrets（可选）
    if args.set_secret:
        secrets = {}
        for secret_pair in args.set_secret:
            if '=' in secret_pair:
                key, value = secret_pair.split('=', 1)
                secrets[key] = value
            else:
                print(f"⚠️  忽略无效的 secret 格式: {secret_pair}")
        
        if secrets:
            configure_secrets_via_api(
                token=args.token,
                username=args.username,
                repo_name=args.repo,
                secrets=secrets
            )
    
    # 完成
    print()
    print("=" * 60)
    print("✅ 部署完成！")
    print("=" * 60)
    print()
    print(f"📦 仓库地址: https://github.com/{args.username}/{args.repo}")
    print(f"🚀 克隆地址: {repo_url}")
    print(f"📋 Actions 页面: https://github.com/{args.username}/{args.repo}/actions")
    print()
    print("下一步：")
    print("1. 进入仓库页面，配置 GitHub Secrets")
    print("2. 启用 GitHub Actions")
    print("3. 手动触发测试或等待定时任务执行")
    print()

if __name__ == "__main__":
    main()
