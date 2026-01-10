# 快速开始：5分钟部署到 GitHub

## 第一步：准备 GitHub 账号

如果你还没有 GitHub 账号，请先注册：https://github.com/signup

## 第二步：创建 GitHub 仓库

1. 登录 GitHub
2. 点击右上角 "+" -> "New repository"
3. 填写信息：
   - Repository name: `medical-news-collector`（或任意名称）
   - Description: `自动收集医疗器械和医美新闻`
   - 选择 Public 或 Private（Private 更安全）
4. 点击 "Create repository"

## 第三步：推送代码到 GitHub

在项目根目录执行以下命令（替换 `YOUR_USERNAME` 和 `REPO_NAME`）：

```bash
# 方式 1：使用部署脚本（推荐）
bash scripts/deploy_to_github.sh YOUR_USERNAME REPO_NAME

# 方式 2：手动执行命令
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

**示例**（假设你的用户名是 `zhangsan`，仓库名是 `news-bot`）：
```bash
bash scripts/deploy_to_github.sh zhangsan news-bot
```

## 第四步：配置 GitHub Secrets（重要！）

1. 进入你的 GitHub 仓库
2. 点击 "Settings" 标签
3. 左侧菜单：Secrets and variables -> Actions
4. 点击 "New repository secret"

### 必需配置

| Name | Value | 说明 |
|------|-------|------|
| `EMAILS` | `your-email@example.com` | 接收邮件的邮箱地址 |

如果有多个收件人，用逗号分隔：
```
user1@example.com,user2@example.com,user3@example.com
```

### 邮件服务配置

根据你的邮箱服务商，配置以下 Secrets：

#### QQ 邮箱（推荐）
| Name | Value |
|------|-------|
| `SMTP_HOST` | `smtp.qq.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | 你的QQ邮箱地址 |
| `SMTP_PASSWORD` | QQ邮箱授权码（不是登录密码！） |

**获取授权码**：
1. 登录 QQ 邮箱网页版
2. 设置 -> 账户 -> POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务
3. 开启 "POP3/SMTP服务"
4. 按提示发送短信获取授权码

#### 163 网易邮箱
| Name | Value |
|------|-------|
| `SMTP_HOST` | `smtp.163.com` |
| `SMTP_PORT` | `465` |
| `SMTP_USER` | 你的163邮箱地址 |
| `SMTP_PASSWORD` | 授权码 |

#### Gmail
| Name | Value |
|------|-------|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | 你的Gmail地址 |
| `SMTP_PASSWORD` | 应用专用密码 |

## 第五步：启用 GitHub Actions

1. 进入仓库的 "Actions" 标签
2. 如果看到提示 "I understand my workflows, go ahead and enable them"，点击它
3. 你会看到名为 "News Collection Workflow" 的工作流

## 第六步：手动测试

1. 在 Actions 页面，点击 "News Collection Workflow"
2. 点击 "Run workflow" 按钮
3. 选择分支（通常是 `main`）
4. 输入接收邮件的邮箱地址（或使用 Secrets 中配置的默认值）
5. 点击 "Run workflow" 绿色按钮

等待几分钟，检查你的邮箱是否收到新闻汇总邮件。

## 第七步：验证定时任务

定时任务已配置为：
- **UTC 22:00**（北京时间次日 06:00）
- **UTC 06:00**（北京时间 14:00）

你也可以在 `.github/workflows/news-collection.yml` 中修改时间：

```yaml
schedule:
  - cron: '0 22 * * *'  # UTC 22:00 = 北京时间 06:00
  - cron: '0 6 * * *'   # UTC 06:00 = 北京时间 14:00
```

## 常见问题

### Q1: 推送代码失败，提示 "Authentication failed"

**解决方案**：
- 如果使用 HTTPS，需要配置 Git 凭据或使用 Personal Access Token
- 推荐使用 SSH：`git remote set-url origin git@github.com:YOUR_USERNAME/REPO_NAME.git`
- 参考：https://docs.github.com/zh/authentication/connecting-to-github-with-ssh

### Q2: 邮件发送失败

**解决方案**：
1. 检查 SMTP 配置是否正确
2. QQ/163 邮箱需要使用授权码，不是登录密码
3. 查看 Actions 日志获取详细错误信息

### Q3: 没有收到邮件

**解决方案**：
1. 检查邮箱垃圾箱/垃圾邮件文件夹
2. 确认 `EMAILS` Secret 配置正确
3. 查看 Actions 日志，确认新闻是否成功收集

### Q4: 新闻数量为 0

**解决方案**：
1. 这是正常的，如果当天没有新的相关新闻
2. 查看日志中的搜索结果
3. 可以手动触发测试

## 监控和维护

### 查看执行历史
- 进入 Actions 标签
- 可以看到所有执行记录和日志

### 下载日志文件
- 失败的工作流会自动上传日志文件
- 在工作流页面底部的 "Artifacts" 部分下载

### 调整新闻源
编辑 `src/graphs/node.py` 中的 `fetch_news_node` 函数：
```python
# 修改 target_sites 批次
target_sites_batch1 = "toutiao.com|sohu.com|..."
```

### 修改搜索关键词
同样在 `src/graphs/node.py` 中，修改 `batch1_queries` 等变量。

## 技术支持

遇到问题？
1. 查看完整的 [README.md](./README.md)
2. 检查 Actions 日志文件
3. 在本地运行测试：`bash scripts/local_run.sh -m flow`

---

**恭喜！你的新闻收集机器人已成功部署！🎉**
