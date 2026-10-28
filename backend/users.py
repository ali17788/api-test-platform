# -*- coding: utf-8 -*-
"""用户与权限（RBAC）模块：菜单目录 / 角色管理 / 用户管理

权限模型：
  - 菜单（menu）是平台功能的最小权限单元，对应前端侧边栏的每一个入口。
  - 角色（role）聚合一组菜单权限；内置角色不可删除，可被多名用户复用。
  - 用户（user）绑定一个角色，并可在此基础上单独勾选/微调菜单权限（落库到 users.menu_keys）。
    最终权限 = 用户自身 menu_keys（优先）；若为空则回退取所属角色的 menu_keys。
  - 仅拥有 `users` 菜单权限（即超级管理员）可调用本模块的用户/角色管理接口。
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, List
import db as d
from utils import ok, http_err, get_user, jloads, jdumps

router = APIRouter(prefix="/api", tags=["users"])

# ----------------------- 菜单目录（平台全部功能入口，权限的最小单元） -----------------------
MENUS = [
    {"key": "dashboard",   "title": "首页仪表盘", "icon": "DataLine",     "path": "/dashboard"},
    {"key": "projects",    "title": "项目管理",   "icon": "Folder",       "path": "/projects"},
    {"key": "envs",        "title": "环境配置",   "icon": "Setting",      "path": "/envs"},
    {"key": "apis",        "title": "接口管理",   "icon": "Connection",   "path": "/apis"},
    {"key": "ai-generate", "title": "AI用例生成", "icon": "MagicStick",   "path": "/ai-generate"},
    {"key": "cases",       "title": "用例管理",   "icon": "Document",     "path": "/cases"},
    {"key": "execution",   "title": "测试执行",   "icon": "VideoPlay",    "path": "/execution"},
    {"key": "reports",     "title": "测试报告",   "icon": "DataAnalysis",  "path": "/reports"},
    {"key": "ai-config",   "title": "系统AI配置", "icon": "Key",          "path": "/ai-config"},
    {"key": "users",       "title": "用户与权限", "icon": "User",         "path": "/users"},
]
MENU_KEYS = [m["key"] for m in MENUS]
MENU_TITLE = {m["key"]: m["title"] for m in MENUS}
PERM_USERS = "users"  # 用户与权限管理入口的权限标识


# ----------------------- 权限辅助函数 -----------------------
def _valid_keys(keys):
    return [k for k in (keys or []) if k in MENU_KEYS]


def _as_dict(user):
    """sqlite3.Row 与 dict 统一为 dict，兼容各调用方"""
    return user if isinstance(user, dict) else d.row_to_dict(user)


def get_user_menus(user):
    """返回用户实际拥有的菜单 key 列表（去重且保证合法）"""
    if not user:
        return []
    user = _as_dict(user)
    keys = jloads(user.get("menu_keys"), None)
    if not keys:
        role = d.q1("SELECT * FROM roles WHERE id=?", (user.get("role_id"),)) if user.get("role_id") else None
        keys = jloads(role["menu_keys"], []) if role else []
    return _valid_keys(keys)


def get_role_name(user):
    user = _as_dict(user)
    if user.get("role_id"):
        role = d.q1("SELECT * FROM roles WHERE id=?", (user.get("role_id"),))
        if role:
            return role["name"]
    return user.get("role") or "普通用户"


def require_perm(request: Request, key: str = PERM_USERS):
    """校验当前登录用户是否拥有指定菜单权限，无权限直接 403"""
    user = get_user(request)
    if key not in get_user_menus(user):
        http_err(403, "无权限执行该操作（需要「用户与权限」菜单权限）")
    return user


def user_public(user):
    """用户对外字段（剔除密码）"""
    item = d.row_to_dict(user)
    item.pop("password", None)
    item["role_name"] = get_role_name(user)
    item["menus"] = get_user_menus(user)
    return item


# ----------------------- 菜单目录 -----------------------
@router.get("/menus")
def list_menus(request: Request):
    get_user(request)  # 登录即可获取目录（前端据此渲染可见菜单）
    return ok(MENUS)


# ----------------------- 角色管理 -----------------------
class RoleBody(BaseModel):
    name: str = ""
    code: str = ""
    description: str = ""
    menu_keys: List[str] = []


def _role_dict(r):
    item = d.row_to_dict(r)
    item["menu_keys"] = _valid_keys(jloads(item.get("menu_keys"), []))
    item["is_system"] = bool(item.get("is_system"))
    return item


@router.get("/roles")
def list_roles(request: Request):
    require_perm(request)
    rows = d.q("SELECT * FROM roles ORDER BY is_system DESC, id")
    return ok([_role_dict(r) for r in rows])


@router.post("/roles")
def create_role(body: RoleBody, request: Request):
    require_perm(request)
    name = (body.name or "").strip()
    code = (body.code or "").strip()
    if not name or not code:
        http_err(400, "角色名称与角色编码不能为空")
    if d.q1("SELECT id FROM roles WHERE code=?", (code,)):
        http_err(400, f"角色编码「{code}」已存在")
    keys = _valid_keys(body.menu_keys)
    rid = d.ex("INSERT INTO roles(name,code,description,menu_keys,is_system) VALUES(?,?,?,?,0)",
               (name, code, (body.description or "").strip(), jdumps(keys)))
    d.op_log(get_user(request)["username"], "新增角色", f"{name}({code})")
    return ok({"id": rid}, msg="角色创建成功")


@router.put("/roles/{rid}")
def update_role(rid: int, body: RoleBody, request: Request):
    require_perm(request)
    r = d.q1("SELECT * FROM roles WHERE id=?", (rid,))
    if not r:
        http_err(404, "角色不存在")
    name = (body.name or "").strip()
    if not name:
        http_err(400, "角色名称不能为空")
    # 内置角色的编码不可修改，防止与权限标识冲突
    code = r["code"] if r["is_system"] else (body.code or "").strip()
    keys = _valid_keys(body.menu_keys)
    d.ex("UPDATE roles SET name=?, description=?, menu_keys=? WHERE id=?",
         (name, (body.description or "").strip(), jdumps(keys), rid))
    d.op_log(get_user(request)["username"], "编辑角色", f"#{rid} {name}")
    return ok(msg="角色更新成功")


@router.delete("/roles/{rid}")
def delete_role(rid: int, request: Request):
    require_perm(request)
    r = d.q1("SELECT * FROM roles WHERE id=?", (rid,))
    if not r:
        http_err(404, "角色不存在")
    if r["is_system"]:
        http_err(400, "内置角色不可删除")
    cnt = d.q1("SELECT COUNT(*) c FROM users WHERE role_id=?", (rid,))["c"]
    if cnt > 0:
        http_err(400, f"该角色下仍有 {cnt} 名用户，请先调整用户角色后再删除")
    d.ex("DELETE FROM roles WHERE id=?", (rid,))
    d.op_log(get_user(request)["username"], "删除角色", f"#{rid} {r['name']}")
    return ok(msg="角色已删除")


# ----------------------- 用户管理 -----------------------
class UserBody(BaseModel):
    username: str = ""
    password: str = ""
    nickname: str = ""
    role_id: Optional[int] = None
    status: str = "active"
    menu_keys: List[str] = []


@router.get("/users")
def list_users(request: Request):
    require_perm(request)
    rows = d.q("SELECT * FROM users ORDER BY id")
    out = []
    for r in rows:
        u = user_public(r)
        # 统计该用户所属角色下的人数（用于删除校验展示）
        out.append(u)
    return ok(out)


@router.post("/users")
def create_user(body: UserBody, request: Request):
    require_perm(request)
    username = (body.username or "").strip()
    if not username:
        http_err(400, "登录用户名不能为空")
    if not body.password:
        http_err(400, "初始密码不能为空")
    if len(body.password) < 6:
        http_err(400, "密码长度至少 6 位")
    if d.q1("SELECT id FROM users WHERE username=?", (username,)):
        http_err(400, f"用户名「{username}」已存在")
    # 角色校验
    if body.role_id:
        role = d.q1("SELECT * FROM roles WHERE id=?", (body.role_id,))
        if not role:
            http_err(400, "所选角色不存在")
    # 菜单权限：优先使用传入的 menu_keys；为空则继承角色权限
    keys = _valid_keys(body.menu_keys)
    if not keys and body.role_id:
        role = d.q1("SELECT * FROM roles WHERE id=?", (body.role_id,))
        keys = _valid_keys(jloads(role["menu_keys"], [])) if role else []
    uid = d.ex("INSERT INTO users(username,password,role,nickname,status,role_id,menu_keys) VALUES(?,?,?,?,?,?,?)",
               (username, d.hash_pwd(body.password), "custom",
                (body.nickname or "").strip(), body.status or "active",
                body.role_id, jdumps(keys)))
    d.op_log(get_user(request)["username"], "新增用户", f"{username}(角色#{body.role_id})")
    return ok({"id": uid}, msg="用户创建成功")


@router.put("/users/{uid}")
def update_user(uid: int, body: UserBody, request: Request):
    require_perm(request)
    u = d.q1("SELECT * FROM users WHERE id=?", (uid,))
    if not u:
        http_err(404, "用户不存在")
    me = get_user(request)
    is_self = (u["id"] == me["id"])
    # 不能禁用 / 降权自己，避免把自己锁在门外
    if is_self and body.status and body.status != "active":
        http_err(400, "不能禁用当前登录账号")
    if is_self and body.role_id not in (None, u["role_id"]):
        http_err(400, "不能修改自身的角色")
    # 防止删除最后一个超级管理员：统计拥有 users 权限的管理员数量
    cur_menus = get_user_menus(u)
    new_role = d.q1("SELECT * FROM roles WHERE id=?", (body.role_id,)) if body.role_id else None
    new_keys = _valid_keys(body.menu_keys) or (jloads(new_role["menu_keys"], []) if new_role else [])
    if PERM_USERS in cur_menus and PERM_USERS not in new_keys and _admin_count() <= 1:
        http_err(400, "至少需保留一名拥有「用户与权限」权限的管理员")

    sets, params = [], []
    if body.nickname is not None:
        sets.append("nickname=?"); params.append((body.nickname or "").strip())
    if body.password:
        if len(body.password) < 6:
            http_err(400, "密码长度至少 6 位")
        sets.append("password=?"); params.append(d.hash_pwd(body.password))
    if body.role_id is not None:
        if body.role_id and not new_role:
            http_err(400, "所选角色不存在")
        sets.append("role_id=?"); params.append(body.role_id)
    if body.status:
        sets.append("status=?"); params.append(body.status)
    if body.menu_keys is not None:
        sets.append("menu_keys=?"); params.append(jdumps(new_keys))
    if sets:
        d.ex(f"UPDATE users SET {','.join(sets)} WHERE id=?", params + [uid])
    d.op_log(me["username"], "编辑用户", f"#{uid} {u['username']}")
    return ok(msg="用户更新成功")


@router.delete("/users/{uid}")
def delete_user(uid: int, request: Request):
    require_perm(request)
    u = d.q1("SELECT * FROM users WHERE id=?", (uid,))
    if not u:
        http_err(404, "用户不存在")
    me = get_user(request)
    if u["id"] == me["id"]:
        http_err(400, "不能删除当前登录账号")
    if get_user_menus(u).count(PERM_USERS) and _admin_count() <= 1:
        http_err(400, "至少需保留一名管理员，无法删除")
    d.ex("DELETE FROM users WHERE id=?", (uid,))
    d.op_log(me["username"], "删除用户", f"#{uid} {u['username']}")
    return ok(msg="用户已删除")


def _admin_count():
    """拥有「用户与权限」菜单权限的用户数量"""
    rows = d.q("SELECT id, role_id, menu_keys FROM users")
    return sum(1 for r in rows if PERM_USERS in get_user_menus(d.row_to_dict(r)))
