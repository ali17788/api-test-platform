# -*- coding: utf-8 -*-
"""用例管理模块：筛选 / 增删改 / 单条执行 / 批量操作"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
import db as d
from utils import ok, http_err, get_user, jloads, jdumps
from services import executor

router = APIRouter(prefix="/api", tags=["cases"])


class CaseBody(BaseModel):
    api_id: int
    name: str
    case_type: str = "正向"
    priority: str = "P1"
    steps: str = ""
    request_data: dict = {}
    expected: dict = {}


def _case_dict(r):
    item = d.row_to_dict(r)
    item["request_data"] = jloads(item.get("request_data"), {})
    item["expected"] = jloads(item.get("expected"), {})
    return item


def _ordered_cases(pid, api_id=None, case_type="", priority="", keyword="", page=1, size=10):
    """返回 (rows, total)，按 模块→接口→类型→优先级 标准化排序"""
    where = "c.project_id=?"
    params = [pid]
    if api_id:
        where += " AND c.api_id=?"
        params.append(api_id)
    if case_type:
        where += " AND c.case_type=?"
        params.append(case_type)
    if priority:
        where += " AND c.priority=?"
        params.append(priority)
    if keyword:
        where += " AND c.name LIKE ?"
        params.append(f"%{keyword}%")
    total = d.q1(f"SELECT COUNT(*) c FROM cases c WHERE {where}", params)["c"]
    order = ("ORDER BY a.module, c.api_id, "
             "CASE c.case_type WHEN '正向' THEN 1 WHEN '反向' THEN 2 WHEN '边界' THEN 3 ELSE 4 END, "
             "CASE c.priority WHEN 'P0' THEN 1 WHEN 'P1' THEN 2 ELSE 3 END, c.id")
    rows = d.q(f"SELECT c.*, a.name AS api_name, a.method, a.path, a.module FROM cases c "
               f"LEFT JOIN apis a ON a.id=c.api_id WHERE {where} {order} LIMIT ? OFFSET ?",
               params + [size, (page - 1) * size])
    return rows, total


@router.get("/projects/{pid}/cases")
def list_cases(pid: int, request: Request, api_id: int | None = None, case_type: str = "",
               priority: str = "", keyword: str = "", page: int = 1, size: int = 10):
    get_user(request)
    rows, total = _ordered_cases(pid, api_id, case_type, priority, keyword, page, size)
    return ok({"total": total, "list": [_case_dict(r) for r in rows]})


@router.get("/cases/{cid}")
def get_case(cid: int, request: Request):
    get_user(request)
    r = d.q1("SELECT * FROM cases WHERE id=?", (cid,))
    if not r:
        http_err(404, "用例不存在")
    return ok(_case_dict(r))


@router.post("/projects/{pid}/cases")
def create_case(pid: int, body: CaseBody, request: Request):
    user = get_user(request)
    if not body.name.strip():
        http_err(400, "用例名称不能为空")
    if not d.q1("SELECT id FROM apis WHERE id=? AND project_id=?", (body.api_id, pid)):
        http_err(400, "所属接口不存在")
    cid = d.ex("INSERT INTO cases(project_id,api_id,name,case_type,priority,steps,request_data,expected,source) VALUES(?,?,?,?,?,?,?,?,?)",
               (pid, body.api_id, body.name.strip(), body.case_type, body.priority, body.steps,
                jdumps(body.request_data), jdumps(body.expected), "MANUAL"))
    d.op_log(user["username"], "新增用例", f"#{cid} {body.name}")
    return ok({"id": cid}, msg="用例创建成功")


@router.put("/cases/{cid}")
def update_case(cid: int, body: CaseBody, request: Request):
    user = get_user(request)
    if not d.q1("SELECT id FROM cases WHERE id=?", (cid,)):
        http_err(404, "用例不存在")
    d.ex("UPDATE cases SET api_id=?,name=?,case_type=?,priority=?,steps=?,request_data=?,expected=? WHERE id=?",
         (body.api_id, body.name.strip(), body.case_type, body.priority, body.steps,
          jdumps(body.request_data), jdumps(body.expected), cid))
    d.op_log(user["username"], "编辑用例", f"#{cid} {body.name}")
    return ok(msg="用例更新成功")


@router.delete("/cases/{cid}")
def delete_case(cid: int, request: Request):
    user = get_user(request)
    if not d.q1("SELECT id FROM cases WHERE id=?", (cid,)):
        http_err(404, "用例不存在")
    d.ex("DELETE FROM cases WHERE id=?", (cid,))
    d.op_log(user["username"], "删除用例", f"#{cid}")
    return ok(msg="用例已删除")


@router.post("/cases/batch-delete")
async def batch_delete(request: Request):
    user = get_user(request)
    try:
        data = await request.json()
    except Exception:
        data = []
    if isinstance(data, dict):
        ids = data.get("ids", [])
    else:
        ids = data or []
    ids = [int(i) for i in ids if str(i).isdigit()]
    if not ids:
        http_err(400, "请选择要删除的用例")
    placeholders = ",".join("?" * len(ids))
    d.ex(f"DELETE FROM cases WHERE id IN ({placeholders})", ids)
    d.op_log(user["username"], "批量删除用例", f"{len(ids)}条")
    return ok(msg=f"已删除 {len(ids)} 条用例")


class RunBody(BaseModel):
    ids: list = []
    case_id: int = 0
    env_id: int | None = None


@router.post("/cases/run")
def run_single(body: RunBody, request: Request):
    """执行单条 / 批量选中的用例。
    环境优先级：显式传入 env_id → 项目默认环境 → 项目首个环境。
    若项目下没有任何环境且接口路径非完整 URL，则拒绝启动并提示先配置环境。"""
    user = get_user(request)
    target_ids = body.ids or ([body.case_id] if body.case_id else [])
    if not target_ids:
        http_err(400, "请选择要执行的用例")
    first = d.q1("SELECT * FROM cases WHERE id=?", (target_ids[0],))
    if not first:
        http_err(404, "用例不存在")
    pid = first["project_id"]

    env = None
    if body.env_id:
        env = d.q1("SELECT * FROM environments WHERE id=? AND project_id=?", (body.env_id, pid))
        if not env:
            http_err(400, "所选环境不存在")
    if env is None:
        env = d.q1("SELECT * FROM environments WHERE project_id=? AND is_default=1", (pid,))
    if env is None:
        env = d.q1("SELECT * FROM environments WHERE project_id=? ORDER BY id LIMIT 1", (pid,))
    env_row = d.row_to_dict(env) if env else None

    # 无任何环境时，检查待执行用例的接口是否自带完整域名
    if env_row is None:
        ph = ",".join("?" * len(target_ids))
        rows = d.q(f"""SELECT a.path FROM cases c JOIN apis a ON a.id=c.api_id
                       WHERE c.id IN ({ph}) AND (a.path IS NULL OR a.path NOT LIKE 'http%') LIMIT 1""",
                   target_ids)
        if rows:
            http_err(400, "该项目尚未配置测试环境，请先到「环境配置」添加环境（填写接口域名）后再执行")

    seq = d.q1("SELECT COUNT(*) c FROM tasks")["c"] + 1
    name = f"快速执行任务-{seq:03d}"
    task_id = d.ex("""INSERT INTO tasks(project_id,name,env_id,env_name,case_ids,status,total)
                      VALUES(?,?,?,?,?,?,?)""",
                   (pid, name, env_row["id"] if env_row else None,
                    env_row["name"] if env_row else "", jdumps(target_ids), "pending", len(target_ids)))
    d.op_log(user["username"], "执行用例", f"任务#{task_id} 共{len(target_ids)}条")
    executor.start_task(task_id)
    return ok({"task_id": task_id, "total": len(target_ids)}, msg="执行任务已启动")


@router.get("/projects/{pid}/cases/all")
def list_all_cases(pid: int, request: Request):
    get_user(request)
    rows = d.q("SELECT c.*, a.name AS api_name, a.method, a.path, a.module FROM cases c LEFT JOIN apis a ON a.id=c.api_id "
               "WHERE c.project_id=? ORDER BY c.id", (pid,))
    return ok([_case_dict(r) for r in rows])
