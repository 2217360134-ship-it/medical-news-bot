from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from graphs.state import (
    SplitEmailsInput, SplitEmailsOutput,
    FetchNewsInput, FetchNewsOutput,
    DeduplicateNewsInput, DeduplicateNewsOutput,
    ExtractNewsInfoInput, ExtractNewsInfoOutput,
    ExtractDateInput, ExtractDateOutput,
    CreateTableInput, CreateTableOutput,
    SendEmailInput, SendEmailOutput,
    SaveNewsHistoryInput, SaveNewsHistoryOutput,
    NewsItem
)
import os
from datetime import datetime
from cozeloop.decorator import observe
import json
from jinja2 import Template


def split_emails_node(state: SplitEmailsInput, config: RunnableConfig, runtime: Runtime[Context]) -> SplitEmailsOutput:
    """
    title: 分割邮箱地址
    desc: 将逗号分隔的邮箱字符串分割成列表，支持逗号、分号、空格等分隔符
    """
    # 将emails字符串分割成列表（支持逗号、分号、空格分隔）
    emails_str = state.emails or ""
    emails_list = [email.strip() for email in emails_str.replace(';', ',').replace(' ', ',').split(',') if email.strip()]
    
    print(f"分割后的邮箱列表: {emails_list}")
    
    return SplitEmailsOutput(emails_list=emails_list)


def fetch_news_node(state: FetchNewsInput, config: RunnableConfig, runtime: Runtime[Context]) -> FetchNewsOutput:
    """
    title: 获取指定来源新闻
    desc: 从今日头条、搜狐、腾讯网、网易新闻、凤凰网获取医疗器械和医美相关的新闻
    integrations: 联网搜索
    """
    ctx = runtime.context
    
    # 导入网络搜索函数
    from tools.web_search_tool import web_search
    
    news_list = []
    
    # 定义目标新闻来源域名
    target_sites = "toutiao.com|sohu.com|qq.com|163.com|ifeng.com|thepaper.cn|finance.sina.com.cn|sina.com.cn|ylqx.qgyyzs.net|camdi.cn|qxw18.com|cctv.com"
    
    # 构建核心搜索词列表（确保获取的新闻主体内容与医疗器械、医美相关）
    medical_device_queries = [
        "医疗器械公司",
        "医疗器械产品",
        "医疗器械技术",
        "医疗设备",
        "诊断设备",
        "IVD 体外诊断",
        "医疗器械融资",
        "医疗器械上市"
    ]
    
    medical_beauty_queries = [
        "医美公司",
        "医美产品",
        "医美技术",
        "激光美容",
        "整形美容",
        "微整形",
        "医美融资",
        "医美上市"
    ]
    
    try:
        # 并行搜索所有医疗器械相关查询
        all_web_items = []
        search_success_count = 0
        search_fail_count = 0
        
        print(f"开始搜索新闻，目标网站: {target_sites}")
        
        for query in medical_device_queries:
            try:
                web_items, _, _, _ = web_search(
                    ctx=ctx,
                    query=query,
                    search_type="web",
                    count=10,
                    need_summary=True,
                    need_content=True,
                    sites=target_sites
                )
                all_web_items.extend(web_items)
                search_success_count += 1
                print(f"[成功] 搜索 '{query}' 获取到 {len(web_items)} 条新闻")
            except Exception as e:
                search_fail_count += 1
                print(f"[失败] 搜索 '{query}' 失败: {str(e)}")
                continue
        
        for query in medical_beauty_queries:
            try:
                web_items, _, _, _ = web_search(
                    ctx=ctx,
                    query=query,
                    search_type="web",
                    count=10,
                    need_summary=True,
                    need_content=True,
                    sites=target_sites
                )
                all_web_items.extend(web_items)
                search_success_count += 1
                print(f"[成功] 搜索 '{query}' 获取到 {len(web_items)} 条新闻")
            except Exception as e:
                search_fail_count += 1
                print(f"[失败] 搜索 '{query}' 失败: {str(e)}")
                continue
        
        print(f"搜索完成: 成功 {search_success_count} 个查询，失败 {search_fail_count} 个查询")
        print(f"总共获取到 {len(all_web_items)} 条原始新闻")
        
        # 如果没有获取到任何新闻，打印警告
        if not all_web_items:
            print("⚠️ 警告: 所有搜索查询都没有获取到新闻！")
            print("可能的原因:")
            print("  1. 网络搜索服务暂时不可用")
            print("  2. 目标网站没有相关新闻")
            print("  3. 搜索词需要调整")
        
        # 转换为NewsItem格式
        for item in all_web_items:
            if not item.Url:
                continue
            
            # 解析日期，如果PublishTime为空则使用当前日期
            if item.PublishTime:
                try:
                    # ISO时间格式转换为简单日期
                    publish_date = item.PublishTime.split('T')[0]
                except:
                    publish_date = datetime.now().strftime('%Y-%m-%d')
            else:
                publish_date = datetime.now().strftime('%Y-%m-%d')
            
            news_item = NewsItem(
                title=item.Title or "",
                date=publish_date,
                url=item.Url,
                summary=item.Snippet or "",
                content=item.Content or "",
                keywords=[]
            )
            news_list.append(news_item)
        
        # 去重逻辑
        # 1. 根据URL去重
        seen_urls = set()
        unique_by_url = []
        for news in news_list:
            if news.url not in seen_urls:
                seen_urls.add(news.url)
                unique_by_url.append(news)
        
        # 2. 根据标题相似度去重（避免不同网站的相同新闻）
        seen_titles = set()
        final_news = []
        for news in unique_by_url:
            # 标准化标题：去除空格和特殊字符，转小写
            normalized_title = news.title.lower().strip()
            # 移除一些常见的网站名称后缀
            for suffix in ['| toutiao', '- 今日头条', '_头条', '_新闻', '_资讯']:
                normalized_title = normalized_title.replace(suffix.lower(), '')
            
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                final_news.append(news)
        
        return FetchNewsOutput(news_list=final_news)
        
    except Exception as e:
        raise Exception(f"获取新闻失败: {str(e)}")


