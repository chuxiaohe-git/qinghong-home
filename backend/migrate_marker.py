"""迁移脚本：为 bookmarks 表添加 marker 列（幂等，可重复执行）"""
import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(__file__), 'instance')
DB_FILES = [f for f in os.listdir(DB_DIR) if f.endswith('.db')]

for db_name in DB_FILES:
    db_path = os.path.join(DB_DIR, db_name)
    print(f"📁 {db_name}...", end=' ')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查 marker 列是否存在
    cursor.execute("PRAGMA table_info(bookmarks)")
    cols = [row[1] for row in cursor.fetchall()]
    
    if 'marker' in cols:
        print("✅ 已存在，跳过")
    else:
        cursor.execute("ALTER TABLE bookmarks ADD COLUMN marker VARCHAR(20)")
        conn.commit()
        print("✅ 已添加 marker 列")
    
    conn.close()
