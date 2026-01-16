from langgraph.graph import StateGraph, END
from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput
)
from graphs.node import (
    split_emails_node,
    search_until_10_node,
    enrich_news_node,
    create_table_node,
    send_email_node,
    save_news_history_node
)

# 创建状态图, 一定指定工作流的入参和出参
builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

# 添加节点（为所有节点添加metadata以便预览正确显示）
builder.add_node("split_emails", split_emails_node, metadata={"type": "normal"})
builder.add_node("search_until_10", search_until_10_node, metadata={"type": "normal"})
builder.add_node("enrich_news", enrich_news_node, metadata={"type": "agent", "llm_cfg": "config/enrich_news_llm_cfg.json"})
builder.add_node("create_table", create_table_node, metadata={"type": "normal"})
builder.add_node("send_email", send_email_node, metadata={"type": "normal"})
builder.add_node("save_news_history", save_news_history_node, metadata={"type": "normal"})


# 条件判断函数：检查是否有新闻
def check_has_news(state: GlobalState) -> str:
    """
    检查 filtered_news_list 是否为空
    """
    if state.filtered_news_list and len(state.filtered_news_list) >= 5:
        return "有新闻"
    else:
        return "无新闻"


# 设置入口点
builder.set_entry_point("split_emails")

# 添加边 - 线性工作流架构
# split_emails -> search_until_10（循环搜索5-20条新闻）
builder.add_edge("split_emails", "search_until_10")

# search_until_10 -> 条件判断
builder.add_conditional_edges(
    source="search_until_10",
    path=check_has_news,
    path_map={
        "有新闻": "enrich_news",
        "无新闻": END
    }
)

# enrich_news -> create_table
builder.add_edge("enrich_news", "create_table")

# create_table -> send_email
builder.add_edge("create_table", "send_email")

# send_email -> save_news_history（保存历史记录） -> END
builder.add_edge("send_email", "save_news_history")
builder.add_edge("save_news_history", END)

# 编译图
main_graph = builder.compile()