def deduplicate_news_node(state: DeduplicateNewsInput, config: RunnableConfig, runtime: Runtime[Context]) -> DeduplicateNewsOutput:
    """
    title: 去重历史新闻
    desc: 查询数据库中的历史新闻记录，去除重复的新闻（URL或标题相同的新闻）
    integrations: 数据库
    """
    ctx = runtime.context

    try:
        from storage.database.db import get_session
        from storage.database.news_history_manager import NewsHistoryManager

        # 获取数据库会话
        db = get_session()

        try:
            # 创建管理器
            mgr = NewsHistoryManager()

            # 获取所有历史新闻的URL和标题
            history_urls = mgr.get_all_urls(db)
            history_titles = mgr.get_all_titles(db)

            print(f"历史记录中共有 {len(history_urls)} 个URL，{len(history_titles)} 个标题")

            # 去重逻辑
            deduplicated_news = []
            duplicate_count = 0

            for news in state.filtered_news_list:
                # 1. 检查URL是否已存在
                if news.url in history_urls:
                    duplicate_count += 1
                    print(f"URL重复，跳过: {news.title}")
                    continue

                # 2. 检查标题是否已存在
                if news.title in history_titles:
                    duplicate_count += 1
                    print(f"标题重复，跳过: {news.title}")
                    continue

                # 通过去重检查
                deduplicated_news.append(news)

            print(f"去重完成: 原始 {len(state.filtered_news_list)} 条，去重 {duplicate_count} 条，剩余 {len(deduplicated_news)} 条")

            # 如果去重后没有新闻，打印警告
            if not deduplicated_news:
                print("警告: 去重后没有剩余的新闻！")

            return DeduplicateNewsOutput(filtered_news_list=deduplicated_news)

        finally:
            db.close()

    except Exception as e:
        print(f"去重失败: {str(e)}，使用原始新闻列表")
        # 如果去重失败，返回原始新闻列表（保守处理）
        return DeduplicateNewsOutput(filtered_news_list=state.filtered_news_list)


