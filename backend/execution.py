# -*- coding: utf-8 -*-
"""测试执行模块：创建任务 / 实时状态轮询 / 日志 / 终止 / 重跑失败用例"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
import db as d
from utils import ok, http_err, get_user, jloads, jdumps
from services import executor

router = APIRouter(prefix="/api/execution", tags=["execution"])


class TaskBody(BaseModel):
    project_id: int
    env_id: int | None = None
    scope: str = "all"               # all / selected / failed
    case_ids: list = []              # scope=selected 时生效
    task_name: str = ""


@router.post("/start")
def start_task(body: TaskBody, request: Request):
    user = get_user(request)
    if body.scope == "selected":
        ids = [c for c in (body.case_ids or [])]
    elif body.scope == "failed":
        ids = [r["id"] for r in d.q("SELECT id FROM cases WHERE project_id=? AND last_status='failed'", (body.project_id,))]
    else:
        ids = [r["id"] for r in d.q("SELECT id FROM cases WHERE project_id=?", (body.project_id,))]
    if not ids:
        http_err(400, "选择的执行范围内没有可执行用例")

    env = None
    if body.env_id:
        env = d.q1("SELECT * FROM environments WHERE id=? AND project_id=?", (body.env_id, body.project_id))
        if not env:
            http_err(400, "所选环境不存在")
    if env is None:
        env = d.q1("SELECT * FROM environments WHERE project_id=? AND is_default=1", (body.project_id,))
    env_dict = d.row_to_dict(env) if env else None
    seq = d.q1("SELECT COUNT(*) c FROM tasks")["c"] + 1
    name = body.task_name.strip() or f"测试任务-{seq:03d}"
    task_id = d.ex("""INSERT INTO tasks(project_id,name,env_id,env_name,case_ids,status,total)
                      VALUES(?,?,?,?,?,?,?)""",
                   (body.project_id, name, env_dict["id"] if env_dict else None,
                    env_dict["name"] if env_dict else "", jdumps(ids), "pending", len(ids)))
    d.op_log(user["username"], "启动测试任务", f"任务#{task_id} {name} 用例{len(ids)}条")
    executor.start_task(task_id)
    return ok({"task_id": task_id, "total": len(ids)}, msg="任务已启动")


@router.get("/{task_id}/status")
def task_status(task_id: int, request: Request, log_after: int = 0):
    get_user(request)
    t = d.q1("SELECT * FROM tasks WHERE id=?", (task_id,))
    if not t:
        http_err(404, "任务不存在")
    logs = d.q("SELECT id, level, message FROM task_logs WHERE task_id=? AND id>? ORDER BY id LIMIT 200",
               (task_id, log_after))
    return ok({
        "task": d.row_to_dict(t),
        "running": t["status"] == "running",
        "logs": [{"id": r["id"], "level": r["level"], "message": r["message"]} for r in logs],
    })


@router.post("/{task_id}/stop")
def stop_task(task_id: int, request: Request):
    user = get_user(request)
    t = d.q1("SELECT * FROM tasks WHERE id=?", (task_id,))
    if not t:
        http_err(404, "任务不存在")
    stopped = executor.stop_task(task_id)
    if not stopped:
        http_err(400, "任务不在运行中，无法终止")
    d.op_log(user["username"], "终止测试任务", f"任务#{task_id}")
    return ok(msg="终止指令已发送")


@router.post("/{task_id}/rerun-failed")
def rerun_failed(task_id: int, request: Request):
    """重跑指定任务中的失败用例，生成新任务"""
    user = get_user(request)
    t = d.q1("SELECT * FROM tasks WHERE id=?", (task_id,))
    if not t:
        http_err(404, "任务不存在")
    failed_ids = [r["case_id"] for r in d.q("SELECT case_id FROM case_results WHERE task_id=? AND status='failed'", (task_id,))]
    if not failed_ids:
        http_err(400, "该任务没有失败用例，无需重跑")
    new_name = f"重跑失败用例-{t['name']}"
    new_id = d.ex("""INSERT INTO tasks(project_id,name,env_id,env_name,case_ids,status,total)
                     VALUES(?,?,?,?,?,?,?)""",
                  (t["project_id"], new_name, t["env_id"], t["env_name"], jdumps(failed_ids), "pending", len(failed_ids)))
    d.op_log(user["username"], "重跑失败用例", f"任务#{task_id} -> 新任务#{new_id} {len(failed_ids)}条")
    executor.start_task(new_id)
    return ok({"task_id": new_id, "total": len(failed_ids)}, msg=f"已创建重跑任务，共 {len(failed_ids)} 条失败用例")
