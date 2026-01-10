# Coze API 配置指南

本文档说明如何在 GitHub Actions 中使用 Coze API 调用工作流。

## 概述

GitHub Actions 通过 HTTP API 调用部署在 Coze 平台上的工作流，避免了在 GitHub Actions 中配置复杂的 Coze 环境变量。

## 架构说明

```
GitHub Actions (触发器)
    ↓
调用 Coze API (HTTP POST)
    ↓
Coze 平台工作流 (执行新闻收集)
    ↓
发送邮件通知
```

## 步骤 1：获取 Coze API Token

### 方法 1：通过 Coze 平台获取

1. 登录 [Coze 平台](https://www.coze.cn)
2. 进入你的工作空间
3. 点击右上角头像 → "设置" 或 "API 管理"
4. 找到 "API Token" 或 "Personal Access Token" 部分
5. 点击 "生成新 Token"
6. 设置 Token 权限：
   - ✅ **工作流运行权限** (Workflow Run)
   - ✅ **工作流查询权限** (Workflow Query)
7. 复制并保存 Token（格式类似：`pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxx`）

**⚠️ 重要**：
- Token 只显示一次，请立即复制保存
- 不要将 Token 提交到代码仓库

### 方法 2：通过项目设置获取

1. 在 Coze 平台打开你的项目
2. 点击 "设置" 标签
3. 找到 "API 访问" 或 "访问令牌" 部分
4. 点击 "生成访问令牌"
5. 复制生成的 Token

## 步骤 2：获取工作流 ID

### 方法 1：从工作流 URL 获取

1. 在 Coze 平台打开你的工作流
2. 浏览器地址栏中的 URL 格式类似：
   ```
   https://www.coze.cn/space/xxxxxx/workflow/xxxxxxxxx
   ```
3. 最后一段 `xxxxxxxxx` 就是 **Workflow ID**

### 方法 2：从 API 文档获取

1. 在 Coze 平台打开工作流
2. 点击 "API" 或 "调试" 按钮
3. 查看 API 文档中的 Workflow ID

### 方法 3：通过列表 API 获取

使用以下 curl 命令获取所有工作流列表：

```bash
curl -X GET "https://api.coze.cn/v1/workflows" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

返回结果中的 `id` 字段就是 Workflow ID。

## 步骤 3：配置 GitHub Secrets

在 GitHub 仓库中配置以下 Secrets：

### 必需配置

| Secret 名称 | 说明 | 示例值 |
|------------|------|--------|
| `COZE_API_TOKEN` | Coze API Token | `pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `COZE_WORKFLOW_ID` | 工作流 ID | `734827389472348` |
| `EMAILS` | 接收邮件的邮箱地址（多个用逗号分隔） | `user1@example.com,user2@example.com` |

### 可选配置

| Secret 名称 | 说明 | 默认值 |
|------------|------|--------|
| `COZE_API_BASE_URL` | Coze API 基础 URL | `https://api.coze.cn` |

### 配置步骤

1. 进入你的 GitHub 仓库
2. 点击 "Settings" 标签
3. 左侧菜单：Secrets and variables → Actions
4. 点击 "New repository secret"
5. 依次添加上述 Secrets

## 步骤 4：验证配置

### 方法 1：手动触发工作流

1. 进入仓库的 "Actions" 标签
2. 点击 "News Collection Workflow"
3. 点击 "Run workflow" 按钮
4. 输入邮箱地址（或使用 Secrets 中配置的默认值）
5. 点击 "Run workflow" 绿色按钮
6. 查看执行日志，确认工作流是否成功触发

### 方法 2：本地测试 API

在本地使用 curl 测试 API 是否可用：

```bash
# 设置变量
COZE_API_TOKEN="your_token_here"
COZE_WORKFLOW_ID="your_workflow_id_here"
EMAILS="test@example.com"

# 调用 API
curl -X POST "https://api.coze.cn/v1/workflow/run" \
  -H "Authorization: Bearer ${COZE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"workflow_id\": \"${COZE_WORKFLOW_ID}\",
    \"parameters\": {
      \"emails\": \"${EMAILS}\"
    }
  }"
```

如果返回成功（code 为 0），说明配置正确。

### 方法 3：查看工作流执行日志

在 Coze 平台查看工作流执行情况：

1. 登录 Coze 平台
2. 进入你的工作流
3. 点击 "运行历史" 或 "日志" 标签
4. 查看最新的执行记录和日志

## 步骤 5：配置定时任务

GitHub Actions 工作流已配置为每天自动触发两次：

```yaml
schedule:
  - cron: '0 22 * * *'  # UTC 22:00 = 北京时间 06:00
  - cron: '0 6 * * *'   # UTC 06:00 = 北京时间 14:00
```

你可以根据需要修改 `.github/workflows/news-collection.yml` 中的时间设置。

### Cron 表达式格式

```
分钟 小时 日期 月份 星期
*    *    *    *    *
```

示例：
- `0 6 * * *`：每天早上 6 点执行
- `0 0 * * 1`：每周一凌晨 0 点执行
- `0 */2 * * *`：每 2 小时执行一次

⚠️ **注意**：GitHub Actions 使用 UTC 时间，请根据时区换算。

## 常见问题

### Q1: API 调用返回 401 Unauthorized

**原因**：Token 无效或已过期

**解决方案**：
1. 检查 Token 是否正确复制（注意空格和换行）
2. 确认 Token 未过期
3. 重新生成新的 Token

### Q2: API 调用返回 404 Not Found

**原因**：Workflow ID 错误或工作流不存在

**解决方案**：
1. 确认 Workflow ID 是否正确
2. 在 Coze 平台检查工作流是否存在
3. 确认工作流是否已发布

### Q3: 工作流执行失败

**原因**：可能是邮件配置、网络搜索等环节出错

**解决方案**：
1. 查看 GitHub Actions 日志中的 API 响应
2. 在 Coze 平台查看工作流执行日志
3. 检查工作流中的邮件配置（SMTP 相关）

### Q4: 没有收到邮件

**可能原因**：
1. 邮箱地址配置错误
2. SMTP 配置不正确
3. 邮件被垃圾邮箱拦截

**解决方案**：
1. 检查 GitHub Secrets 中的 `EMAILS` 配置
2. 在 Coze 平台检查工作流的 SMTP 配置
3. 检查邮箱垃圾箱
4. 在 Coze 平台手动触发工作流测试

### Q5: 工作流执行超时

**原因**：工作流执行时间超过 15 分钟

**解决方案**：
1. 在 Coze 平台优化工作流性能
2. 调整 GitHub Actions 中的 `MAX_WAIT` 参数

### Q6: 如何修改工作流代码

**方法**：
1. 在 Coze 平台直接修改工作流
2. 不需要更新 GitHub 代码仓库
3. 修改后立即生效

### Q7: GitHub Token 和 Coze Token 有什么区别？

- **GitHub Token (PAT)**：用于 GitHub Actions 操作（部署代码）
- **Coze API Token**：用于调用 Coze 平台的工作流 API

两者完全独立，用途不同。

## 安全建议

1. **定期更换 Token**：建议每 6 个月更换一次
2. **最小权限原则**：只授予工作流运行和查询权限
3. **不要泄露 Token**：
   - 不要提交到代码仓库
   - 不要在公开渠道分享
   - 不要写入日志文件
4. **监控使用情况**：定期查看 API 调用日志

## 相关文档

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Coze 平台文档](https://www.coze.cn/docs)
- [GitHub Secrets 配置指南](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [部署指南](../DEPLOYMENT.md)
- [快速开始](../QUICKSTART.md)

## 技术支持

遇到问题？

1. 查看完整的 [README.md](../README.md)
2. 检查 Coze 平台工作流日志
3. 检查 GitHub Actions 执行日志
4. 在 Coze 平台手动触发工作流测试

---

**配置完成后，你的新闻收集机器人就能通过 GitHub Actions 每天自动运行了！🎉**
