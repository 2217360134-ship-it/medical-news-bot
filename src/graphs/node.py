from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from graphs.state import (
    FetchNewsInput, FetchNewsOutput,
    FilterNewsInput, FilterNewsOutput,
    ExtractKeywordsInput, ExtractKeywordsOutput,
    SyncToFeishuInput, SyncToFeishuOutput,
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
        
        return FetchNewsOutput(news_list=final_news)
        
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


def sync_to_feishu_node(state: SyncToFeishuInput, config: RunnableConfig, runtime: Runtime[Context]) -> SyncToFeishuOutput:
    """
    title: 同步到飞书多维表格
    desc: 将新闻数据批量写入飞书多维表格
    integrations: 飞书多维表格
    """
    ctx = runtime.context
    
    # 导入飞书多维表格客户端
    from tools.feishu_bitable_tool import FeishuBitable
    
    try:
        print(f"收到 {len(state.news_list)} 条新闻")
        if not state.news_list:
            print("警告：没有新闻需要同步")
            return SyncToFeishuOutput(
                synced_count=0,
                app_token="",
                table_id=""
            )
        
        # 创建飞书客户端
        client = FeishuBitable()
        
        app_token = state.app_token
        table_id = state.table_id
        
        # 如果没有提供app_token和table_id，提示用户需要提供
        if not app_token or not table_id:
            print("提示：为了正确使用此工作流，请提供飞书多维表格的app_token和table_id")
            print("或者，工作流将无法自动创建Base和表")
            
            # 尝试创建新的Base和表（可能失败）
            try:
                # 创建新的Base
                print("开始创建Base...")
                base_resp = client.create_base(name="医疗器械医美新闻收集")
                app_token = base_resp["data"]["app"]["app_token"]
                print(f"创建Base成功: app_token={app_token}")
            except Exception as create_base_error:
                print(f"创建Base失败: {str(create_base_error)}")
                raise Exception(f"无法自动创建飞书Base: {str(create_base_error)}")
            
            try:
                # 创建数据表（使用不同的请求格式）
                print("开始创建表...")
                # 尝试使用table格式，并添加字段
                table_resp = client._request(
                    "POST",
                    f"/bitable/v1/apps/{app_token}/tables",
                    json={
                        "table": {
                            "name": "news_data",
                            "fields": [
                                {
                                    "field_name": "标题",
                                    "type": 1
                                },
                                {
                                    "field_name": "日期",
                                    "type": 1
                                },
                                {
                                    "field_name": "关键词",
                                    "type": 1
                                },
                                {
                                    "field_name": "链接",
                                    "type": 1
                                },
                                {
                                    "field_name": "摘要",
                                    "type": 1
                                }
                            ]
                        }
                    }
                )
                print(f"创建表响应: {table_resp}")
                
                # 检查响应结构
                if "data" in table_resp:
                    if "table" in table_resp["data"]:
                        table_id = table_resp["data"]["table"]["table_id"]
                        print(f"创建表成功: table_id={table_id}")
                    else:
                        print(f"响应中没有table键，data内容: {table_resp['data']}")
                        # 尝试直接获取table_id
                        table_id = table_resp["data"].get("table_id", "")
                        if not table_id:
                            raise Exception("无法从响应中获取table_id")
                else:
                    print(f"响应中没有data键，完整响应: {table_resp}")
                    raise Exception("响应格式不正确")
            except Exception as create_table_error:
                print(f"创建表失败: {str(create_table_error)}")
                raise Exception(f"无法自动创建飞书表: {str(create_table_error)}")
            except Exception as create_error:
                print(f"创建Base或表失败: {str(create_error)}")
                print("请手动创建飞书多维表格，并提供app_token和table_id")
                raise Exception(f"无法自动创建飞书Base和表，请提供app_token和table_id: {str(create_error)}")
        
        # 准备批量插入的记录
        records = []
        for news in state.news_list:
            # 将关键词列表转换为逗号分隔的字符串
            keywords_str = ", ".join(news.keywords) if news.keywords else ""
            
            records.append({
                "fields": {
                    "标题": str(news.title) if news.title else "",
                    "日期": str(news.date) if news.date else "",
                    "关键词": keywords_str,
                    "链接": str(news.url) if news.url else "",
                    "摘要": str(news.summary) if news.summary else ""
                }
            })
        
        # 批量插入记录
        if records:
            try:
                sync_resp = client.add_records(
                    app_token=app_token,
                    table_id=table_id,
                    records=records,
                    user_id_type="open_id"
                )
                synced_count = len(sync_resp.get("data", {}).get("records", []))
            except Exception as sync_error:
                print(f"插入记录失败: {str(sync_error)}")
                print(f"records内容: {records[:1] if records else []}")  # 打印第一条记录
                raise Exception(f"同步到飞书失败: {str(sync_error)}")
        else:
            synced_count = 0
        
        return SyncToFeishuOutput(
            synced_count=synced_count,
            app_token=app_token,
            table_id=table_id
        )
        
    except Exception as e:
        raise Exception(f"同步到飞书失败: {str(e)}")
