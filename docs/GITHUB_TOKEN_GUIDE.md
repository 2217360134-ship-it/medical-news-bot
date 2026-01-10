# GitHub Personal Access Token (PAT) 获取指南

## 什么是 Personal Access Token？

Personal Access Token (PAT) 是 GitHub 提供的一种认证方式，用于代替密码访问 GitHub API 和 Git 操作。使用 API 部署项目时，你需要创建一个 PAT。

## 步骤 1: 登录 GitHub

访问 https://github.com 并登录你的账号。

## 步骤 2: 进入 Settings 页面

1. 点击右上角的头像
2. 选择 "Settings"（设置）

## 步骤 3: 进入 Developer Settings

1. 在左侧菜单底部找到 "Developer settings"（开发者设置）
2. 点击进入

## 步骤 4: 创建 Personal Access Token

1. 点击左侧的 "Personal access tokens"（个人访问令牌）
2. 点击 "Tokens (classic)" 或 "Fine-grained tokens"

### 方式 A: Tokens (classic) - 推荐

1. 点击 "Generate new token (classic)"
2. 填写信息：

   **Note（备注）**：
   ```
   医疗器械新闻收集机器人
   ```

   **Expiration（过期时间）**：
   - 建议：No expiration（永不过期）或选择较长时间（如 1 年）
   - 如果需要更高安全性，可以选择较短时间（如 90 天）

   **Select scopes（选择权限）**：
   
   勾选以下权限：
   
   - ✅ **repo** - 完整的仓库访问权限（包括创建、删除、推送代码）
     - repo:status
     - repo_deployment
     - public_repo
     - repo:invite
     - security_events
   
   - ✅ **workflow** - GitHub Actions 工作流权限（可选，如果需要通过 API 管理 Actions）

3. 点击底部的 "Generate token"（生成令牌）

4. **重要：复制并保存你的 Token**
   - ⚠️ Token 只会显示一次，请务必立即复制保存！
   - Token 格式类似：`ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 方式 B: Fine-grained tokens（细粒度令牌）- 更安全

1. 点击 "Generate new token" → "Generate fine-grained token"

2. 填写信息：

   **Token name**：
   ```
   医疗器械新闻收集机器人
   ```

   **Expiration**：
   - 选择有效期（如 90 天、1 年等）

   **Description**（可选）：
   ```
   用于自动部署医疗器械新闻收集项目
   ```

   **Resource owner**：
   - 选择 "Only select repositories"（仅选择特定仓库）
   - 后续创建仓库后，你需要添加该仓库的访问权限

   **Repository permissions（仓库权限）**：
   
   选择以下权限：
   - ✅ **Contents** - Read and write（读写仓库内容）
   - ✅ **Pull requests** - Read and write（读写拉取请求）
   - ✅ **Issues** - Read and write（读写问题）
   - ✅ **Workflows** - Read and write（读写工作流，可选）

   **Account permissions（账号权限）**：
   - 无需配置

3. 点击 "Generate token"

4. **保存你的 Token**（格式类似：`github_pat_xxxxx`）

## 步骤 5: 测试 Token

你可以使用 curl 测试 Token 是否有效：

```bash
# 替换 YOUR_TOKEN 为你的实际 Token
curl -H "Authorization: token YOUR_TOKEN" \
     https://api.github.com/user
```

如果返回你的用户信息，说明 Token 有效。

## 安全建议

1. **不要泄露 Token**
   - 不要将 Token 提交到 Git 仓库
   - 不要分享给他人
   - Token 已添加到 `.gitignore`

2. **定期更换 Token**
   - 建议每 6-12 个月更换一次
   - 如果怀疑泄露，立即撤销并重新生成

3. **使用最小权限原则**
   - 只授予必要的权限
   - 如果只需读取，不要授予写入权限

4. **设置过期时间**
   - 虽然 Token 可以永不过期，但建议设置合理的过期时间

5. **监控使用情况**
   - 在 GitHub Settings > Developer settings > Personal access tokens 中查看使用情况

## 撤销 Token

如果不再需要或怀疑泄露，可以撤销 Token：

1. 进入 Settings > Developer settings > Personal access tokens
2. 找到对应的 Token
3. 点击 "Revoke"（撤销）

## 常见问题

### Q1: Token 创建后，在哪里查看？

Token 只在创建时显示一次。如果丢失，你需要：
1. 撤销旧的 Token
2. 创建新的 Token

### Q2: 使用 Token 访问 GitHub 时提示 401 Unauthorized

可能的原因：
- Token 已过期
- Token 权限不足
- Token 输入错误（注意空格和换行）

### Q3: 使用 Fine-grained token 部署时提示权限不足

Fine-grained token 需要额外授权才能访问仓库：
1. 进入个人 Settings > Applications
2. 找到对应的 Token
3. 点击 "Add repository" 添加你的仓库

### Q4: Token 格式说明

- **Classic token**: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`（以 `ghp_` 开头）
- **Fine-grained token**: `github_pat_xxxxx`（以 `github_pat_` 开头）

两种格式都可以使用。

### Q5: 如何在 CI/CD 中使用 Token？

在 GitHub Actions 中，通常不需要手动配置 Token。Actions 会自动提供 `GITHUB_TOKEN`。

但在本地脚本中使用时：
- 作为命令行参数：`--token ghp_xxx`
- 作为环境变量：`export GITHUB_TOKEN=ghp_xxx`

## 下一步

获取 Token 后，你可以：

1. **使用 Python 脚本部署**：
   ```bash
   python scripts/deploy_via_api.py --token YOUR_TOKEN --username USERNAME --repo REPO_NAME
   ```

2. **使用 Bash 脚本部署**：
   ```bash
   bash scripts/deploy_via_api.sh YOUR_TOKEN USERNAME REPO_NAME
   ```

3. **使用 Git 命令行**：
   ```bash
   git remote set-url origin https://YOUR_TOKEN@github.com/USERNAME/REPO_NAME.git
   git push -u origin main
   ```

## 相关文档

- [GitHub 官方文档：Creating a personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [部署指南](./DEPLOYMENT.md)
- [API 部署示例](./API_DEPLOYMENT.md)
