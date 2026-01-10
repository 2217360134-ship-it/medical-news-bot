#!/bin/bash

# GitHub API 部署脚本（使用 curl）
# 使用 Personal Access Token (PAT) 创建仓库并推送代码

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    cat << EOF
GitHub API 部署脚本（使用 curl）

使用方法:
    bash scripts/deploy_via_api.sh <TOKEN> <USERNAME> <REPO_NAME> [OPTIONS]

参数:
    TOKEN              GitHub Personal Access Token（必需）
    USERNAME           GitHub 用户名或组织名（必需）
    REPO_NAME          仓库名称（必需）

选项:
    -d, --description  仓库描述（默认: 自动收集医疗器械和医美相关新闻）
    -p, --private      创建私有仓库
    -b, --branch       Git 分支名称（默认: main）
    -s, --skip-push    跳过代码推送，只创建仓库

示例:
    # 基本用法
    bash scripts/deploy_via_api.sh ghp_xxxxxxxxxxxx zhangsan news-bot

    # 创建私有仓库
    bash scripts/deploy_via_api.sh ghp_xxxxxxxxxxxx zhangsan news-bot --private

    # 指定描述
    bash scripts/deploy_via_api.sh ghp_xxxxxxxxxxxx zhangsan news-bot \\
        -d "我的新闻收集机器人"

获取 Personal Access Token:
    https://github.com/settings/tokens

EOF
}

# 检查参数
if [ $# -lt 3 ]; then
    echo -e "${RED}错误: 缺少必需参数${NC}"
    echo ""
    show_help
    exit 1
fi

TOKEN="$1"
USERNAME="$2"
REPO_NAME="$3"

# 默认值
DESCRIPTION="自动收集医疗器械和医美相关新闻并发送邮件"
PRIVATE=false
BRANCH="main"
SKIP_PUSH=false

# 解析选项
shift 3
while [ $# -gt 0 ]; do
    case "$1" in
        -d|--description)
            DESCRIPTION="$2"
            shift 2
            ;;
        -p|--private)
            PRIVATE=true
            shift
            ;;
        -b|--branch)
            BRANCH="$2"
            shift 2
            ;;
        -s|--skip-push)
            SKIP_PUSH=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  GitHub API 部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 步骤 1: 创建仓库
echo -e "${YELLOW}[1/4] 创建 GitHub 仓库...${NC}"

# 检查仓库是否已存在
CHECK_URL="https://api.github.com/repos/${USERNAME}/${REPO_NAME}"
CHECK_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/check_repo.json \
    -H "Authorization: token ${TOKEN}" \
    -H "Accept: application/vnd.github.v3+json" \
    "${CHECK_URL}")
CHECK_CODE="${CHECK_RESPONSE: -3}"

if [ "$CHECK_CODE" = "200" ]; then
    echo -e "${YELLOW}⚠️  仓库 '${REPO_NAME}' 已存在${NC}"
    REPO_URL=$(cat /tmp/check_repo.json | grep -o '"clone_url":"[^"]*"' | cut -d'"' -f4)
elif [ "$CHECK_CODE" = "404" ]; then
    # 仓库不存在，创建新仓库
    CREATE_URL="https://api.github.com/user/repos"
    
    # 构建请求数据
    PRIVATE_FLAG="false"
    if [ "$PRIVATE" = true ]; then
        PRIVATE_FLAG="true"
    fi
    
    JSON_DATA=$(cat <<EOF
{
    "name": "${REPO_NAME}",
    "description": "${DESCRIPTION}",
    "private": ${PRIVATE_FLAG},
    "auto_init": false,
    "has_issues": true,
    "has_projects": true,
    "has_wiki": true
}
EOF
)
    
    echo "📦 创建仓库: ${REPO_NAME}"
    echo "   描述: ${DESCRIPTION}"
    echo "   私有: $( [ "$PRIVATE" = true ] && echo '是' || echo '否' )"
    
    CREATE_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/create_repo.json \
        -X POST \
        -H "Authorization: token ${TOKEN}" \
        -H "Accept: application/vnd.github.v3+json" \
        -H "Content-Type: application/json" \
        -d "${JSON_DATA}" \
        "${CREATE_URL}")
    
    CREATE_CODE="${CREATE_RESPONSE: -3}"
    
    if [ "$CREATE_CODE" = "201" ]; then
        echo -e "${GREEN}✅ 仓库创建成功${NC}"
        REPO_URL=$(cat /tmp/create_repo.json | grep -o '"clone_url":"[^"]*"' | cut -d'"' -f4)
    else
        echo -e "${RED}❌ 仓库创建失败: ${CREATE_CODE}${NC}"
        echo "响应:"
        cat /tmp/create_repo.json
        exit 1
    fi
else
    echo -e "${RED}❌ 检查仓库失败: ${CHECK_CODE}${NC}"
    cat /tmp/check_repo.json
    exit 1
fi

echo ""

# 步骤 2: 配置 Git 远程仓库
if [ "$SKIP_PUSH" = false ]; then
    echo -e "${YELLOW}[2/4] 配置 Git 远程仓库...${NC}"
    
    # 检查是否已有远程仓库
    if git remote get-url origin > /dev/null 2>&1; then
        EXISTING_URL=$(git remote get-url origin)
        echo -e "${YELLOW}⚠️  已存在远程仓库: ${EXISTING_URL}${NC}"
        echo -n "是否要更新远程仓库地址? (y/N): "
        read -r response
        
        if [[ "$response" =~ ^[Yy]$ ]]; then
            git remote set-url origin "${REPO_URL}"
            echo -e "${GREEN}✅ 远程仓库已更新${NC}"
        else
            echo -e "${GREEN}✅ 使用现有远程仓库${NC}"
        fi
    else
        git remote add origin "${REPO_URL}"
        echo -e "${GREEN}✅ 远程仓库已添加${NC}"
    fi
    
    echo ""
    
    # 步骤 3: 推送代码
    echo -e "${YELLOW}[3/4] 推送代码到 GitHub...${NC}"
    
    # 切换到指定分支
    git checkout -B "${BRANCH}" 2>/dev/null || git checkout "${BRANCH}"
    
    # 推送代码
    if git push -u origin "${BRANCH}"; then
        echo -e "${GREEN}✅ 代码推送成功${NC}"
    else
        echo -e "${RED}❌ 代码推送失败${NC}"
        echo ""
        echo "可能的原因:"
        echo "1. Token 权限不足（需要 repo 权限）"
        echo "2. 网络连接问题"
        echo "3. 分支冲突"
        exit 1
    fi
    
    echo ""
else
    echo -e "${YELLOW}[2/4] 跳过代码推送${NC}"
    echo ""
fi

# 步骤 4: 完成
echo -e "${YELLOW}[4/4] 部署完成信息${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ 部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📦 仓库地址: https://github.com/${USERNAME}/${REPO_NAME}${NC}"
echo -e "${BLUE}🚀 克隆地址: ${REPO_URL}${NC}"
echo -e "${BLUE}📋 Actions 页面: https://github.com/${USERNAME}/${REPO_NAME}/actions${NC}"
echo ""
echo "下一步："
echo "1. 进入仓库页面，配置 GitHub Secrets"
echo "2. 启用 GitHub Actions"
echo "3. 手动触发测试或等待定时任务执行"
echo ""
echo "详细文档: DEPLOYMENT.md"
echo ""
