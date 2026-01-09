from langgraph.graph import StateGraph, END
from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput
)
from graphs.node import (
    fetch_news_node,
    filter_news_node,
    extract_keywords_node,
    sync_to_feishu_node,
    send_email_node
)

# 创建状态图, 一定指定工作流的入参和出参
builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

# 添加节点
builder.add_node("fetch_news", fetch_news_node)
builder.add_node("filter_news", filter_news_node)
builder.add_node("extract_keywords", extract_keywords_node, metadata={"type": "agent", "llm_cfg": "config/extract_keywords_llm_cfg.json"})
builder.add_node("sync_to_feishu", sync_to_feishu_node)
builder.add_node("send_email", send_email_node)

# 设置入口点
builder.set_entry_point("fetch_news")

# 添加边 - 线性工作流
builder.add_edge("fetch_news", "filter_news")
builder.add_edge("filter_news", "extract_keywords")
builder.add_edge("extract_keywords", "sync_to_feishu")
builder.add_edge("sync_to_feishu", "send_email")
builder.add_edge("send_email", END)

# 编译图
main_graph = builder.compile()
