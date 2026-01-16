"""
清空新闻历史记录数据库
"""
import sys
import os

# 添加项目路径到 sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.storage.database.db import get_session
from src.storage.database.news_history_manager import NewsHistoryManager


def clear_news_history():
    """清空所有新闻历史记录"""
    print("=" * 60)
    print("开始清空新闻历史记录数据库")
    print("=" * 60)

    db = get_session()
    try:
        mgr = NewsHistoryManager()

        # 获取当前记录数
        total_count = mgr.get_total_count(db)
        print(f"当前历史记录数: {total_count}")

        if total_count == 0:
            print("数据库为空，无需清空")
            return

        # 确认是否删除
        confirm = input(f"确认删除所有 {total_count} 条历史记录？(yes/no): ")
        if confirm.lower() != 'yes':
            print("取消操作")
            return

        # 清空所有记录
        deleted_count = mgr.clear_all(db)
        print(f"✅ 成功删除 {deleted_count} 条历史记录")

    except Exception as e:
        print(f"❌ 清空失败: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clear_news_history()
