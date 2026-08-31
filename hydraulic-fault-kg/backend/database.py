"""
数据库连接管理 - 基于 sqlite3 标准库（不使用 SQLAlchemy）

管理 kg.db 的连接、表创建与基础操作。
所有 16 张表使用中文列名，遵循项目中文规范。
"""
import sqlite3
import os
import threading
from typing import Optional, List, Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "kg.db")

# 线程本地存储：每个线程持有独立连接
_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """获取当前线程的数据库连接（线程安全）"""
    conn = getattr(_local, "connection", None)
    if conn is None:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.connection = conn
    return conn


def close_connection():
    """关闭当前线程的数据库连接"""
    conn = getattr(_local, "connection", None)
    if conn is not None:
        conn.close()
        _local.connection = None


def get_db():
    """获取数据库连接上下文管理器（每次调用获取同一线程连接）"""
    return get_connection()


def execute_sql(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    """执行 SQL 语句并返回游标"""
    conn = get_connection()
    cursor = conn.execute(sql, params)
    conn.commit()
    return cursor


def execute_many(sql: str, params_list: List[tuple]) -> sqlite3.Cursor:
    """批量执行 SQL 语句"""
    conn = get_connection()
    cursor = conn.executemany(sql, params_list)
    conn.commit()
    return cursor


def fetch_all(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """查询所有行，返回字典列表"""
    conn = get_connection()
    cursor = conn.execute(sql, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def fetch_one(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """查询单行，返回字典或 None"""
    conn = get_connection()
    cursor = conn.execute(sql, params)
    row = cursor.fetchone()
    return dict(row) if row else None


def init_db():
    """创建所有数据库表（共 16 张）"""
    conn = get_connection()
    cursor = conn.cursor()

    # ============================================================
    # 1. sources — 公开资料来源
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id       TEXT UNIQUE NOT NULL,
            来源类型         TEXT NOT NULL,
            标题            TEXT NOT NULL,
            作者            TEXT,
            年份            INTEGER,
            出版方          TEXT,
            文件路径         TEXT,
            文档类型         TEXT,
            公开说明         TEXT,
            资料描述         TEXT,
            录入时间         TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # ============================================================
    # 2. paragraphs — 解析后的段落
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paragraphs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            paragraph_id    TEXT UNIQUE NOT NULL,
            source_id       TEXT NOT NULL,
            段落序号         INTEGER NOT NULL,
            段落内容         TEXT NOT NULL,
            字符数           INTEGER,
            解析时间         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (source_id) REFERENCES sources(source_id)
        )
    """)

    # ============================================================
    # 3. filtered_paragraphs — 清洗和领域过滤后的段落
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS filtered_paragraphs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            filtered_id     TEXT UNIQUE NOT NULL,
            paragraph_id    TEXT NOT NULL,
            source_id       TEXT NOT NULL,
            过滤后内容       TEXT NOT NULL,
            相关度评分       REAL,
            过滤原因         TEXT,
            过滤时间         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (paragraph_id) REFERENCES paragraphs(paragraph_id),
            FOREIGN KEY (source_id) REFERENCES sources(source_id)
        )
    """)

    # ============================================================
    # 4. events — 抽取事件
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id        TEXT UNIQUE NOT NULL,
            filtered_id     TEXT,
            事件类型         TEXT NOT NULL,
            事件触发词       TEXT,
            事件描述         TEXT NOT NULL,
            论元JSON        TEXT,
            发生时间         TEXT,
            录入时间         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            置信度          REAL,
            FOREIGN KEY (filtered_id) REFERENCES filtered_paragraphs(filtered_id)
        )
    """)

    # ============================================================
    # 5. evidence — 证据 span
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id     TEXT UNIQUE NOT NULL,
            event_id        TEXT NOT NULL,
            filtered_id     TEXT,
            来源文件         TEXT,
            原文片段         TEXT NOT NULL,
            起始位置         INTEGER,
            结束位置         INTEGER,
            锚定时间         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (event_id) REFERENCES events(event_id),
            FOREIGN KEY (filtered_id) REFERENCES filtered_paragraphs(filtered_id)
        )
    """)

    # ============================================================
    # 6. mechanism_templates — 机理模板
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mechanism_templates (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id     TEXT UNIQUE NOT NULL,
            模板名称         TEXT NOT NULL,
            模板描述         TEXT,
            前件条件JSON    TEXT,
            后件结果JSON    TEXT,
            物理约束         TEXT,
            适用事件类型     TEXT,
            创建时间         TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # ============================================================
    # 7. event_relations — 事件关系
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_relations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            relation_id     TEXT UNIQUE NOT NULL,
            source_event_id TEXT NOT NULL,
            target_event_id TEXT NOT NULL,
            关系类型         TEXT NOT NULL,
            关系描述         TEXT,
            置信度          REAL,
            FOREIGN KEY (source_event_id) REFERENCES events(event_id),
            FOREIGN KEY (target_event_id) REFERENCES events(event_id)
        )
    """)

    # ============================================================
    # 8. graph_nodes — 图谱节点
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS graph_nodes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id         TEXT UNIQUE NOT NULL,
            节点名称         TEXT NOT NULL,
            节点类型         TEXT NOT NULL,
            节点属性JSON    TEXT,
            来源event_id    TEXT,
            创建时间         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (来源event_id) REFERENCES events(event_id)
        )
    """)

    # ============================================================
    # 9. graph_links — 图谱边
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS graph_links (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id         TEXT UNIQUE NOT NULL,
            source_node_id  TEXT NOT NULL,
            target_node_id  TEXT NOT NULL,
            边类型          TEXT NOT NULL,
            边属性JSON      TEXT,
            来源relation_id TEXT,
            FOREIGN KEY (source_node_id) REFERENCES graph_nodes(node_id),
            FOREIGN KEY (target_node_id) REFERENCES graph_nodes(node_id),
            FOREIGN KEY (来源relation_id) REFERENCES event_relations(relation_id)
        )
    """)

    # ============================================================
    # 10. version_logs — 双时态和版本日志
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS version_logs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            log_id          TEXT UNIQUE NOT NULL,
            实体类型         TEXT NOT NULL,
            实体ID          TEXT NOT NULL,
            操作类型         TEXT NOT NULL,
            旧值JSON        TEXT,
            新值JSON        TEXT,
            操作时间         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            操作说明         TEXT
        )
    """)

    # ============================================================
    # 11. qa_sessions — 大模型问答会话
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa_sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT UNIQUE NOT NULL,
            会话标题         TEXT,
            创建时间         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            更新时间         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            状态            TEXT NOT NULL DEFAULT '进行中'
        )
    """)

    # ============================================================
    # 12. qa_records — 问答记录
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id       TEXT UNIQUE NOT NULL,
            session_id      TEXT NOT NULL,
            用户问题         TEXT NOT NULL,
            模型回答         TEXT NOT NULL,
            检索证据JSON    TEXT,
            引用来源JSON    TEXT,
            创建时间         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (session_id) REFERENCES qa_sessions(session_id)
        )
    """)

    # ============================================================
    # 13. maintenance_rules — 维修推荐规则
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_rules (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id         TEXT UNIQUE NOT NULL,
            规则名称         TEXT NOT NULL,
            故障模式         TEXT NOT NULL,
            适用条件         TEXT,
            维修方案         TEXT NOT NULL,
            所需工具         TEXT,
            所需材料         TEXT,
            操作步骤JSON    TEXT,
            参考来源         TEXT
        )
    """)

    # ============================================================
    # 14. metrics — 构建质量评价指标
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_id       TEXT UNIQUE NOT NULL,
            指标名称         TEXT NOT NULL,
            指标值          REAL,
            指标单位         TEXT,
            评估时间         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            说明            TEXT
        )
    """)

    # ============================================================
    # 15. uploaded_files — 可选上传文件信息
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id         TEXT UNIQUE NOT NULL,
            文件名          TEXT NOT NULL,
            文件类型         TEXT NOT NULL,
            文件大小         INTEGER,
            上传时间         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            处理状态         TEXT NOT NULL DEFAULT '待处理',
            存储路径         TEXT
        )
    """)

    # ============================================================
    # 16. analysis_results — 可选上传文件后的分析结果
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id       TEXT UNIQUE NOT NULL,
            file_id         TEXT NOT NULL,
            分析类型         TEXT NOT NULL,
            分析结果JSON    TEXT,
            是否加入图谱     INTEGER DEFAULT 0,
            分析时间         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (file_id) REFERENCES uploaded_files(file_id)
        )
    """)

    conn.commit()
    print(f"[OK] 数据库初始化完成: {DB_PATH}")
    print(f"     已创建 16 张数据表")


def get_table_count(table_name: str) -> int:
    """获取表的行数"""
    row = fetch_one(f"SELECT COUNT(*) as cnt FROM {table_name}")
    return row["cnt"] if row else 0


def get_all_tables() -> List[str]:
    """获取所有表名"""
    rows = fetch_all("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [r["name"] for r in rows]
