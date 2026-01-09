from typing import List, Optional
from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    """新闻数据模型"""
    title: str = Field(..., description="新闻标题")
    date: str = Field(..., description="新闻发布日期")
    url: str = Field(..., description="新闻链接")
    summary: str = Field(..., description="新闻摘要")
    keywords: List[str] = Field(default=[], description="关键词列表")


class GlobalState(BaseModel):
    """全局状态定义"""
    # 飞书多维表格信息
    app_token: str = Field(default="", description="飞书多维表格App Token")
    table_id: str = Field(default="", description="飞书数据表ID")
    
    # 邮件信息
    email: str = Field(default="", description="接收邮件的邮箱地址")
    
    # 新闻数据流
    raw_news_list: List[NewsItem] = Field(default=[], description="从今日头条获取的原始新闻列表")
    filtered_news_list: List[NewsItem] = Field(default=[], description="筛选后的医疗器械和医美相关新闻")
    enriched_news_list: List[NewsItem] = Field(default=[], description="提取关键词后的新闻列表")
    
    # 结果
    sync_result: dict = Field(default={}, description="同步到飞书的结果")
    synced_count: int = Field(default=0, description="成功同步的记录数")
    email_sent: bool = Field(default=False, description="邮件是否发送成功")
    email_message: str = Field(default="", description="邮件发送结果消息")


class GraphInput(BaseModel):
    """工作流的输入"""
    app_token: str = Field(default="", description="飞书多维表格App Token（可选，如不提供则创建新Base）")
    table_id: str = Field(default="", description="飞书数据表ID（可选，如不提供则创建新表）")
    email: str = Field(..., description="接收邮件的邮箱地址")


class GraphOutput(BaseModel):
    """工作流的输出"""
    synced_count: int = Field(..., description="成功同步到飞书的新闻数量")
    email_sent: bool = Field(default=False, description="邮件是否发送成功")
    message: str = Field(..., description="执行结果消息")


class FetchNewsInput(BaseModel):
    """新闻获取节点的输入"""
    pass


class FetchNewsOutput(BaseModel):
    """新闻获取节点的输出"""
    news_list: List[NewsItem] = Field(..., description="获取到的新闻列表")


class FilterNewsInput(BaseModel):
    """新闻筛选节点的输入"""
    news_list: List[NewsItem] = Field(..., description="待筛选的新闻列表")


class FilterNewsOutput(BaseModel):
    """新闻筛选节点的输出"""
    filtered_news_list: List[NewsItem] = Field(..., description="筛选后的新闻列表")


class ExtractKeywordsInput(BaseModel):
    """关键词提取节点的输入"""
    news_list: List[NewsItem] = Field(..., description="需要提取关键词的新闻列表")


class ExtractKeywordsOutput(BaseModel):
    """关键词提取节点的输出"""
    enriched_news_list: List[NewsItem] = Field(..., description="提取关键词后的新闻列表")


class SyncToFeishuInput(BaseModel):
    """飞书多维表格同步节点的输入"""
    news_list: List[NewsItem] = Field(..., description="需要同步的新闻列表")
    app_token: str = Field(default="", description="飞书多维表格App Token")
    table_id: str = Field(default="", description="飞书数据表ID")


class SyncToFeishuOutput(BaseModel):
    """飞书多维表格同步节点的输出"""
    news_list: List[NewsItem] = Field(..., description="同步的新闻列表")
    synced_count: int = Field(..., description="成功同步的记录数")
    app_token: str = Field(..., description="使用的App Token")
    table_id: str = Field(..., description="使用的数据表ID")


class SendEmailInput(BaseModel):
    """发送邮件节点的输入"""
    email: str = Field(..., description="接收邮件的邮箱地址")
    news_list: List[NewsItem] = Field(..., description="新闻列表")
    synced_count: int = Field(..., description="同步到飞书的新闻数量")


class SendEmailOutput(BaseModel):
    """发送邮件节点的输出"""
    email_sent: bool = Field(..., description="邮件是否发送成功")
    email_message: str = Field(..., description="邮件发送结果消息")
