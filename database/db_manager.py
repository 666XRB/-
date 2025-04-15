import os
import sqlite3
from models.knowledge_card import KnowledgeCard
import datetime
from datetime import timedelta

class DBManager:
    def __init__(self):
        # 获取用户应用数据目录
        appdata_dir = os.getenv('APPDATA')
        if not appdata_dir:
            appdata_dir = os.path.expanduser('~')
        
        # 创建应用专属目录
        self.app_dir = os.path.join(appdata_dir, 'KnowledgeBaseApp')
        os.makedirs(self.app_dir, exist_ok=True)
        
        # 设置数据库路径
        self.db_path = os.path.join(self.app_dir, 'knowledge_base.db')
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

    def clear_all_cards(self):
        """清空所有卡片"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM knowledge_cards")
        self.conn.commit()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT NOT NULL,
                content TEXT NOT NULL,
                mnemonic TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                query_count INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    def add_card(self, card: KnowledgeCard):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO knowledge_cards (module, content, mnemonic, created_at, updated_at, query_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (card.module, card.content, card.mnemonic, card.created_at, card.updated_at, card.query_count))
        self.conn.commit()
        return cursor.lastrowid

    def get_all_cards(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM knowledge_cards")
        rows = cursor.fetchall()
        return [KnowledgeCard(*row) for row in rows]

    def get_all_cards_sorted_by_views(self):
        """获取所有卡片并按查询次数降序排序"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM knowledge_cards ORDER BY query_count DESC")
        rows = cursor.fetchall()
        return [KnowledgeCard(*row) for row in rows]

    def search_cards(self, query):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM knowledge_cards 
            WHERE module LIKE ? 
            OR content LIKE ? 
            OR mnemonic LIKE ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        rows = cursor.fetchall()
        return [KnowledgeCard(*row) for row in rows]

    def delete_card(self, card_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM knowledge_cards WHERE id = ?", (card_id,))
        self.conn.commit()

    def update_card(self, card: KnowledgeCard):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE knowledge_cards 
            SET module = ?, content = ?, mnemonic = ?, 
                updated_at = ?, query_count = ? 
            WHERE id = ?
        """, (card.module, card.content, card.mnemonic, 
              card.updated_at, card.query_count, card.id))
        self.conn.commit()

    def increment_query_count(self, card_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE knowledge_cards 
            SET query_count = query_count + 1 
            WHERE id = ?
        """, (card_id,))
        self.conn.commit()

    def get_card_by_id(self, card_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM knowledge_cards WHERE id = ?", (card_id,))
        row = cursor.fetchone()
        if row:
            return KnowledgeCard(*row)
        return None

    def get_card_id_by_content(self, content):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM knowledge_cards WHERE content = ?", (content,))
        row = cursor.fetchone()
        if row:
            return row[0]
        return None

    def get_today_cards(self):
        """获取今天创建的卡片(基于created_at字段)"""
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM knowledge_cards 
            WHERE created_at >= ?
        """, (today.strftime("%Y-%m-%d %H:%M:%S"),))
        rows = cursor.fetchall()
        return [KnowledgeCard(*row) for row in rows]
    
    def get_week_cards(self):
        """获取本周创建的卡片(基于created_at字段)"""
        week_start = datetime.datetime.now() - datetime.timedelta(days=datetime.datetime.now().weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM knowledge_cards 
            WHERE created_at >= ?
        """, (week_start.strftime("%Y-%m-%d %H:%M:%S"),))
        rows = cursor.fetchall()
        return [KnowledgeCard(*row) for row in rows]
    
    def get_cards_by_date(self, date):
        """获取指定日期创建的卡片(基于created_at字段)"""
        start = datetime.datetime.combine(date, datetime.time.min)
        end = datetime.datetime.combine(date, datetime.time.max)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM knowledge_cards 
            WHERE created_at BETWEEN ? AND ?
        """, (start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S")))
        rows = cursor.fetchall()
        return [KnowledgeCard(*row) for row in rows]