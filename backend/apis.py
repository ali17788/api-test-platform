# -*- coding: utf-8 -*-
"""接口管理模块：列表 / 增删改查 / 文档上传解析"""
from fastapi import APIRouter, Request, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import os
import db as d
from utils import ok, http_err, get_user, jloads, jdumps
from services.parser import parse_document, SUPPORTED_EXT

router = APIRouter(prefix="/api", tags=["apis"])


class ApiBody(BaseModel):
    name: str
    method: str = "GET"
    path: str = "/"
    module: str = "默认模块"
    headers: dict = {}
    query_params: dict = {}
    body: dict = {}
    response_schema: dict = {}


def _api_dict(r):
    item = d.row_to_dict(r)
    for k in ("headers", "query_params", "body", "response_schema"):
        item[k] = jloads(item.get(k), {})
    return item


@router.get("/projects/{pid}/apis")
def list_apis(pid: int, request: Request, keyword: str = "", page: int = 1, size: int = 10):
    get_user(request)
    where = "project_id=?"
    params = [pid]
    if keyword:
        where += " AND (name LIKE ? OR path LIKE ?)"
        params += [f"%{keyword}%", f"%{keyword}%"]
    total = d.q1(f"SELECT COUNT(*) c FROM apis WHERE {where}", params)["c"]
    rows = d.q(f"SELECT * FROM apis WHERE {where} ORDER BY id DESC LIMIT ? OFFSET ?",
               params + [size, (page - 1) * size])
    return ok({"total": total, "list": [_api_dict(r) for r in rows]})


@router.get("/projects/{pid}/apis/all")
def list_all_apis(pid: int, request: Request):
    get_user(request)
    rows = d.q("SELECT * FROM apis WHERE project_id=? ORDER BY id", (pid,))
    return ok([_api_dict(r) for r in rows])


@router.get("/apis/{aid}")
def get_api(aid: int, request: Request):
    get_user(request)
    r = d.q1("SELECT * FROM apis WHERE id=?", (aid,))
    if not r:
        http_err(404, "接口不存在")
    return ok(_api_dict(r))


@router.post("/projects/{pid}/apis")
def create_api(pid: int, body: ApiBody, request: Request):
    user = get_user(request)
    if not body.name.strip():
        http_err(400, "接口名称不能为空")
    aid = d.ex(
        "INSERT INTO apis(project_id,name,method,path,module,headers,query_params,body,response_schema) VALUES(?,?,?,?,?,?,?,?,?)",
        (pid, body.name.strip(), body.method.upper(), body.path.strip() or "/",
         body.module.strip() or "默认模块", jdumps(body.headers), jdumps(body.query_params),
         jdumps(body.body), jdumps(body.response_schema)))
    d.op_log(user["username"], "新增接口", f"项目#{pid} {body.name}")
    return ok({"id": aid}, msg="接口创建成功")


@router.put("/apis/{aid}")
def update_api(aid: int, body: ApiBody, request: Request):
    user = get_user(request)
    if not d.q1("SELECT id FROM apis WHERE id=?", (aid,)):
        http_err(404, "接口不存在")
    d.ex("UPDATE apis SET name=?,method=?,path=?,module=?,headers=?,query_params=?,body=?,response_schema=? WHERE id=?",
         (body.name.strip(), body.method.upper(), body.path.strip() or "/", body.module.strip() or "默认模块",
          jdumps(body.headers), jdumps(body.query_params), jdumps(body.body), jdumps(body.response_schema), aid))
    d.op_log(user["username"], "编辑接口", f"#{aid} {body.name}")
    return ok(msg="接口更新成功")


@router.delete("/apis/{aid}")
def delete_api(aid: int, request: Request):
    user = get_user(request)
    if not d.q1("SELECT id FROM apis WHERE id=?", (aid,)):
        http_err(404, "接口不存在")
    d.ex("DELETE FROM cases WHERE api_id=?", (aid,))
    d.ex("DELETE FROM apis WHERE id=?", (aid,))
    d.op_log(user["username"], "删除接口", f"#{aid}")
    return ok(msg="接口已删除")


@router.post("/projects/{pid}/apis/upload")
async def upload_doc(pid: int, request: Request, file: UploadFile = File(...)):
    user = get_user(request)
    fname = file.filename or ""
    ext = os.path.splitext(fname.lower())[1]
    if ext and ext not in SUPPORTED_EXT:
        http_err(400, f"不支持的文件类型 {ext}，当前支持：{(' / '.join(SUPPORTED_EXT))}")
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        http_err(400, "文件过大（限制 20MB）")
    apis, parse_err = parse_document(file.filename or "", content)
    if parse_err:
        http_err(400, f"解析失败：{parse_err}")
    if not apis:
        http_err(400, "解析成功但未发现有效接口")
    # 查重：同项目下 method+path 已存在则跳过
    existing = {(r["method"], r["path"]) for r in d.q("SELECT method,path FROM apis WHERE project_id=?", (pid,))}
    inserted = 0
    for a in apis:
        if (a["method"], a["path"]) in existing:
            continue
        d.ex("INSERT INTO apis(project_id,name,method,path,module,headers,query_params,body,response_schema) VALUES(?,?,?,?,?,?,?,?,?)",
             (pid, a["name"], a["method"], a["path"], a["module"], jdumps(a["headers"]),
              jdumps(a["query_params"]), jdumps(a["body"]), jdumps(a["response_schema"])))
        inserted += 1
    d.op_log(user["username"], "上传接口文档", f"项目#{pid} {file.filename} 解析{len(apis)}个接口，新增{inserted}个")
    return ok({"parsed": len(apis), "inserted": inserted},
              msg=f"接口文档解析完成，共 {len(apis)} 个有效接口，新增入库 {inserted} 个（重复已跳过）")
