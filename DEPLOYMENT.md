# 🚀 GitHub 自动化部署完整指南

## 📋 概述

本项目已配置好 GitHub Actions，可以实现：
- ✅ 每天上午 6 点自动收集新闻并发送邮件
- ✅ 手动触发新闻收集任务
- ✅ 自动记录执行日志
- ✅ 失败自动重试

## 🎯 快速开始（5 分钟）

### 第一步：创建 GitHub 仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - Repository name: `medical-news-collector`（可自定义）
   - Description: `自动收集医疗器械和医美新闻`
   - 选择 Public 或 Private（建议 Private，更安全）
3. 点击 "Create repository"

### 第二步：推送代码

在项目根目录执行以下命令（**替换 `YOUR_USERNAME` 和 `REPO_NAME` 为你的实际信息**）：

```bash
# 使用自动化部署脚本（推荐）
bash scripts/deploy_to_github.sh YOUR_USERNAME REPO_NAME

# 示例（假设你的用户名是 zhangsan，仓库名是 news-bot）
bash scripts/deploy_to_github.sh zhangsan news-bot
```

**脚本会自动完成**：
- ✅ 检查 Git 状态
- ✅ 配置远程仓库
- ✅ 推送代码到 GitHub
- ✅ 显示后续配置步骤

### 第三步：配置 GitHub Secrets（重要！）

#### 必需配置

1. 进入你的 GitHub 仓库
2. 点击 **Settings** 标签
3. 左侧菜单：**Secrets and variables** → **Actions**
4. 点击 **New repository secret**
5. 添加以下 Secret：

| Name | Value | 示例 |
|------|-------|------|
| `EMAILS` | 接收邮件的邮箱地址 | `zhangsan@qq.com` |

**多个邮箱地址用逗号分隔**：
```
user1@example.com,user2@example.com,user3@example.com
```

#### 邮件服务配置（选择一种）

**QQ 邮箱（推荐）**

| Name | Value |
|------|-------|
| `SMTP_HOST` | `smtp.qq.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | 你的QQ邮箱地址 |
| `SMTP_PASSWORD` | QQ邮箱授权码 |

**获取 QQ 邮箱授权码**：
1. 登录 QQ 邮箱网页版
2. 设置 → 账户 → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务
3. 开启 "POP3/SMTP服务"
4. 发送短信获取授权码（**不是登录密码**）

**163 网易邮箱**

| Name | Value |
|------|-------|
| `SMTP_HOST` | `smtp.163.com` |
| `SMTP_PORT` | `465` |
| `SMTP_USER` | 你的163邮箱地址 |
| `SMTP_PASSWORD` | 163邮箱授权码 |

**Gmail**

| Name | Value |
|------|-------|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | 你的Gmail地址 |
| `SMTP_PASSWORD` | 应用专用密码 |

### 第四步：启用 GitHub Actions

1. 进入仓库的 **Actions** 标签
2. 如果看到提示 "I understand my workflows, go ahead and enable them"，点击它
3. 你会看到名为 **"News Collection Workflow"** 的工作流

### 第五步：手动测试

1. 在 Actions 页面，点击 "News Collection Workflow"
2. 点击 **"Run workflow"** 按钮
3. 选择分支（通常是 `main`）
4. 输入接收邮件的邮箱地址（或留空使用 Secrets 中配置的默认值）
5. 点击绿色 **"Run workflow"** 按钮

等待 3-5 分钟，检查你的邮箱是否收到新闻汇总邮件。

### 第六步：验证定时任务

定时任务已自动配置为：
- **UTC 22:00**（北京时间次日 06:00）
- **UTC 06:00**（北京时间 14:00）

你可以在 `.github/workflows/news-collection.yml` 中修改触发时间：

```yaml
schedule:
  - cron: '0 22 * * *'  # UTC 22:00 = 北京时间 06:00
  - cron: '0 6 * * *'   # UTC 06:00 = 北京时间 14:00
