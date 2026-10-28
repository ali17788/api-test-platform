# -*- coding: utf-8 -*-
"""项目管理 + 测试环境配置"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
import db as d
from utils import ok, http_err, get_user, jloads, jdumps

router = APIRouter(prefix="/api", tags=["projects"])


# ---------------- 项目管理 ----------------
class ProjectBody(BaseModel):
    name: str
    description: str = ""


def _project_stats(pid):
    api_cnt = d.q1("SELECT COUNT(*) c FROM apis WHERE project_id=?", (pid,))["c"]
    case_cnt = d.q1("SELECT COUNT(*) c FROM cases WHERE project_id=?", (pid,))["c"]
    return api_cnt, case_cnt


@router.get("/projects")
def list_projects(request: Request, keyword: str = ""):
    get_user(request)
    rows = d.q("SELECT * FROM projects ORDER BY id DESC")
    out = []
    for r in rows:
        if keyword and keyword not in r["name"]:
            continue
        item = d.row_to_dict(r)
        item["api_count"], item["case_count"] = _project_stats(r["id"])
        out.append(item)
    return ok(out)


@router.post("/projects")
def create_project(body: ProjectBody, request: Request):
    user = get_user(request)
    if not body.name.strip():
        http_err(400, "项目名称不能为空")
    pid = d.ex("INSERT INTO projects(name,description,owner) VALUES(?,?,?)",
               (body.name.strip(), body.description.strip(), user["username"]))
    d.op_log(user["username"], "新增项目", body.name)
    return ok({"id": pid}, msg="项目创建成功")


@router.put("/projects/{pid}")
def update_project(pid: int, body: ProjectBody, request: Request):
    user = get_user(request)
    if not d.q1("SELECT id FROM projects WHERE id=?", (pid,)):
        http_err(404, "项目不存在")
    d.ex("UPDATE projects SET name=?, description=? WHERE id=?",
         (body.name.strip(), body.description.strip(), pid))
    d.op_log(user["username"], "编辑项目", f"#{pid} {body.name}")
    return ok(msg="项目更新成功")


@router.delete("/projects/{pid}")
def delete_project(pid: int, request: Request):
    user = get_user(request)
    if not d.q1("SELECT id FROM projects WHERE id=?", (pid,)):
        http_err(404, "项目不存在")
    for t in ("environments", "apis", "cases"):
        d.ex(f"DELETE FROM {t} WHERE project_id=?", (pid,))
    d.ex("DELETE FROM tasks WHERE project_id=?", (pid,))
    d.ex("DELETE FROM projects WHERE id=?", (pid,))
    d.op_log(user["username"], "删除项目", f"#{pid}")
    return ok(msg="项目已删除")


@router.get("/projects/{pid}/overview")
def project_overview(pid: int, request: Request):
    get_user(request)
    p = d.q1("SELECT * FROM projects WHERE id=?", (pid,))
    if not p:
        http_err(404, "项目不存在")
    api_cnt, case_cnt = _project_stats(pid)
    env_cnt = d.q1("SELECT COUNT(*) c FROM environments WHERE project_id=?", (pid,))["c"]
    return ok({"project": d.row_to_dict(p), "api_count": api_cnt, "case_count": case_cnt, "env_count": env_cnt})


# ---------------- 环境配置 ----------------
class EnvBody(BaseModel):
    name: str
    base_url: str
    headers: list = []          # [{"key","value"}]
    timeout: int = 10
    retry: int = 0
    is_default: bool = False


def _env_dict(r):
    item = d.row_to_dict(r)
    raw = jloads(item.get("headers"), [])
    item["headers"] = raw if isinstance(raw, list) else []
    return item


@router.get("/projects/{pid}/envs")
def list_envs(pid: int, request: Request):
    get_user(request)
    rows = d.q("SELECT * FROM environments WHERE project_id=? ORDER BY is_default DESC, id", (pid,))
    return ok([_env_dict(r) for r in rows])


@router.post("/projects/{pid}/envs")
def create_env(pid: int, body: EnvBody, request: Request):
    user = get_user(request)
    if not body.name.strip() or not body.base_url.strip():
        http_err(400, "环境名称与接口域名不能为空")
    if body.is_default:
        d.ex("UPDATE environments SET is_default=0 WHERE project_id=?", (pid,))
    eid = d.ex("INSERT INTO environments(project_id,name,base_url,headers,timeout,retry,is_default) VALUES(?,?,?,?,?,?,?)",
               (pid, body.name.strip(), body.base_url.strip().rstrip("/"),
                jdumps(body.headers), body.timeout, body.retry, 1 if body.is_default else 0))
    d.op_log(user["username"], "新增环境", f"项目#{pid} {body.name}")
    return ok({"id": eid}, msg="环境创建成功")


@router.put("/envs/{eid}")
def update_env(eid: int, body: EnvBody, request: Request):
    user = get_user(request)
    r = d.q1("SELECT * FROM environments WHERE id=?", (eid,))
    if not r:
        http_err(404, "环境不存在")
    pid = r["project_id"]
    if body.is_default:
        d.ex("UPDATE environments SET is_default=0 WHERE project_id=?", (pid,))
    d.ex("UPDATE environments SET name=?,base_url=?,headers=?,timeout=?,retry=?,is_default=? WHERE id=?",
         (body.name.strip(), body.base_url.strip().rstrip("/"), jdumps(body.headers),
          body.timeout, body.retry, 1 if body.is_default else 0, eid))
    d.op_log(user["username"], "编辑环境", f"#{eid} {body.name}")
    return ok(msg="环境更新成功")


@router.delete("/envs/{eid}")
def delete_env(eid: int, request: Request):
    user = get_user(request)
    if not d.q1("SELECT id FROM environments WHERE id=?", (eid,)):
        http_err(404, "环境不存在")
    d.ex("DELETE FROM environments WHERE id=?", (eid,))
    d.op_log(user["username"], "删除环境", f"#{eid}")
    return ok(msg="环境已删除")
