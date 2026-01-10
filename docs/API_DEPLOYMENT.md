# GitHub API 部署完整示例

## 🚀 快速开始

### 第 1 步：获取 Personal Access Token

参考 [GITHUB_TOKEN_GUIDE.md](./GITHUB_TOKEN_GUIDE.md) 获取你的 GitHub Token。

**注意**：Token 格式类似 `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 第 2 步：确定部署信息

你需要准备以下信息：

| 参数 | 说明 | 示例 |
|------|------|------|
| `TOKEN` | GitHub Personal Access Token | `ghp_1234567890abcdef...` |
| `USERNAME` | GitHub 用户名 | `zhangsan` |
| `REPO_NAME` | 仓库名称 | `news-bot` |

### 第 3 步：选择部署方式

## 方式 1: 使用 Python 脚本（推荐）

### 安装依赖

```bash
pip install requests cryptography
```

### 基本用法

```bash
# 创建公开仓库
python scripts/deploy_via_api.py \\
    --token ghp_xxxxxxxxxxxx \\
    --username zhangsan \\
    --repo news-bot
```

### 创建私有仓库

```bash
python scripts/deploy_via_api.py \\
    --token ghp_xxxxxxxxxxxx \\
    --username zhangsan \\
    --repo news-bot \\
    --private
```

### 指定仓库描述

```bash
python scripts/deploy_via_api.py \\
    --token ghp_xxxxxxxxxxxx \\
    --username zhangsan \\
    --repo news-bot \\
    --description "我的新闻收集机器人"
```

### 只创建仓库，不推送代码

```bash
python scripts/deploy_via_api.py \\
    --token ghp_xxxxxxxxxxxx \\
    --username zhangsan \\
    --repo news-bot \\
    --skip-push
```

### 配置 GitHub Secrets（需要 cryptography 库）

```bash
python scripts/deploy_via_api.py \\
    --token ghp_xxxxxxxxxxxx \\
    --username zhangsan \\
    --repo news-bot \\
    --set-secret "EMAILS=test@example.com" \\
    --set-secret "SMTP_HOST=smtp.qq.com" \\
    --set-secret "SMTP_PORT=587" \\
    --set-secret "SMTP_USER=your-qq@qq.com" \\
    --set-secret "SMTP_PASSWORD=your-auth-code"
```

## 方式 2: 使用 Bash 脚本

### 基本用法

```bash
# 创建公开仓库
bash scripts/deploy_via_api.sh ghp_xxxxxxxxxxxx zhangsan news-bot
```

### 创建私有仓库

```bash
bash scripts/deploy_via_api.sh ghp_xxxxxxxxxxxx zhangsan news-bot --private
```

### 指定仓库描述

```bash
bash scripts/deploy_via_api.sh ghp_xxxxxxxxxxxx zhangsan news-bot \\
    -d "我的新闻收集机器人"
```

### 只创建仓库，不推送代码

```bash
bash scripts/deploy_via_api.sh ghp_xxxxxxxxxxxx zhangsan news-bot --skip-push
```

## 方式 3: 使用 curl 命令

### 创建仓库

```bash
# 设置变量
TOKEN="ghp_xxxxxxxxxxxx"
USERNAME="zhangsan"
REPO_NAME="news-bot"

# 创建仓库的请求数据
JSON_DATA='{
    "name": "'"$REPO_NAME"'",
    "description": "自动收集医疗器械和医美相关新闻并发送邮件",
    "private": false,
    "auto_init": false,
    "has_issues": true,
    "has_projects": true,
    "has_wiki": true
}'

# 创建仓库
curl -X POST \\
    -H "Authorization: token ${TOKEN}" \\
    -H "Accept: application/vnd.github.v3+json" \\
    -H "Content-Type: application/json" \\
    -d "${JSON_DATA}" \\
    https://api.github.com/user/repos
```

### 推送代码

```bash
# 添加远程仓库
git remote add origin https://github.com/${USERNAME}/${REPO_NAME}.git

# 或者如果远程仓库已存在，使用 Token 推送
git remote set-url origin https://${TOKEN}@github.com/${USERNAME}/${REPO_NAME}.git

# 推送代码
git branch -M main
git push -u origin main
```

## 方式 4: 使用 Python requests 库

### 示例代码

```python
import requests
import subprocess
import json

# 配置
TOKEN = "ghp_xxxxxxxxxxxx"
USERNAME = "zhangsan"
REPO_NAME = "news-bot"
DESCRIPTION = "自动收集医疗器械和医美相关新闻并发送邮件"

# GitHub API 基础 URL
API_URL = "https://api.github.com"

# 1. 创建仓库
def create_repo():
    url = f"{API_URL}/user/repos"
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": REPO_NAME,
        "description": DESCRIPTION,
        "private": False,
        "auto_init": False
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print("✅ 仓库创建成功")
        repo_info = response.json()
        return repo_info["clone_url"]
    else:
        print(f"❌ 创建失败: {response.status_code}")
        print(response.text)
        return None

