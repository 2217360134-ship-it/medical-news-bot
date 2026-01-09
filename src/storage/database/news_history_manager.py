from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from storage.database.shared.model import NewsHistory


class NewsHistoryCreate(BaseModel):
    """创建新闻历史记录的输入模型"""
    title: str = Field(..., description="新闻标题")
    url: str = Field(..., description="新闻链接")
    date: str = Field(default="", description="新闻发布日期")
    source: str = Field(default="", description="新闻来源")


class NewsHistoryManager:
    """新闻历史记录管理器 - 用于查询和管理已发送的新闻记录"""

    def create_news_history(self, db: Session, news_in: NewsHistoryCreate) -> NewsHistory:
        """
        创建新闻历史记录
        """
        news_data = news_in.model_dump()
        db_news = NewsHistory(**news_data)
        db.add(db_news)
        try:
            db.commit()
            db.refresh(db_news)
            return db_news
        except Exception as e:
            db.rollback()
            raise Exception(f"创建新闻历史记录失败: {str(e)}")

    def batch_create_news_history(self, db: Session, news_list: List[NewsHistoryCreate]) -> List[NewsHistory]:
        """
        批量创建新闻历史记录
        """
        db_news_list = []
        for news_in in news_list:
            news_data = news_in.model_dump()
            db_news = NewsHistory(**news_data)
            db.add(db_news)
            db_news_list.append(db_news)
        
        try:
            db.commit()
            for db_news in db_news_list:
                db.refresh(db_news)
            return db_news_list
        except Exception as e:
            db.rollback()
            raise Exception(f"批量创建新闻历史记录失败: {str(e)}")

    def get_all_urls(self, db: Session) -> set:
        """
        获取所有历史新闻的URL集合
        返回: URL的集合
        """
        news_list = db.query(NewsHistory.url).all()
        return {news[0] for news in news_list}

    def get_all_titles(self, db: Session) -> set:
        """
        获取所有历史新闻的标题集合
        返回: 标题的集合
        """
        news_list = db.query(NewsHistory.title).all()
        return {news[0] for news in news_list}

    def exists_by_url(self, db: Session, url: str) -> bool:
        """
        检查URL是否已存在
        """
        return db.query(NewsHistory).filter(NewsHistory.url == url).first() is not None

    def exists_by_title(self, db: Session, title: str) -> bool:
        """
        检查标题是否已存在
        """
        return db.query(NewsHistory).filter(NewsHistory.title == title).first() is not None

    def get_news_by_date_range(self, db: Session, start_date: str, end_date: str) -> List[NewsHistory]:
        """
        按日期范围查询新闻记录
        """
        return db.query(NewsHistory).filter(
            and_(
                NewsHistory.date >= start_date,
                NewsHistory.date <= end_date
            )
        ).all()

    def delete_old_news(self, db: Session, days: int = 180) -> int:
        """
        删除指定天数之前的旧新闻记录（用于清理历史数据）
        默认删除180天之前的记录
        """
        from datetime import timedelta
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        deleted_count = db.query(NewsHistory).filter(
            NewsHistory.sent_at < cutoff_date
        ).delete(synchronize_session=False)
        
        db.commit()
        return deleted_count

    def get_total_count(self, db: Session) -> int:
        """
        获取历史新闻总数
        """
        return db.query(NewsHistory).count()
