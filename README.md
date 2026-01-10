# 项目结构说明

# 本地运行
## 运行流程
bash scripts/local_run.sh -m flow

## 运行节点
bash scripts/local_run.sh -m node -n node_name

# 启动HTTP服务
bash scripts/http_run.sh -m http -p 5000

# GitHub 部署指南

## 方式 1: 使用 API 部署（推荐）🚀

### 快速开始

1. **获取 Personal Access Token**
   - 访问 https://github.com/settings/tokens
   - 创建新 Token，勾选 `repo` 权限
   - 详细步骤：[Token 获取指南](docs/GITHUB_TOKEN_GUIDE.md)

2. **执行部署命令**

   **Python 脚本（推荐）**：
   ```bash
   pip install requests cryptography  # 首次需要

   python scripts/deploy_via_api.py \
       --token ghp_xxxxxxxxxxxx \
       --username your-username \
       --repo news-bot
   ```

   **Bash 脚本**：
   ```bash
   bash scripts/deploy_via_api.sh ghp_xxxxxxxxxxxx your-username news-bot
   ```

   **创建私有仓库**：
   ```bash
   python scripts/deploy_via_api.py \
       --token ghp_xxx \
       --username your-username \
       --repo news-bot \
       --private
   ```

3. **配置 GitHub Secrets**（参考下方说明）

更多 API 部署示例：[API 部署完整指南](docs/API_DEPLOYMENT.md)

---

## 方式 2: 传统方式部署

### 步骤 1: 创建 GitHub 仓库

1. 登录 [GitHub](https://github.com)
2. 点击右上角 "+" 按钮，选择 "New repository"
3. 填写仓库信息：
   - Repository name: 医疗器械医美新闻收集
   - Description: 自动收集医疗器械和医美相关新闻并发送邮件
   - Public/Private: 根据需要选择
4. 点击 "Create repository"

## 步骤 2: 关联本地仓库到 GitHub

```bash
# 添加远程仓库（替换 YOUR_USERNAME 和 REPO_NAME）
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# 推送代码到 GitHub
git branch -M main
git push -u origin main
```

## 步骤 3: 配置 GitHub Secrets

1. 进入仓库页面，点击 "Settings" 标签
2. 左侧菜单点击 "Secrets and variables" -> "Actions"
3. 点击 "New repository secret"
4. 添加以下密钥：
   
   | Name | Value | 说明 |
   |------|-------|------|
   | `EMAILS` | `user1@example.com,user2@example.com` | 接收邮件的邮箱地址，多个用逗号分隔 |

## 步骤 4: 配置邮件服务

由于邮件服务需要认证信息，你还需要配置以下 Secrets（参考你的邮件服务商）：

1. **SMTP 配置**（以 QQ 邮箱为例）：
   - `SMTP_HOST`: `smtp.qq.com`
   - `SMTP_PORT`: `587`
   - `SMTP_USER`: 你的邮箱地址
   - `SMTP_PASSWORD`: 授权码（不是登录密码，需要在邮箱设置中生成）

2. **其他邮箱服务商配置**：
   - **163 网易邮箱**: `smtp.163.com:465`
   - **Gmail**: `smtp.gmail.com:587`
   - **企业邮箱**: 联系 IT 部门获取配置信息

## 步骤 5: 配置其他集成服务（如果需要）

1. **大语言模型配置**：
   - `COZE_INTEGRATION_MODEL_BASE_URL`: 模型API地址
   - `COZE_WORKLOAD_IDENTITY_API_KEY`: API密钥

2. **数据库配置**（如果使用外部数据库）：
   - `DATABASE_URL`: 数据库连接字符串

## 步骤 6: 验证定时任务

1. 进入仓库的 "Actions" 标签
2. 你可以看到名为 "News Collection Workflow" 的工作流
3. 点击工作流，可以查看执行历史和日志
4. 点击 "Run workflow" 可以手动触发测试

## 定时任务说明

- **默认触发时间**：
  - UTC 时间 22:00（北京时间次日 06:00）
  - UTC 时间 06:00（北京时间 14:00）
- **时区调整**：
  - 如需修改触发时间，编辑 `.github/workflows/news-collection.yml` 文件中的 cron 表达式
  - Cron 格式：`分 时 日 月 周`
  - 例如：`0 6 * * *` 表示每天 UTC 时间 6:00 执行

## 常见问题

### 1. 邮件发送失败
- 检查 SMTP 配置是否正确
- 确认授权码是否有效（QQ邮箱需要单独生成授权码）
- 查看 Actions 日志获取详细错误信息

### 2. 没有收到邮件
- 检查邮箱垃圾箱
- 确认 Secrets 中的 EMAILS 配置正确
- 检查工作流执行日志，确认新闻是否成功收集

### 3. 新闻数量不足
- 检查新闻源网站是否正常访问
- 查看工作流日志中的搜索结果
- 可能需要调整搜索关键词或新闻源

### 4. 定时任务未执行
- 检查工作流文件语法是否正确
- 确认仓库 Actions 功能已启用
- 查看 GitHub 状态页面确认服务正常

## 监控与维护

1. **定期检查**：每周查看一次 Actions 执行日志
2. **更新密钥**：定期更换敏感信息（如授权码）
3. **优化搜索词**：根据实际需求调整搜索关键词
4. **新闻源维护**：如某些网站无法访问，及时更新新闻源列表

## 技术支持

如遇到问题，请：
1. 查看 Actions 日志文件
2. 检查本地的运行情况
3. 参考 GitHub Actions 文档：https://docs.github.com/en/actions

