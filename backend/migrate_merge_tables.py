"""
数据库迁移：合并 calendar_todos → todos
用法：python backend/migrate_merge_tables.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from models.todo import Todo
from datetime import date, datetime

with app.app_context():
    inspector = db.inspect(db.engine)
    if 'calendar_todos' not in inspector.get_table_names():
        print("calendar_todos 表不存在，跳过迁移")
        sys.exit(0)

    conn = db.engine.raw_connection()
    c = conn.cursor()

    # 0. 先添加新字段到 todos 表
    try:
        c.execute("ALTER TABLE todos ADD COLUMN date DATE")
        print("添加 date 列")
    except:
        print("date 列已存在")
    try:
        c.execute("ALTER TABLE todos ADD COLUMN reminder_at DATETIME")
        print("添加 reminder_at 列")
    except:
        print("reminder_at 列已存在")
    try:
        c.execute("ALTER TABLE todos ADD COLUMN reminded BOOLEAN DEFAULT 0")
        print("添加 reminded 列")
    except:
        print("reminded 列已存在")
    try:
        c.execute("ALTER TABLE todos ADD COLUMN updated_at DATETIME")
        print("添加 updated_at 列")
    except:
        print("updated_at 列已存在")

    # 1. 为已有 source=1 的 todos 设置 date（从 calendar_todos 关联）
    c.execute("""
        UPDATE todos SET date = (
            SELECT ct.date FROM calendar_todos ct
            WHERE ct.id = todos.source_id
        )
        WHERE source = 1 AND source_id IS NOT NULL
    """)
    updated = c.rowcount
    print(f"更新 {updated} 条现有 todos 的 date")

    # 2. 插入 calendar_todos 中没有对应 source=1 的记录进 todos
    c.execute("""
        INSERT INTO todos (user_id, title, done, sort_order, color,
                           reminder_at, reminded, created_at, date)
        SELECT ct.user_id, ct.title, ct.done, ct.sort_order, ct.color,
               ct.reminder_at, ct.reminded, ct.created_at, ct.date
        FROM calendar_todos ct
        LEFT JOIN todos t ON t.source_id = ct.id AND t.source = 1
        WHERE t.id IS NULL
    """)
    inserted = c.rowcount
    print(f"插入 {inserted} 条新记录（从 calendar_todos）")

    # 3. 清理 source/source_id 字段（SQLite 不直接支持 DROP COLUMN，新建表）
    c.execute("""
        CREATE TABLE todos_new (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title VARCHAR(200) NOT NULL,
            done BOOLEAN DEFAULT 0,
            priority INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            color VARCHAR(7),
            label VARCHAR(50),
            date DATE,
            reminder_at DATETIME,
            reminded BOOLEAN DEFAULT 0,
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # 4. 复制数据（去掉 source/source_id/due_date，新增 reminder_at/reminded/date/updated_at）
    c.execute("""
        INSERT INTO todos_new (id, user_id, title, done, priority, sort_order,
                               color, label, date, reminder_at, reminded, created_at, updated_at)
        SELECT id, user_id, title,
               CASE WHEN done IS NULL THEN 0 ELSE done END,
               COALESCE(priority, 0), COALESCE(sort_order, 0),
               color, label, date, reminder_at,
               CASE WHEN reminded IS NULL THEN 0 ELSE reminded END,
               created_at, created_at
        FROM todos
        ORDER BY id
    """)
    migrated = c.rowcount
    print(f"迁移 {migrated} 条记录到新结构")

    # 5. 切换表
    c.execute("DROP TABLE todos")
    c.execute("ALTER TABLE todos_new RENAME TO todos")

    # 6. 重建索引
    c.execute("CREATE INDEX ix_todos_user_id ON todos(user_id)")
    c.execute("CREATE INDEX ix_todos_date ON todos(date)")

    # 7. 删除旧表
    c.execute("DROP TABLE IF EXISTS calendar_todos")

    conn.commit()
    conn.close()

    # 验证
    total = Todo.query.count()
    with_date = Todo.query.filter(Todo.date.isnot(None)).count()
    without_date = Todo.query.filter(Todo.date.is_(None)).count()
    print(f"\n验证完成：共 {total} 条，{with_date} 条有日期，{without_date} 条无日期")
    print("迁移成功！")
