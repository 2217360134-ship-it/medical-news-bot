from langgraph.graph import StateGraph, END
from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput
)
from graphs.node import (
    fetch_news_node,
    filter_news_node,
    generate_summary_node,
    extract_keywords_node,
    create_table_node,
    send_email_node
)

# 创建状态图, 一定指定工作流的入参和出参
builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

# 添加节点
builder.add_node("fetch_news", fetch_news_node)
builder.add_node("filter_news", filter_news_node)
builder.add_node("generate_summary", generate_summary_node, metadata={"type": "agent", "llm_cfg": "config/generate_summary_llm_cfg.json"})
builder.add_node("extract_keywords", extract_keywords_node, metadata={"type": "agent", "llm_cfg": "config/extract_keywords_llm_cfg.json"})
builder.add_node("create_table", create_table_node)
builder.add_node("send_email", send_email_node)

# 设置入口点
builder.set_entry_point("fetch_news")

# 添加边 - 线性工作流
builder.add_edge("fetch_news", "filter_news")
builder.add_edge("filter_news", "generate_summary")
builder.add_edge("generate_summary", "extract_keywords")
builder.add_edge("extract_keywords", "create_table")
builder.add_edge("create_table", "send_email")
builder.add_edge("send_email", END)

# 编译图
main_graph = builder.compile()
