from sqlalchemy import MetaData
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text, JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional
import datetime

metadata = MetaData()

class Base(DeclarativeBase):
    pass

class NewsHistory(Base):
    """新闻历史记录表 - 用于存储已发送的新闻，避免重复"""
    __tablename__ = "news_history"
    
    id = Column(Integer, primary_key=True, comment="主键ID")
    title = Column(String(512), nullable=False, comment="新闻标题")
    url = Column(String(1024), unique=True, nullable=False, comment="新闻链接（唯一索引）")
    date = Column(String(32), nullable=True, comment="新闻发布日期")
    source = Column(String(128), nullable=True, comment="新闻来源")
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="发送时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="记录创建时间")
    
    # 索引
    __table_args__ = (
        Index("ix_news_history_url", "url"),
        Index("ix_news_history_sent_at", "sent_at"),
    )

