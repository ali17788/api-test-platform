# -*- coding: utf-8 -*-
"""SQLite 数据持久层：建库、建表、种子数据、连接助手"""
import sqlite3
import hashlib
import os
import threading

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "platform.db")
_local = threading.local()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  role TEXT DEFAULT 'admin',
  nickname TEXT DEFAULT '',
  status TEXT DEFAULT 'active',
  role_id INTEGER,
  menu_keys TEXT DEFAULT '[]',
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS roles(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  code TEXT UNIQUE NOT NULL,
  description TEXT DEFAULT '',
  menu_keys TEXT DEFAULT '[]',
  is_system INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS tokens(
  token TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL,
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS projects(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT DEFAULT '',
  owner TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS environments(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  base_url TEXT NOT NULL,
  headers TEXT DEFAULT '{}',
  timeout INTEGER DEFAULT 10,
  retry INTEGER DEFAULT 0,
  is_default INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS apis(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  method TEXT DEFAULT 'GET',
  path TEXT DEFAULT '/',
  module TEXT DEFAULT '默认模块',
  headers TEXT DEFAULT '{}',
  query_params TEXT DEFAULT '{}',
  body TEXT DEFAULT '{}',
  response_schema TEXT DEFAULT '{}',
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS cases(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  api_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  case_type TEXT DEFAULT '正向',
  priority TEXT DEFAULT 'P1',
  steps TEXT DEFAULT '',
  request_data TEXT DEFAULT '{}',
  expected TEXT DEFAULT '{}',
  source TEXT DEFAULT 'AI',
  last_status TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS tasks(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  env_id INTEGER,
  env_name TEXT DEFAULT '',
  case_ids TEXT DEFAULT '[]',
  status TEXT DEFAULT 'pending',
  total INTEGER DEFAULT 0,
  executed INTEGER DEFAULT 0,
  passed INTEGER DEFAULT 0,
  failed INTEGER DEFAULT 0,
  skipped INTEGER DEFAULT 0,
  duration REAL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now','localtime')),
  finished_at TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS task_logs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id INTEGER NOT NULL,
  level TEXT DEFAULT 'INFO',
  message TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS case_results(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id INTEGER NOT NULL,
  case_id INTEGER NOT NULL,
  case_name TEXT DEFAULT '',
  api_name TEXT DEFAULT '',
  module TEXT DEFAULT '',
  case_type TEXT DEFAULT '',
  status TEXT DEFAULT '',
  request_info TEXT DEFAULT '{}',
  response_info TEXT DEFAULT '{}',
  assertions TEXT DEFAULT '[]',
  fail_reason TEXT DEFAULT '',
  duration REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS ai_config(
  id INTEGER PRIMARY KEY CHECK (id = 1),
  model TEXT DEFAULT 'deepseek-chat',
  api_key TEXT DEFAULT '',
  base_url TEXT DEFAULT 'https://api.deepseek.com/v1',
  timeout INTEGER DEFAULT 60
);
CREATE TABLE IF NOT EXISTS op_logs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT DEFAULT '',
  action TEXT DEFAULT '',
  detail TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now','localtime'))
);
"""


def hash_pwd(pwd: str) -> str:
    return hashlib.sha256(("apitest::" + pwd).encode("utf-8")).hexdigest()


def get_conn():
    conn = getattr(_local, "conn", None)
    if conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        _local.conn = conn
    return conn


def q(sql, params=()):
    return get_conn().execute(sql, params).fetchall()


def q1(sql, params=()):
    return get_conn().execute(sql, params).fetchone()


def ex(sql, params=()):
    conn = get_conn()
    cur = conn.execute(sql, params)
    conn.commit()
    return cur.lastrowid


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    # 存量库迁移：users 表可能缺少新字段
    _migrate_users()
    # 种子：默认管理员 admin / admin123
    if not q1("SELECT id FROM users WHERE username='admin'"):
        ex("INSERT INTO users(username,password,role) VALUES(?,?,?)",
           ("admin", hash_pwd("admin123"), "admin"))
    if not q1("SELECT id FROM ai_config WHERE id=1"):
        ex("INSERT INTO ai_config(id,model,api_key,base_url,timeout) VALUES(1,'deepseek-chat','','https://api.deepseek.com/v1',60)")
    # 种子：内置角色 + 将 admin 用户绑定到超级管理员角色
    _seed_roles()



def op_log(username, action, detail=""):
    try:
        ex("INSERT INTO op_logs(username,action,detail) VALUES(?,?,?)", (username, action, str(detail)[:500]))
    except Exception:
        pass


def _migrate_users():
    """为已存在的 users 表补齐新字段（兼容旧库）"""
    try:
        cols = [r[1] for r in get_conn().execute("PRAGMA table_info(users)").fetchall()]
        for col, ddl in (
            ("nickname", "ALTER TABLE users ADD COLUMN nickname TEXT DEFAULT ''"),
            ("status", "ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'"),
            ("role_id", "ALTER TABLE users ADD COLUMN role_id INTEGER"),
            ("menu_keys", "ALTER TABLE users ADD COLUMN menu_keys TEXT DEFAULT '[]'"),
        ):
            if col not in cols:
                get_conn().execute(ddl)
        get_conn().commit()
    except Exception:
        pass


def _seed_roles():
    """内置默认角色：超级管理员（全部权限）/ 测试工程师 / 只读访客"""
    all_menus = '["dashboard","projects","envs","apis","ai-generate","cases","execution","reports","ai-config","users"]'
    tester_menus = '["dashboard","projects","envs","apis","ai-generate","cases","execution","reports"]'
    viewer_menus = '["dashboard","projects","apis","cases","reports"]'
    roles = [
        ("超级管理员", "admin", "拥有平台全部功能与系统配置权限", all_menus, 1),
        ("测试工程师", "tester", "可参与测试全流程，无系统配置与用户管理权限", tester_menus, 1),
        ("只读访客", "viewer", "仅可浏览项目、接口、用例与测试报告", viewer_menus, 1),
    ]
    for name, code, desc, menus, is_sys in roles:
        if not q1("SELECT id FROM roles WHERE code=?", (code,)):
            ex("INSERT INTO roles(name,code,description,menu_keys,is_system) VALUES(?,?,?,?,?)",
               (name, code, desc, menus, is_sys))
    # 将 admin 用户绑定到超级管理员角色并赋全部菜单
    admin_role = q1("SELECT id FROM roles WHERE code='admin'")
    if admin_role and not q1("SELECT role_id FROM users WHERE username='admin' AND role_id IS NOT NULL"):
        ex("UPDATE users SET role_id=?, menu_keys=? WHERE username='admin'",
           (admin_role["id"], all_menus))


def row_to_dict(row):
    return {k: row[k] for k in row.keys()} if row is not None else None


def rows_to_dicts(rows):
    return [{k: r[k] for k in r.keys()} for r in rows]