def extract_date_node(state: ExtractDateInput, config: RunnableConfig, runtime: Runtime[Context]) -> ExtractDateOutput:
    """
    title: 提取并过滤新闻日期
    desc: 直接使用网络搜索返回的日期字段，只保留近3个月内的新闻
    """
    # 检查是否为空列表
    if not state.news_list:
        print("新闻列表为空，跳过日期过滤")
        return ExtractDateOutput(filtered_news_list=[])
    
    # 计算近3个月的截止日期
    from datetime import timedelta
    today = datetime.now()
    three_months_ago = today - timedelta(days=90)
    cutoff_date_str = three_months_ago.strftime('%Y-%m-%d')
    
    print(f"日期过滤截止日期: {cutoff_date_str}")
    
    filtered_news = []
    no_date_count = 0
    old_date_count = 0
    
    for news in state.news_list:
        try:
            # 直接使用已有的日期字段
            news_date = news.date if news.date else ""
            
            # 如果没有日期，使用当前日期（保守处理）
            if not news_date:
                news_date = today.strftime('%Y-%m-%d')
                no_date_count += 1
                print(f"新闻无日期，使用当前日期: {news.title}")
            
            # 检查日期格式是否为 YYYY-MM-DD
            import re
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', news_date):
                print(f"日期格式无效，跳过: {news.title}, 日期: {news_date}")
                continue
            
            # 判断日期是否在近3个月内
            if news_date >= cutoff_date_str:
                # 更新新闻的日期字段（确保格式正确）
                news.date = news_date
                filtered_news.append(news)
            else:
                old_date_count += 1
                print(f"新闻已过滤（日期过早）: {news.title}, 日期: {news_date}")
            
        except Exception as e:
            # 如果处理失败，跳过该新闻
            print(f"处理日期失败: {str(e)}, 跳过新闻: {news.title}")
            continue
    
    print(f"日期过滤完成: 原始 {len(state.news_list)} 条，无日期 {no_date_count} 条，过期 {old_date_count} 条，保留 {len(filtered_news)} 条")
    
    return ExtractDateOutput(filtered_news_list=filtered_news)


