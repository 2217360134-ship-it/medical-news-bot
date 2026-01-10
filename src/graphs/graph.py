from langgraph.graph import StateGraph, END
from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput
)
from graphs.node import (
    split_emails_node,
    fetch_news_node,
    deduplicate_news_node,
    extract_date_node,
    extract_news_info_node,
    create_table_node,
    send_email_node,
    save_news_history_node
)

# 创建状态图, 一定指定工作流的入参和出参
builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

# 添加节点（为所有节点添加metadata以便预览正确显示）
builder.add_node("split_emails", split_emails_node, metadata={"type": "normal"})
builder.add_node("fetch_news", fetch_news_node, metadata={"type": "normal"})
builder.add_node("deduplicate_news", deduplicate_news_node, metadata={"type": "normal"})
builder.add_node("extract_date", extract_date_node, metadata={"type": "normal"})
builder.add_node("extract_news_info", extract_news_info_node, metadata={"type": "agent", "llm_cfg": "config/extract_news_info_llm_cfg.json"})
builder.add_node("create_table", create_table_node, metadata={"type": "normal"})
builder.add_node("send_email", send_email_node, metadata={"type": "normal"})
builder.add_node("save_news_history", save_news_history_node, metadata={"type": "normal"})

# 设置入口点
builder.set_entry_point("split_emails")

# 添加边 - 线性工作流架构
# split_emails -> (无依赖，只是设置 emails_list)
builder.add_edge("split_emails", "fetch_news")

# fetch_news -> deduplicate_news（去重历史新闻）
builder.add_edge("fetch_news", "deduplicate_news")

# deduplicate_news -> extract_date（提取日期）
builder.add_edge("deduplicate_news", "extract_date")

# extract_date -> extract_news_info（提取新闻信息，包括摘要、关键词、来源、地区）
builder.add_edge("extract_date", "extract_news_info")

# extract_news_info -> create_table（创建Excel表格）
builder.add_edge("extract_news_info", "create_table")

# create_table -> send_email（发送邮件）
builder.add_edge("create_table", "send_email")

# send_email -> save_news_history（保存历史记录） -> END
builder.add_edge("send_email", "save_news_history")
builder.add_edge("save_news_history", END)

# 编译图
main_graph = builder.compile()
