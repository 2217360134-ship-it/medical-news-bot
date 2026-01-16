"""
循环搜索子图 - 循环搜索直到达到目标新闻数量
"""
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from graphs.state import LoopGlobalState
from langgraph.graph import StateGraph, END
import os
from datetime import datetime


def fetch_batch_node(state: LoopGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> dict:
    """
    title: 批次搜索新闻
    desc: 从多个来源搜索医疗器械和医美相关的新闻（用于循环搜索）
    integrations: 联网搜索
    """
    ctx = runtime.context

    print("=" * 60)
    print(f"[循环搜索-{state.search_count + 1}] 开始批次搜索")
    print("=" * 60)

    # 导入网络搜索函数
    from tools.web_search_tool import web_search

    # 导入NewsItem
    from graphs.state import NewsItem

    # 检查环境变量
    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_BASE_URL")

    if not api_key or not base_url:
        error_msg = "缺少必要的环境变量：COZE_WORKLOAD_IDENTITY_API_KEY 或 COZE_INTEGRATION_BASE_URL"
        print(f"❌ 错误: {error_msg}")
        raise Exception(error_msg)

    news_list = []

    # 定义目标新闻来源域名（与主图保持一致）
    target_sites_batch1 = "toutiao.com|sohu.com|qq.com|163.com|ifeng.com"
    target_sites_batch2 = "sina.com.cn|thepaper.cn|36kr.com"
    target_sites_batch3 = "ylqx.qgyyzs.net|finance.sina.com.cn"

    # 构建核心搜索词列表（与主图保持一致）
    batch1_queries = [
        "医疗器械公司",
        "医疗器械产品",
        "医疗器械技术",
        "医美公司",
        "医美产品",
        "医美技术"
    ]

    batch2_queries = [
        "医疗设备",
        "诊断设备",
        "激光美容",
        "整形美容",
        "微整形"
    ]

    batch3_queries = [
        "IVD 体外诊断",
        "医疗器械融资",
        "医疗器械上市",
        "医美融资",
        "医美上市"
    ]

    try:
        # 分批搜索
        all_web_items = []
        search_success_count = 0

        print(f"开始批次搜索，第一批次网站: {target_sites_batch1}")

        # 第一批次
        for idx, query in enumerate(batch1_queries, 1):
            try:
                print(f"  [批次1-{idx}/{len(batch1_queries)}] 搜索: '{query}'")

                web_items, _, _, _ = web_search(
                    ctx=ctx,
                    query=query,
                    search_type="web",
                    count=10,
                    need_summary=True,
                    need_content=True,
                    sites=target_sites_batch1
                )

                print(f"    ✅ 获取到 {len(web_items)} 条新闻")
                all_web_items.extend(web_items)
                search_success_count += 1

            except Exception as e:
                print(f"    ❌ 搜索失败: {str(e)}")
                continue

        print(f"开始批次搜索，第二批次网站: {target_sites_batch2}")

        # 第二批次
        for idx, query in enumerate(batch2_queries, 1):
            try:
                print(f"  [批次2-{idx}/{len(batch2_queries)}] 搜索: '{query}'")

                web_items, _, _, _ = web_search(
                    ctx=ctx,
                    query=query,
                    search_type="web",
                    count=10,
                    need_summary=True,
                    need_content=True,
                    sites=target_sites_batch2
                )

                print(f"    ✅ 获取到 {len(web_items)} 条新闻")
                all_web_items.extend(web_items)
                search_success_count += 1

            except Exception as e:
                print(f"    ❌ 搜索失败: {str(e)}")
                continue

        print(f"开始批次搜索，第三批次网站: {target_sites_batch3}")

        # 第三批次
        for idx, query in enumerate(batch3_queries, 1):
            try:
                print(f"  [批次3-{idx}/{len(batch3_queries)}] 搜索: '{query}'")

                web_items, _, _, _ = web_search(
                    ctx=ctx,
                    query=query,
                    search_type="web",
                    count=10,
                    need_summary=True,
                    need_content=True,
                    sites=target_sites_batch3
                )

                print(f"    ✅ 获取到 {len(web_items)} 条新闻")
                all_web_items.extend(web_items)
                search_success_count += 1

            except Exception as e:
                print(f"    ❌ 搜索失败: {str(e)}")
                continue

        print(f"\n批次搜索完成: 成功 {search_success_count} 个查询，原始 {len(all_web_items)} 条")

        # 转换为NewsItem格式
        for item in all_web_items:
            if not item.Url:
                continue

            # 解析日期
            if item.PublishTime:
                try:
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

        # 批次内去重（URL和标题）
        seen_urls = set()
        unique_by_url = []
        for news in news_list:
            if news.url not in seen_urls:
                seen_urls.add(news.url)
                unique_by_url.append(news)

        seen_titles = set()
        final_news = []
        for news in unique_by_url:
            normalized_title = news.title.lower().strip()
            for suffix in ['| toutiao', '- 今日头条', '_头条', '_新闻', '_资讯']:
                normalized_title = normalized_title.replace(suffix.lower(), '')

            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                final_news.append(news)

        print(f"批次内去重后: {len(final_news)} 条")
        print("=" * 60)

        # 返回更新后的状态
        return {
            "current_batch_news": final_news
        }

    except Exception as e:
        print(f"❌ 批次搜索失败: {str(e)}")
        raise Exception(f"批次搜索失败: {str(e)}")


def deduplicate_batch_node(state: LoopGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> dict:
    """
    title: 批次去重
    desc: 将当前批次的新闻与累积列表去重，避免重复
    """
    print("=" * 60)
    print(f"[循环搜索-{state.search_count + 1}] 批次去重")
    print(f"  当前批次: {len(state.current_batch_news)} 条")
    print(f"  累积列表: {len(state.accumulated_news)} 条")
    print("=" * 60)

    # 获取累积列表中的URL和标题
    accumulated_urls = {news.url for news in state.accumulated_news}
    accumulated_titles = {news.title for news in state.accumulated_news}

    deduplicated_news = []
    duplicate_count = 0

    for news in state.current_batch_news:
        # 检查URL是否已存在
        if news.url in accumulated_urls:
            duplicate_count += 1
            print(f"  URL重复，跳过: {news.title[:50]}...")
            continue

        # 检查标题是否已存在
        if news.title in accumulated_titles:
            duplicate_count += 1
            print(f"  标题重复，跳过: {news.title[:50]}...")
            continue

        # 通过去重检查
        deduplicated_news.append(news)

    print(f"批次去重完成: 去重 {duplicate_count} 条，剩余 {len(deduplicated_news)} 条")
    print("=" * 60)

    # 返回更新后的状态
    return {
        "current_batch_news": deduplicated_news
    }


def accumulate_node(state: LoopGlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> dict:
    """
    title: 累积新闻
    desc: 将去重后的当前批次新闻累积到总列表，并更新搜索次数
    """
    import time

    print("=" * 60)
    print(f"[循环搜索-{state.search_count + 1}] 累积新闻")
    print(f"  新增: {len(state.current_batch_news)} 条")
    print(f"  累积前: {len(state.accumulated_news)} 条")

    # 累积新闻
    new_accumulated = state.accumulated_news + state.current_batch_news
    new_search_count = state.search_count + 1

    print(f"  累积后: {len(new_accumulated)} 条")
    print(f"  搜索次数: {new_search_count}")
    print("=" * 60)

    # 检查是否需要继续搜索，如果需要则等待30秒
    if len(new_accumulated) < state.target_count and new_search_count < state.max_searches:
        print(f"\n⏳ 等待30秒后继续下一次搜索...")
        print(f"   当前进度: {len(new_accumulated)}/{state.target_count} 条")
        print(f"   搜索进度: {new_search_count}/{state.max_searches} 次")
        time.sleep(30)
        print(f"✅ 等待结束，开始下一次搜索\n")

    # 返回更新后的状态
    return {
        "accumulated_news": new_accumulated,
        "search_count": new_search_count
    }


def check_threshold(state: LoopGlobalState) -> str:
    """
    title: 检查是否达到目标
    desc: 根据累积新闻数量和搜索次数判断是否继续搜索
    """
    current_count = len(state.accumulated_news)
    target = state.target_count
    max_searches = state.max_searches

    print("=" * 60)
    print(f"[循环搜索] 检查阈值")
    print(f"  当前数量: {current_count}")
    print(f"  目标数量: {target}")
    print(f"  搜索次数: {state.search_count}")
    print(f"  最大次数: {max_searches}")
    print("=" * 60)

    if current_count >= target:
        print(f"✅ 已达到目标数量 ({current_count} >= {target})")
        return "达到目标"
    elif state.search_count >= max_searches:
        print(f"⚠️ 已达到最大搜索次数 ({state.search_count} >= {max_searches})")
        print(f"   当前数量: {current_count}, 目标数量: {target}")
        return "达到最大次数"
    else:
        print(f"⏳ 未达到目标，继续搜索")
        return "继续搜索"


# 子图编排
builder = StateGraph(LoopGlobalState)

# 添加节点
builder.add_node("fetch_batch", fetch_batch_node)
builder.add_node("deduplicate_batch", deduplicate_batch_node)
builder.add_node("accumulate", accumulate_node)

# 设置入口点
builder.set_entry_point("fetch_batch")

# 添加边
builder.add_edge("fetch_batch", "deduplicate_batch")
builder.add_edge("deduplicate_batch", "accumulate")

# 添加条件分支
builder.add_conditional_edges(
    source="accumulate",
    path=check_threshold,
    path_map={
        "继续搜索": "fetch_batch",
        "达到目标": END,
        "达到最大次数": END
    }
)

# 编译子图
loop_graph = builder.compile()
