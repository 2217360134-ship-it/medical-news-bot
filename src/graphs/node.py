from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from graphs.state import (
    FetchNewsInput, FetchNewsOutput,
    FilterNewsInput, FilterNewsOutput,
    GenerateSummaryInput, GenerateSummaryOutput,
    ExtractKeywordsInput, ExtractKeywordsOutput,
    CreateTableInput, CreateTableOutput,
    SendEmailInput, SendEmailOutput,
    NewsItem
)
import os
from datetime import datetime
from cozeloop.decorator import observe
import json
from jinja2 import Template


def fetch_news_node(state: FetchNewsInput, config: RunnableConfig, runtime: Runtime[Context]) -> FetchNewsOutput:
    """
    title: 获取指定来源新闻
    desc: 从今日头条、搜狐、人民网、新华网、央视网等获取医疗器械和医美相关的新闻
    integrations: 联网搜索
    """
    ctx = runtime.context
    
    # 将emails字符串分割成列表（支持逗号、分号、空格分隔）
    emails_str = state.emails or ""
    emails_list = [email.strip() for email in emails_str.replace(';', ',').replace(' ', ',').split(',') if email.strip()]
    
    print(f"分割后的邮箱列表: {emails_list}")
    
    # 导入网络搜索函数
    from tools.web_search_tool import web_search
    
    news_list = []
    
    # 定义目标新闻来源域名（最多支持5个）
    target_sites = "toutiao.com|sohu.com|people.com.cn|xinhuanet.com|cctv.com"
    
    try:
        # 搜索医疗器械相关新闻（限定来源）
        web_items1, _, _, _ = web_search(
            ctx=ctx,
            query="医疗器械",
            search_type="web",
            count=20,
            need_summary=True,
            sites=target_sites
        )
        
        # 搜索医美相关新闻（限定来源）
        web_items2, _, _, _ = web_search(
            ctx=ctx,
            query="医美",
            search_type="web",
            count=20,
            need_summary=True,
            sites=target_sites
        )
        
        # 合并搜索结果
        all_web_items = web_items1 + web_items2
        
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
        
        return FetchNewsOutput(news_list=final_news, emails_list=emails_list)
        
    except Exception as e:
        raise Exception(f"获取新闻失败: {str(e)}")


def filter_news_node(state: FilterNewsInput, config: RunnableConfig, runtime: Runtime[Context]) -> FilterNewsOutput:
    """
    title: 筛选相关新闻
    desc: 根据关键词筛选医疗器械和医美相关的新闻
    """
    ctx = runtime.context
    
    # 定义医疗器械和医美相关关键词（更精确）
    medical_keywords = [
        # 医疗器械设备
        '医疗器械', '医疗设备', '手术器械', '诊断设备', '治疗设备',
        '医疗影像', '监护设备', '呼吸机', '心电', '超声', 'CT', 'MRI',
        # 医美相关
        '医美', '医疗美容', '整形', '美容注射', '激光美容', '抗衰老',
        '植发', '隆鼻', '隆胸', '吸脂', '微整', '皮肤管理',
        # 公司和技术相关
        '迈瑞医疗', '联影医疗', '微创医疗', '威高集团', '乐普医疗',
        '骨科植入', '介入治疗', '体外诊断', 'IVD', '耗材',
        # 融资相关
        '融资', '上市', 'IPO', '投资', '并购', '收购',
        '医疗器械融资', '医美融资', '估值'
    ]
    
    # 排除关键词（不包含这些内容的新闻将被排除）
    exclude_keywords = [
        '美容护肤', '化妆品', '面膜', '护肤品', '洗发水',
        '美妆', '彩妆', '日常护理', '生活美容',
        '广告', '促销', '优惠', '打折', '活动',
        '双十一', '618', '购物', '电商'
    ]
    
    filtered_news = []
    
    for news in state.news_list:
        # 检查标题和摘要是否包含相关关键词
        title_lower = news.title.lower()
        summary_lower = news.summary.lower()
        
        # 检查是否包含排除关键词（如果包含，直接跳过）
        is_excluded = False
        for exclude_keyword in exclude_keywords:
            if exclude_keyword.lower() in title_lower or exclude_keyword.lower() in summary_lower:
                is_excluded = True
                break
        
        if is_excluded:
            continue
        
        # 检查是否包含医疗器械相关关键词
        is_related = False
        for keyword in medical_keywords:
            if keyword.lower() in title_lower or keyword.lower() in summary_lower:
                is_related = True
                break
        
        # 只保留相关的新闻
        if is_related:
            filtered_news.append(news)
    
    return FilterNewsOutput(filtered_news_list=filtered_news)