# 2. 推送代码
def push_code(repo_url):
    # 使用 Token 进行认证
    auth_url = repo_url.replace("https://", f"https://{TOKEN}@")
    
    try:
        subprocess.run(["git", "remote", "set-url", "origin", auth_url], check=True)
        subprocess.run(["git", "branch", "-M", "main"], check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
        print("✅ 代码推送成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ 推送失败: {e}")

# 执行
if __name__ == "__main__":
    repo_url = create_repo()
    if repo_url:
        push_code(repo_url)
```

## 🔧 高级用法

### 配置 GitHub Secrets（使用 API）

```python
import requests
import base64
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def set_secret(username, repo_name, secret_name, secret_value, token):
    # 获取公钥
    url = f"https://api.github.com/repos/{username}/{repo_name}/actions/secrets/{secret_name}/public-key"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    public_key = response.json()
    
    # 加密值
    public_key_obj = serialization.load_pem_public_key(
        public_key["key"].encode(),
        backend=default_backend()
    )
    
    encrypted_value = public_key_obj.encrypt(
        secret_value.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=padding.SHA1()),
            algorithm=padding.SHA256(),
            label=None
        )
    )
    
    encrypted_value_b64 = base64.b64encode(encrypted_value).decode()
    
    # 设置 secret
    set_url = f"https://api.github.com/repos/{username}/{repo_name}/actions/secrets/{secret_name}"
    data = {
        "encrypted_value": encrypted_value_b64,
        "key_id": public_key["key_id"]
    }
    
    response = requests.put(set_url, headers=headers, json=data)
    
    if response.status_code in [201, 204]:
        print(f"✅ Secret '{secret_name}' 设置成功")
    else:
        print(f"❌ 设置失败: {response.status_code}")

# 使用示例
set_secret("zhangsan", "news-bot", "EMAILS", "test@example.com", "ghp_xxx")
```

### 检查仓库是否存在

```bash
curl -H "Authorization: token ghp_xxx" \\
     https://api.github.com/repos/zhangsan/news-bot
```

### 列出所有仓库

```bash
curl -H "Authorization: token ghp_xxx" \\
     https://api.github.com/user/repos
```

### 删除仓库

```bash
curl -X DELETE \\
    -H "Authorization: token ghp_xxx" \\
    https://api.github.com/repos/zhangsan/news-bot
```

## 📊 常见场景

### 场景 1: 重新部署已存在的仓库

```bash
# 方式 1: 使用脚本（会检测到仓库已存在）
python scripts/deploy_via_api.py \\
    --token ghp_xxx \\
    --username zhangsan \\
    --repo news-bot

# 方式 2: 手动推送代码
git remote set-url origin https://ghp_xxx@github.com/zhangsan/news-bot.git
git push -u origin main
```

### 场景 2: 部署到组织

```bash
# 使用组织名作为用户名
python scripts/deploy_via_api.py \\
    --token ghp_xxx \\
    --username my-org \\
    --repo news-bot
```

### 场景 3: 批量部署多个项目

```bash
#!/bin/bash
TOKEN="ghp_xxx"
USERNAME="zhangsan"

repos=("project1" "project2" "project3")

for repo in "${repos[@]}"; do
    echo "部署 $repo..."
    python scripts/deploy_via_api.py \\
        --token "$TOKEN" \\
        --username "$USERNAME" \\
        --repo "$repo" \\
        --skip-push
done
```

## ❓ 故障排查

### 问题 1: 401 Unauthorized

**原因**：Token 无效或过期

**解决**：
1. 检查 Token 是否正确复制
2. 确认 Token 未过期
3. 重新生成 Token

### 问题 2: 403 Forbidden

**原因**：Token 权限不足

**解决**：
1. 确认 Token 包含 `repo` 权限
2. 对于 Fine-grained token，确保添加了仓库访问权限

### 问题 3: 422 Unprocessable Entity

**原因**：仓库名已存在或格式错误

**解决**：
1. 检查仓库名是否已存在
2. 确认仓库名符合规范（只包含字母、数字、-、_）

### 问题 4: Git 推送失败

**原因**：网络问题或认证失败

**解决**：
1. 使用 Token 认证：`https://TOKEN@github.com/...`
2. 检查网络连接
3. 使用 SSH 方式（需要配置 SSH 密钥）

## 📚 参考资料

- [GitHub REST API 文档](https://docs.github.com/en/rest)
- [GitHub Actions API](https://docs.github.com/en/rest/actions)
- [Token 指南](./GITHUB_TOKEN_GUIDE.md)
- [部署指南](./DEPLOYMENT.md)

## 🎉 完成部署

部署成功后：

1. 访问你的仓库：https://github.com/USERNAME/REPO_NAME
2. 配置 GitHub Secrets
3. 启用 GitHub Actions
4. 手动触发测试或等待定时任务执行
