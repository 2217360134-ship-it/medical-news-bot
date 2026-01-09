from typing import List, Optional
from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    """新闻数据模型"""
    title: str = Field(..., description="新闻标题")
    date: str = Field(..., description="新闻发布日期")
    url: str = Field(..., description="新闻链接")
    summary: str = Field(..., description="新闻摘要")
    source: str = Field(default="", description="新闻来源")
    region: str = Field(default="", description="地区")
    keywords: List[str] = Field(default=[], description="关键词列表")


class GlobalState(BaseModel):
    """全局状态定义"""
    # 邮件信息（输入为字符串，处理为列表）
    emails: str = Field(default="", description="接收邮件的邮箱地址，多个邮箱用逗号分隔")
    emails_list: List[str] = Field(default=[], description="分割后的邮箱地址列表")
    
    # 表格文件信息
    table_filepath: str = Field(default="", description="Excel表格文件路径")
    table_filename: str = Field(default="", description="Excel表格文件名")
    
    # 新闻数据流
    raw_news_list: List[NewsItem] = Field(default=[], description="从今日头条获取的原始新闻列表")
    summarized_news_list: List[NewsItem] = Field(default=[], description="生成摘要后的新闻列表")
    filtered_news_list: List[NewsItem] = Field(default=[], description="过滤后的新闻列表（近3个月内）")
    enriched_news_list: List[NewsItem] = Field(default=[], description="提取关键词后的新闻列表")
    
    # 结果
    synced_count: int = Field(default=0, description="创建的新闻记录数")
    email_sent: bool = Field(default=False, description="邮件是否发送成功")
    email_message: str = Field(default="", description="邮件发送结果消息")


class GraphInput(BaseModel):
    """工作流的输入"""
    emails: str = Field(..., description="接收邮件的邮箱地址，多个邮箱用逗号分隔，例如：user1@example.com,user2@example.com")


class GraphOutput(BaseModel):
    """工作流的输出"""
    synced_count: int = Field(..., description="成功同步到飞书的新闻数量")
    email_sent: bool = Field(default=False, description="邮件是否发送成功")
    message: str = Field(..., description="执行结果消息")


class FetchNewsInput(BaseModel):
    """新闻获取节点的输入"""
    emails: str = Field(..., description="接收邮件的邮箱地址，多个邮箱用逗号分隔")


class FetchNewsOutput(BaseModel):
    """新闻获取节点的输出"""
    news_list: List[NewsItem] = Field(..., description="获取到的新闻列表")
    emails_list: List[str] = Field(..., description="分割后的邮箱地址列表")


class GenerateSummaryInput(BaseModel):
    """生成摘要节点的输入"""
    filtered_news_list: List[NewsItem] = Field(..., description="需要生成摘要的新闻列表")


class GenerateSummaryOutput(BaseModel):
    """生成摘要节点的输出"""
    summarized_news_list: List[NewsItem] = Field(..., description="生成摘要后的新闻列表")


class ExtractDateInput(BaseModel):
    """日期提取节点的输入"""
    news_list: List[NewsItem] = Field(..., description="需要提取日期的新闻列表")


class ExtractDateOutput(BaseModel):
    """日期提取节点的输出"""
    filtered_news_list: List[NewsItem] = Field(..., description="过滤后的新闻列表（近3个月内）")


class ExtractKeywordsInput(BaseModel):
    """关键词提取节点的输入"""
    summarized_news_list: List[NewsItem] = Field(..., description="需要提取关键词的新闻列表")


class ExtractKeywordsOutput(BaseModel):
    """关键词提取节点的输出"""
    enriched_news_list: List[NewsItem] = Field(..., description="提取关键词后的新闻列表")


class CreateTableInput(BaseModel):
    """创建表格节点的输入"""
    enriched_news_list: List[NewsItem] = Field(..., description="需要创建表格的新闻列表")


class CreateTableOutput(BaseModel):
    """创建表格节点的输出"""
    enriched_news_list: List[NewsItem] = Field(..., description="新闻列表")
    synced_count: int = Field(..., description="创建的记录数")
    table_filepath: str = Field(..., description="表格文件路径")
    table_filename: str = Field(..., description="表格文件名")


class SendEmailInput(BaseModel):
    """发送邮件节点的输入"""
    emails_list: List[str] = Field(..., description="分割后的邮箱地址列表")
    enriched_news_list: List[NewsItem] = Field(..., description="新闻列表")
    table_filepath: str = Field(..., description="表格文件路径")
    table_filename: str = Field(..., description="表格文件名")


class SendEmailOutput(BaseModel):
    """发送邮件节点的输出"""
    email_sent: bool = Field(..., description="邮件是否发送成功")
    email_message: str = Field(..., description="邮件发送结果消息")