def generate_summary_node(state: GenerateSummaryInput, config: RunnableConfig, runtime: Runtime[Context]) -> GenerateSummaryOutput:
    """
    title: 生成新闻摘要
    desc: 使用大语言模型为每条新闻生成真实的精简摘要
    integrations: 大语言模型
    """
    ctx = runtime.context
    
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
    
    summarized_news = []
    
    for news in state.news_list:
        try:
            # 渲染用户提示词
            up_tpl = Template(user_prompt_template)
            user_prompt = up_tpl.render({
                "title": news.title,
                "original_summary": news.summary,
                "url": news.url
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
                temperature=llm_config.get("temperature", 0.5),
                max_tokens=llm_config.get("max_tokens", 300),
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
            
            # 解析结果 - 尝试提取JSON格式的摘要
            try:
                import re
                json_match = re.search(r'\{[^}]*"summary"[^}]*\}', result_text)
                if json_match:
                    result_json = json.loads(json_match.group())
                    summary = result_json.get("summary", result_text)
                else:
                    summary = result_text.strip()
            except:
                summary = result_text.strip()
            
            # 更新新闻项的摘要
            news.summary = summary
            summarized_news.append(news)
            
        except Exception as e:
            # 如果生成摘要失败，保留原始摘要
            print(f"生成摘要失败: {str(e)}, 使用原始摘要")
            summarized_news.append(news)
    
    return GenerateSummaryOutput(summarized_news_list=summarized_news)


def extract_keywords_node(state: ExtractKeywordsInput, config: RunnableConfig, runtime: Runtime[Context]) -> ExtractKeywordsOutput:
    """
    title: 提取关键词
    desc: 使用大语言模型为每条新闻提取关键词
    integrations: 大语言模型
    """
    ctx = runtime.context
    
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
    
    for news in state.news_list:
        try:
            # 渲染用户提示词
            up_tpl = Template(user_prompt_template)
            user_prompt = up_tpl.render({
                "title": news.title,
                "summary": news.summary
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
                temperature=llm_config.get("temperature", 0.3),
                max_tokens=llm_config.get("max_tokens", 500),
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
            
            # 解析结果
            # 尝试解析JSON
            try:
                import re
                json_match = re.search(r'\{[^}]*"keywords"[^}]*\}', result_text)
                if json_match:
                    result_json = json.loads(json_match.group())
                    keywords = result_json.get("keywords", [])
                else:
                    keywords = []
            except:
                # 如果JSON解析失败，尝试从文本中提取关键词
                keywords = [kw.strip() for kw in result_text.split('，') if kw.strip()][:5]
            
            # 更新新闻项
            news.keywords = keywords
            enriched_news.append(news)
            
        except Exception as e:
            # 如果提取失败，保留原始新闻
            news.keywords = []
            enriched_news.append(news)
    
    return ExtractKeywordsOutput(enriched_news_list=enriched_news)


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
        
        print(f"收到 {len(state.news_list)} 条新闻")
        if not state.news_list:
            print("警告：没有新闻需要创建表格")
            return CreateTableOutput(
                news_list=[],
                synced_count=0,
                table_filepath="",
                table_filename=""
            )
        
        # 准备数据
        table_data = []
        for news in state.news_list:
            keywords_str = ", ".join(news.keywords) if news.keywords else ""
            table_data.append({
                "标题": news.title,
                "日期": news.date,
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
            news_list=state.news_list,
            synced_count=len(state.news_list),
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
        
        # 检查是否有新闻数据
        if not state.news_list:
            return SendEmailOutput(
                email_sent=False,
                email_message="没有新闻需要发送"
            )
        
        # 检查表格文件是否存在
        if not state.table_filepath or not os.path.exists(state.table_filepath):
            return SendEmailOutput(
                email_sent=False,
                email_message=f"表格文件不存在: {state.table_filepath}"
            )
        
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
                    <p>包含 {len(state.news_list)} 条新闻记录</p>
                </div>
                
                <div class="summary">
                    <p><strong>共收集到 {len(state.news_list)} 条相关新闻</strong></p>
                    <p>来源: 今日头条、搜狐、人民网、新华网、央视网</p>
                </div>
        """
        
        # 添加每条新闻
        for idx, news in enumerate(state.news_list, 1):
            keywords_str = ", ".join(news.keywords) if news.keywords else "无"
            html_content += f"""
                <div class="news-item">
                    <div class="news-title">{idx}. {news.title}</div>
                    <div class="news-meta">
                        <strong>日期:</strong> {news.date} | 
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
                    <p>此邮件由新闻收集工作流自动发送</p>
                    <p>如有问题，请联系管理员</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 创建多部分邮件
        msg = MIMEMultipart()
        msg["From"] = formataddr(("新闻收集助手", email_config["account"]))
        msg["To"] = ", ".join(state.emails_list)  # 支持多个收件人
        msg["Subject"] = Header(f"医疗器械医美新闻汇总 - {today}", 'utf-8')
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()
        
        # 添加HTML正文
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # 添加Excel附件
        with open(state.table_filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{Header(state.table_filename, 'utf-8').encode()}'
        )
        msg.attach(part)
        
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
            # 发送给所有收件人
            server.sendmail(email_config["account"], state.emails_list, msg.as_string())
            server.quit()
        
        return SendEmailOutput(
            email_sent=True,
            email_message=f"邮件已成功发送到 {', '.join(state.emails_list)}，包含 {len(state.news_list)} 条新闻及Excel附件"
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
