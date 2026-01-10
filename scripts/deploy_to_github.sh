#!/bin/bash

# GitHub 部署脚本
# 使用方法: bash scripts/deploy_to_github.sh <YOUR_USERNAME> <REPO_NAME>

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查参数
if [ $# -lt 2 ]; then
    echo -e "${RED}错误: 缺少必需参数${NC}"
    echo "使用方法: bash scripts/deploy_to_github.sh <YOUR_USERNAME> <REPO_NAME>"
    echo ""
    echo "示例:"
    echo "  bash scripts/deploy_to_github.sh johnsmith news-collector"
    exit 1
fi

USERNAME=$1
REPO_NAME=$2
REPO_URL="https://github.com/${USERNAME}/${REPO_NAME}.git"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  GitHub 部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 步骤 1: 检查 Git 状态
echo -e "${YELLOW}[1/5] 检查 Git 状态...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${RED}警告: 工作区有未提交的更改${NC}"
    echo "请先提交所有更改后再部署"
    git status
    exit 1
fi
echo -e "${GREEN}✓ 工作区干净${NC}"
echo ""

# 步骤 2: 检查远程仓库
echo -e "${YELLOW}[2/5] 检查远程仓库配置...${NC}"
if git remote get-url origin > /dev/null 2>&1; then
    EXISTING_URL=$(git remote get-url origin)
    echo "已配置远程仓库: ${EXISTING_URL}"
    echo -n "是否要更新远程仓库地址? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        git remote set-url origin "${REPO_URL}"
        echo -e "${GREEN}✓ 远程仓库已更新${NC}"
    else
        echo "使用现有远程仓库"
    fi
else
    git remote add origin "${REPO_URL}"
    echo -e "${GREEN}✓ 远程仓库已添加${NC}"
fi
echo ""

# 步骤 3: 确认分支
echo -e "${YELLOW}[3/5] 确认分支...${NC}"
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -n "当前分支是 ${CURRENT_BRANCH}，是否切换到 main 分支? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        git checkout -b main || git checkout main
        CURRENT_BRANCH="main"
        echo -e "${GREEN}✓ 已切换到 main 分支${NC}"
    else
        echo "继续使用 ${CURRENT_BRANCH} 分支"
    fi
else
    echo -e "${GREEN}✓ 当前在 main 分支${NC}"
fi
echo ""

# 步骤 4: 推送到 GitHub
echo -e "${YELLOW}[4/5] 推送代码到 GitHub...${NC}"
echo "目标仓库: ${REPO_URL}"
echo ""

# 尝试推送
if git push -u origin "$CURRENT_BRANCH"; then
    echo -e "${GREEN}✓ 代码推送成功${NC}"
else
    echo -e "${RED}✗ 推送失败${NC}"
    echo ""
    echo "可能的原因:"
    echo "1. GitHub 仓库还未创建，请先在 GitHub 网站上创建仓库"
    echo "   访问: https://github.com/new"
    echo "2. 用户名或仓库名称错误"
    echo "3. 需要身份验证（SSH密钥或Personal Access Token）"
    echo ""
    echo "请检查后重试"
    exit 1
fi
echo ""

# 步骤 5: 配置提示
echo -e "${YELLOW}[5/5] 后续配置步骤...${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "接下来请完成以下配置："
echo ""
echo "1️⃣  配置 GitHub Secrets:"
echo "   进入仓库页面 -> Settings -> Secrets and variables -> Actions"
echo ""
echo "   必需配置："
echo "   - EMAILS: 接收邮件的邮箱地址（多个用逗号分隔）"
echo ""
echo "   可选配置（邮件服务）："
echo "   - SMTP_HOST: SMTP 服务器地址（如 smtp.qq.com）"
echo "   - SMTP_PORT: SMTP 端口（如 587）"
echo "   - SMTP_USER: 邮箱账号"
echo "   - SMTP_PASSWORD: 邮箱授权码"
echo ""
echo "2️⃣  启用 GitHub Actions:"
echo "   进入仓库页面 -> Actions 标签"
echo "   点击 "I understand my workflows, go ahead and enable them""
echo ""
echo "3️⃣  手动测试工作流:"
echo "   进入 Actions 标签 -> News Collection Workflow"
echo "   点击 "Run workflow" 手动触发测试"
echo ""
echo "4️⃣  验证定时任务:"
echo "   工作流将在每天 UTC 22:00（北京时间次日 06:00）自动运行"
echo ""
echo -e "${GREEN}📊 仓库地址: ${REPO_URL}${NC}"
echo -e "${GREEN}📋 Actions 页面: ${REPO_URL}/actions${NC}"
echo ""
echo "详细文档请查看 README.md 文件"
