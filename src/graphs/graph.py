from langgraph.graph import StateGraph, END
from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput
)
from graphs.node import (
    fetch_news_node,
    deduplicate_news_node,
    generate_summary_node,
    extract_date_node,
    extract_keywords_node,
    create_table_node,
    send_email_node,
    merge_news_info_node,
    save_news_history_node
)

# 创建状态图, 一定指定工作流的入参和出参
builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

# 添加节点
builder.add_node("fetch_news", fetch_news_node)
builder.add_node("deduplicate_news", deduplicate_news_node)
builder.add_node("generate_summary", generate_summary_node, metadata={"type": "agent", "llm_cfg": "config/generate_summary_llm_cfg.json"})
builder.add_node("extract_date", extract_date_node, metadata={"type": "agent", "llm_cfg": "config/extract_date_llm_cfg.json"})
builder.add_node("extract_keywords", extract_keywords_node, metadata={"type": "agent", "llm_cfg": "config/extract_keywords_llm_cfg.json"})
builder.add_node("merge_news_info", merge_news_info_node)
builder.add_node("create_table", create_table_node)
builder.add_node("send_email", send_email_node)
builder.add_node("save_news_history", save_news_history_node)

# 设置入口点
builder.set_entry_point("fetch_news")

# 添加边 - 并行工作流架构
# fetch_news -> deduplicate_news（去重历史新闻）
builder.add_edge("fetch_news", "deduplicate_news")

# deduplicate_news -> extract_date（提取日期）
builder.add_edge("deduplicate_news", "extract_date")

# extract_date 同时传给 generate_summary 和 extract_keywords（并行执行）
builder.add_edge("extract_date", "generate_summary")
builder.add_edge("extract_date", "extract_keywords")

# 并行分支汇聚：等待 generate_summary 和 extract_keywords 都完成后，执行 merge_news_info
builder.add_edge(["generate_summary", "extract_keywords"], "merge_news_info")

# 后续流程
builder.add_edge("merge_news_info", "create_table")
builder.add_edge("create_table", "send_email")

# send_email -> save_news_history（保存历史记录） -> END
builder.add_edge("send_email", "save_news_history")
builder.add_edge("save_news_history", END)

# 编译图
main_graph = builder.compile()