```

## 📊 监控和管理

### 查看执行历史

1. 进入仓库的 **Actions** 标签
2. 可以看到所有执行记录
3. 点击任意记录可以查看详细日志

### 手动触发测试

任意时间都可以手动触发新闻收集任务，不需要等待定时任务。

### 下载执行日志

失败的工作流会自动上传日志文件：
- 进入具体的工作流执行页面
- 滚动到底部找到 **Artifacts** 区域
- 下载日志文件进行分析

## 🔧 自定义配置

### 修改新闻源

编辑 `src/graphs/node.py` 文件，找到 `fetch_news_node` 函数：

```python
# 第一批次
target_sites_batch1 = "toutiao.com|sohu.com|qq.com|163.com|ifeng.com"

# 第二批次（新增）
target_sites_batch2 = "sina.com.cn|thepaper.cn|36kr.com"

# 第三批次（新增）
target_sites_batch3 = "ylqx.qgyyzs.net|finance.sina.com.cn"
```

### 修改搜索关键词

同样在 `src/graphs/node.py` 中：

```python
# 第一批次查询
batch1_queries = [
    "医疗器械公司",
    "医疗器械产品",
    # ...
]
```

### 修改定时任务时间

编辑 `.github/workflows/news-collection.yml`：

```yaml
schedule:
  - cron: '分 时 日 月 周'
  # 每天上午6点（北京时间）
  - cron: '0 22 * * *'
```

**Cron 表达式说明**：
- `0 6 * * *` - 每天 UTC 6:00
- `0 22 * * *` - 每天 UTC 22:00
- `0 */6 * * *` - 每 6 小时一次
- `0 9 * * 1-5` - 周一到周五上午 9 点

更多示例：https://crontab.guru/

## ❓ 常见问题

### Q1: 推送代码失败，提示 "Authentication failed"

**解决方案**：

1. **使用 SSH（推荐）**：
   ```bash
   git remote set-url origin git@github.com:YOUR_USERNAME/REPO_NAME.git
   git push -u origin main
   ```

2. **配置 HTTPS 认证**：
   - 使用 GitHub CLI: `gh auth login`
   - 或使用 Personal Access Token: https://github.com/settings/tokens

### Q2: Actions 执行失败，邮件发送失败

**解决方案**：

1. 检查 SMTP 配置是否正确
2. QQ/163 邮箱必须使用**授权码**，不是登录密码
3. 查看 Actions 日志获取详细错误信息
4. 确认邮箱开启了 POP3/SMTP 服务

### Q3: 没有收到邮件

**解决方案**：

1. 检查邮箱的**垃圾邮件/垃圾箱**文件夹
2. 确认 `EMAILS` Secret 配置正确
3. 查看 Actions 日志，确认新闻是否成功收集
4. 手动触发测试

### Q4: 新闻数量为 0

**解决方案**：

1. 这是正常的，当天可能没有新的相关新闻
2. 查看 Actions 日志中的搜索结果
3. 可以修改搜索关键词或新闻源
4. 手动触发测试

### Q5: 如何只收集特定日期的新闻？

**解决方案**：

编辑 `.github/workflows/news-collection.yml`，修改触发时间：

```yaml
schedule:
  # 每周一上午 6 点
  - cron: '0 22 * * 1'
  # 每月 1 号上午 6 点
  - cron: '0 22 1 * *'
```

## 📚 相关文档

- **快速开始**: [QUICKSTART.md](./QUICKSTART.md)
- **完整文档**: [README.md](./README.md)
- **GitHub Actions 文档**: https://docs.github.com/en/actions
- **Cron 表达式生成器**: https://crontab.guru/

## 🔐 安全建议

1. **使用 Private 仓库**：避免暴露你的邮件配置
2. **定期更换授权码**：每 3-6 个月更换一次
3. **不要提交 .env 文件**：敏感信息放在 Secrets 中
4. **定期查看日志**：监控异常访问或错误

## 📞 技术支持

遇到问题？

1. 查看 [QUICKSTART.md](./QUICKSTART.md) 快速排查
2. 查看 Actions 日志文件
3. 本地测试：`bash scripts/local_run.sh -m flow`
4. 参考 GitHub 官方文档

---

**🎉 恭喜！你的新闻收集机器人已成功部署！**

每天上午 6 点，系统会自动收集新闻并发送到你的邮箱。