def extract_news_info_node(state: ExtractNewsInfoInput, config: RunnableConfig, runtime: Runtime[Context]) -> ExtractNewsInfoOutput:
    """
    title: 提取新闻信息
    desc: 使用大语言模型为每条新闻生成摘要、提取关键词、来源和地区信息
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 检查是否为空列表
    if not state.filtered_news_list:
        print("新闻列表为空，跳过信息提取")
        return ExtractNewsInfoOutput(enriched_news_list=[])
    
    # 读取配置文件
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r') as fd:
        _cfg = json.load(fd)
    
    llm_config = _cfg.get("config", {})
    system_prompt = _cfg.get("sp", "")
    user_prompt_template = _cfg.get("up", "")
    
    # 导入大语言模型调用
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage, BaseMessageChunk
    from coze_coding_utils.runtime_ctx.context import default_headers
    
    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
    
    enriched_news = []
    
    for news in state.filtered_news_list:
        try:
            # 渲染用户提示词
            up_tpl = Template(user_prompt_template)
            user_prompt = up_tpl.render({
                "title": news.title,
                "original_summary": news.summary,
                "url": news.url,
                "content": news.content
            })
            
            # 调用大语言模型
            llm = ChatOpenAI(
                model=llm_config.get("model", "doubao-seed-1-6-251015"),
                api_key=api_key,
                base_url=base_url,
                streaming=True,
                extra_body={
                    "thinking": {
                        "type": "disabled"
                    }
                },
                temperature=llm_config.get("temperature", 0.4),
                max_tokens=llm_config.get("max_tokens", 600),
                default_headers=default_headers(ctx),
            )
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # 收集流式输出
            result_text = ""
            for chunk in llm.stream(messages):
                if isinstance(chunk.content, str):
                    result_text += chunk.content
                elif isinstance(chunk.content, list):
                    for item in chunk.content:
                        if isinstance(item, str):
                            result_text += item
            
            # 解析结果 - 尝试提取JSON格式的摘要、来源、地区和关键词
            try:
                import re
                
                # 方法1: 尝试直接解析整个文本为JSON
                result_json = None
                try:
                    result_json = json.loads(result_text.strip())
                except:
                    pass
                
                # 方法2: 如果直接解析失败，使用正则表达式提取JSON对象
                if not result_json:
                    # 查找第一个完整的JSON对象（支持跨行）
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
                    if json_match:
                        try:
                            result_json = json.loads(json_match.group())
                        except:
                            pass
                
                # 方法3: 尝试匹配简化的JSON（单行，无嵌套）
                if not result_json:
                    json_match = re.search(r'\{[^}]*"summary"[^}]*"source"[^}]*"region"[^}]*"keywords"[^}]*\}', result_text)
                    if json_match:
                        result_json = json.loads(json_match.group())
                
                # 提取字段
                if result_json and isinstance(result_json, dict):
                    summary = result_json.get("summary", result_text)
                    source = result_json.get("source", "")
                    region = result_json.get("region", "")
                    keywords = result_json.get("keywords", [])
                else:
                    # 所有方法都失败，使用整个文本作为摘要
                    summary = result_text.strip()
                    source = ""
                    region = ""
                    keywords = []
                    
                # 确保keywords是列表
                if isinstance(keywords, str):
                    keywords = [k.strip() for k in keywords.split(',') if k.strip()]
                elif not isinstance(keywords, list):
                    keywords = []
                    
            except Exception as e:
                print(f"解析JSON失败: {str(e)}, 使用原始数据")
                summary = news.summary if news.summary else ""
                source = ""
                region = ""
                keywords = []
            
            # 更新新闻项
            news.summary = summary
            news.source = source
            news.region = region
            news.keywords = keywords
            enriched_news.append(news)
            
        except Exception as e:
            # 如果提取失败，保留原始新闻
            print(f"提取新闻信息失败: {str(e)}")
            news.summary = news.summary if news.summary else ""
            news.source = ""
            news.region = ""
            news.keywords = []
            enriched_news.append(news)
    
    return ExtractNewsInfoOutput(enriched_news_list=enriched_news)


def create_table_node(state: CreateTableInput, config: RunnableConfig, runtime: Runtime[Context]) -> CreateTableOutput:
    """
    title: 创建新闻表格
    desc: 将新闻数据创建为Excel表格文件
    """
    ctx = runtime.context
    
    try:
        import pandas as pd
        from datetime import datetime
        import os
        
        print(f"收到 {len(state.enriched_news_list)} 条新闻")
        if not state.enriched_news_list:
            print("警告：没有新闻需要创建表格")
            # 创建一个空的表格，包含表头
            empty_data = {
                "标题": [],
                "日期": [],
                "来源": [],
                "地区": [],
                "关键词": [],
                "链接": [],
                "摘要": []
            }
            df = pd.DataFrame(empty_data)
            
            today = datetime.now().strftime("%Y%m%d")
            filename = f"新闻汇总_{today}.xlsx"
            filepath = f"/tmp/{filename}"
            
            df.to_excel(filepath, index=False, engine='openpyxl')
            
            return CreateTableOutput(
                enriched_news_list=[],
                synced_count=0,
                table_filepath=filepath,
                table_filename=filename
            )
        
        # 准备数据
        table_data = []
        for news in state.enriched_news_list:
            keywords_str = ", ".join(news.keywords) if news.keywords else ""
            table_data.append({
                "标题": news.title,
                "日期": news.date,
                "来源": news.source,
                "地区": news.region,
                "关键词": keywords_str,
                "链接": news.url,
                "摘要": news.summary
            })
        
        # 创建DataFrame
        df = pd.DataFrame(table_data)
        
        # 生成文件名（包含日期）
        today = datetime.now().strftime("%Y%m%d")
        filename = f"新闻汇总_{today}.xlsx"
        filepath = f"/tmp/{filename}"
        
        # 保存为Excel文件
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        print(f"Excel表格已创建: {filepath}")
        
        # 将文件路径存储在全局状态中，供邮件节点使用
        # 通过修改全局状态实现
        # 这里我们返回文件路径，通过全局状态传递
        
        return CreateTableOutput(
            enriched_news_list=state.enriched_news_list,
            synced_count=len(state.enriched_news_list),
            table_filepath=filepath,
            table_filename=filename
        )
        
    except Exception as e:
        raise Exception(f"创建表格失败: {str(e)}")


def send_email_node(state: SendEmailInput, config: RunnableConfig, runtime: Runtime[Context]) -> SendEmailOutput:
    """
    title: 发送邮件通知
    desc: 将新闻汇总信息和Excel表格附件发送到指定邮箱
    integrations: 邮件
    """
    ctx = runtime.context
    
    try:
        # 导入邮件相关模块
        import smtplib
        import ssl
        import os
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        from email.header import Header
        from email.utils import formataddr, formatdate, make_msgid
        from coze_workload_identity import Client
        
        # 获取邮件配置
        client = Client()
        email_credential = client.get_integration_credential("integration-email-imap-smtp")
        email_config = json.loads(email_credential)
        
        print(f"邮件配置: {email_config.get('account')}")
        print(f"收件人列表: {state.emails_list}")
        print(f"新闻数量: {len(state.enriched_news_list)}")
        
        # 检查是否有新闻数据
        has_news = len(state.enriched_news_list) > 0
        
        if not has_news:
            print("⚠️ 没有新闻数据，将发送通知邮件")
        
        # 构建邮件内容（HTML格式）
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        if has_news:
            # 有新闻时，构建带新闻列表的邮件
            # 检查表格文件是否存在
            print(f"表格文件路径: {state.table_filepath}")
            print(f"表格文件存在: {os.path.exists(state.table_filepath) if state.table_filepath else False}")
            
            if not state.table_filepath or not os.path.exists(state.table_filepath):
                print("❌ 不发送邮件: 表格文件不存在")
                return SendEmailOutput(
                    email_sent=False,
                    email_message=f"表格文件不存在: {state.table_filepath}"
                )
            
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                    .summary {{ background-color: #f8f8f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                    .attachment-note {{ background-color: #fff3cd; border: 1px solid #ffeeba; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center; }}
                    .news-item {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                    .news-item:hover {{ box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                    .news-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #2c3e50; }}
                    .news-meta {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
                    .news-summary {{ margin-bottom: 10px; }}
                    .news-keywords {{ color: #e74c3c; font-size: 14px; }}
                    .news-link {{ color: #3498db; text-decoration: none; }}
                    .news-link:hover {{ text-decoration: underline; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #999; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>医疗器械医美新闻汇总</h2>
                        <p>日期: {today}</p>
                    </div>
                    
                    <div class="attachment-note">
                        <p><strong>📎 详细数据已作为附件发送</strong></p>
                        <p>附件文件: {state.table_filename}</p>
                        <p>包含 {len(state.enriched_news_list)} 条新闻记录</p>
                    </div>
                    
                    <div class="summary">
                        <p><strong>共收集到 {len(state.enriched_news_list)} 条相关新闻</strong></p>
                        <p>来源: 网络搜集</p>
                    </div>
            """
            
            # 添加每条新闻
            for idx, news in enumerate(state.enriched_news_list, 1):
                keywords_str = ", ".join(news.keywords) if news.keywords else "无"
                source_str = news.source if news.source else "未知"
                region_str = news.region if news.region else "-"
                html_content += f"""
                <div class="news-item">
                    <div class="news-title">{idx}. {news.title}</div>
                    <div class="news-meta">
                        <strong>日期:</strong> {news.date} |
                        <strong>来源:</strong> {source_str} |
                        <strong>地区:</strong> {region_str} |
                        <strong>关键词:</strong> <span class="news-keywords">{keywords_str}</span>
                    </div>
                    <div class="news-summary">
                        <strong>摘要:</strong> {news.summary}
                    </div>
                    <div>
                        <a href="{news.url}" class="news-link">查看原文 &rarr;</a>
                    </div>
                </div>
            """
            
            html_content += f"""
                    <div class="footer">
                        <p>此邮件由新闻收集助手自动发送</p>
                        <p>如有问题，请联系管理员</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 读取Excel文件内容
            with open(state.table_filepath, 'rb') as f:
                file_content = f.read()
        else:
            # 没有新闻时，构建通知邮件
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #ff9800; color: white; padding: 20px; text-align: center; }}
                    .notice {{ background-color: #fff3cd; border: 1px solid #ffeeba; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #999; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>医疗器械医美新闻汇总</h2>
                        <p>日期: {today}</p>
                    </div>
                    
                    <div class="notice">
                        <h3>⚠️ 今日未收集到新新闻</h3>
                        <p>可能的原因：</p>
                        <ul>
                            <li>今日无医疗器械或医美相关新闻</li>
                            <li>所有新闻已在之前发送过（已去重）</li>
                            <li>网络搜索服务暂时不可用</li>
                        </ul>
                        <p><strong>工作流已正常运行，请勿担心。</strong></p>
                        <p>建议：明天再检查一次，或联系管理员。</p>
                    </div>
                    
                    <div class="footer">
                        <p>此邮件由新闻收集助手自动发送</p>
                        <p>如有问题，请联系管理员</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        # 构建邮件内容（HTML格式）
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .summary {{ background-color: #f8f8f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .attachment-note {{ background-color: #fff3cd; border: 1px solid #ffeeba; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center; }}
                .news-item {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .news-item:hover {{ box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .news-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #2c3e50; }}
                .news-meta {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
                .news-summary {{ margin-bottom: 10px; }}
                .news-keywords {{ color: #e74c3c; font-size: 14px; }}
                .news-link {{ color: #3498db; text-decoration: none; }}
                .news-link:hover {{ text-decoration: underline; }}
                .footer {{ text-align: center; margin-top: 30px; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>医疗器械医美新闻汇总</h2>
                    <p>日期: {today}</p>
                </div>
                
                <div class="attachment-note">
                    <p><strong>📎 详细数据已作为附件发送</strong></p>
                    <p>附件文件: {state.table_filename}</p>
                    <p>包含 {len(state.enriched_news_list)} 条新闻记录</p>
                </div>
                
                <div class="summary">
                    <p><strong>共收集到 {len(state.enriched_news_list)} 条相关新闻</strong></p>
                    <p>来源: 今日头条、搜狐、人民网、新华网、央视网</p>
                </div>
        """
        
        # 添加每条新闻
        for idx, news in enumerate(state.enriched_news_list, 1):
            keywords_str = ", ".join(news.keywords) if news.keywords else "无"
            source_str = news.source if news.source else "未知"
            region_str = news.region if news.region else "-"
            html_content += f"""
                <div class="news-item">
                    <div class="news-title">{idx}. {news.title}</div>
                    <div class="news-meta">
                        <strong>日期:</strong> {news.date} |
                        <strong>来源:</strong> {source_str} |
                        <strong>地区:</strong> {region_str} |
                        <strong>关键词:</strong> <span class="news-keywords">{keywords_str}</span>
                    </div>
                    <div class="news-summary">
                        <strong>摘要:</strong> {news.summary}
                    </div>
                    <div>
                        <a href="{news.url}" class="news-link">查看原文 &rarr;</a>
                    </div>
                </div>
            """
        
        html_content += f"""
                <div class="footer">
                    <p>此邮件由新闻收集助手自动发送</p>
                    <p>如有问题，请联系管理员</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 分别发送给每个收件人
        success_count = 0
        failed_emails = []
        
        # 为每个收件人单独发送邮件
        for idx, recipient_email in enumerate(state.emails_list):
            try:
                # 判断是否为第一个收件人（只有第一个收件人才发送附件）
                is_first_recipient = (idx == 0)
                
                # 创建邮件
                if has_news:
                    # 有新闻时，创建多部分邮件（HTML + 附件）
                    msg = MIMEMultipart()
                    msg["From"] = formataddr(("Huxg", email_config["account"]))
                    msg["To"] = recipient_email  # 只显示一个收件地址
                    msg["Subject"] = Header(f"医疗器械医美新闻汇总 - {today}", 'utf-8')
                    msg["Date"] = formatdate(localtime=True)
                    msg["Message-ID"] = make_msgid()
                    
                    # 添加HTML正文
                    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
                    
                    # 只有第一个收件人才添加Excel附件
                    if is_first_recipient:
                        # 添加Excel附件
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(file_content)
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{Header(state.table_filename, "utf-8").encode()}'
                        )
                        msg.attach(part)
                else:
                    # 没有新闻时，只发送HTML通知邮件
                    msg = MIMEText(html_content, 'html', 'utf-8')
                    msg["From"] = formataddr(("Huxg", email_config["account"]))
                    msg["To"] = recipient_email
                    msg["Subject"] = Header(f"新闻汇总 - {today}（无新新闻）", 'utf-8')
                    msg["Date"] = formatdate(localtime=True)
                    msg["Message-ID"] = make_msgid()
                
                # 发送邮件
                ctx_ssl = ssl.create_default_context()
                ctx_ssl.minimum_version = ssl.TLSVersion.TLSv1_2
                
                with smtplib.SMTP_SSL(
                    email_config["smtp_server"],
                    email_config["smtp_port"],
                    context=ctx_ssl,
                    timeout=30
                ) as server:
                    server.ehlo()
                    server.login(email_config["account"], email_config["auth_code"])
                    # 只发送给当前收件人
                    server.sendmail(email_config["account"], [recipient_email], msg.as_string())
                    server.quit()
                
                success_count += 1
                if has_news and is_first_recipient:
                    print(f"✅ 邮件已成功发送到: {recipient_email}（含附件）")
                elif has_news:
                    print(f"✅ 邮件已成功发送到: {recipient_email}（无附件）")
                else:
                    print(f"✅ 邮件已成功发送到: {recipient_email}")
                
            except Exception as e:
                print(f"❌ 发送到 {recipient_email} 失败: {str(e)}")
                failed_emails.append(f"{recipient_email}: {str(e)}")
        
        # 返回发送结果
        if success_count > 0:
            if failed_emails:
                message = f"邮件已成功发送到 {success_count} 个收件人。失败的邮箱: {', '.join(failed_emails)}"
            else:
                if has_news:
                    message = f"邮件已成功发送到所有 {success_count} 个收件人，包含 {len(state.enriched_news_list)} 条新闻（仅第一个邮箱含Excel附件）"
                else:
                    message = f"已成功发送通知邮件到所有 {success_count} 个收件人（今日无新新闻）"
            return SendEmailOutput(
                email_sent=True,
                email_message=message
            )
        else:
            return SendEmailOutput(
                email_sent=False,
                email_message=f"邮件发送失败: {', '.join(failed_emails)}"
            )
        
    except smtplib.SMTPAuthenticationError as e:
        return SendEmailOutput(
            email_sent=False,
            email_message=f"邮件认证失败: {str(e)}"
        )
    except smtplib.SMTPRecipientsRefused as e:
        return SendEmailOutput(
            email_sent=False,
            email_message=f"收件人地址被拒绝"
        )
    except Exception as e:
        return SendEmailOutput(
            email_sent=False,
            email_message=f"发送邮件失败: {str(e)}"
        )


def save_news_history_node(state: SaveNewsHistoryInput, config: RunnableConfig, runtime: Runtime[Context]) -> SaveNewsHistoryOutput:
    """
    title: 保存新闻历史记录
    desc: 将已发送的新闻保存到数据库，用于后续去重
    integrations: 数据库
    """
    ctx = runtime.context
    
    # 检查是否为空列表
    if not state.enriched_news_list:
        print("新闻列表为空，无需保存历史记录")
        return SaveNewsHistoryOutput(
            saved_count=0,
            message="新闻列表为空，无需保存历史记录"
        )
    
    try:
        from storage.database.db import get_session
        from storage.database.news_history_manager import NewsHistoryManager, NewsHistoryCreate
        
        # 获取数据库会话
        db = get_session()
        
        try:
            # 创建管理器
            mgr = NewsHistoryManager()
            
            # 准备批量创建的数据
            news_history_list = []
            for news in state.enriched_news_list:
                news_create = NewsHistoryCreate(
                    title=news.title,
                    url=news.url,
                    date=news.date,
                    source=news.source
                )
                news_history_list.append(news_create)
            
            # 批量保存到数据库
            saved_records = mgr.batch_create_news_history(db, news_history_list)
            
            saved_count = len(saved_records)
            print(f"成功保存 {saved_count} 条新闻历史记录")
            
            # 清理旧数据（删除180天之前的记录）
            try:
                deleted_count = mgr.delete_old_news(db, days=180)
                if deleted_count > 0:
                    print(f"清理了 {deleted_count} 条180天前的历史记录")
            except Exception as e:
                print(f"清理历史记录失败: {str(e)}")
            
            return SaveNewsHistoryOutput(
                saved_count=saved_count,
                message=f"成功保存 {saved_count} 条新闻历史记录"
            )
            
        finally:
            db.close()
            
    except Exception as e:
        raise Exception(f"保存新闻历史记录失败: {str(e)}")
