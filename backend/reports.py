# -*- coding: utf-8 -*-
"""测试报告模块：报告列表 / 详情 / 多格式导出 / 删除"""
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
import os
import db as d
from utils import ok, http_err, get_user, jloads
from services import exporter

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/project/{pid}")
def list_reports(pid: int, request: Request, page: int = 1, size: int = 10):
    get_user(request)
    total = d.q1("SELECT COUNT(*) c FROM tasks WHERE project_id=?", (pid,))["c"]
    rows = d.q("SELECT * FROM tasks WHERE project_id=? ORDER BY id DESC LIMIT ? OFFSET ?",
               (pid, size, (page - 1) * size))
    out = []
    for r in rows:
        item = d.row_to_dict(r)
        item["pass_rate"] = round(item["passed"] / item["executed"] * 100, 1) if item["executed"] else 0
        item.update(exporter.env_of_task(item))
        out.append(item)
    return ok({"total": total, "list": out})


@router.get("/{task_id}")
def report_detail(task_id: int, request: Request):
    get_user(request)
    ctx = exporter.report_context(task_id)
    if not ctx:
        http_err(404, "报告不存在")
    t = ctx["task"]
    results = ctx["results"]
    module_map = {}
    for r in results:
        m = r["module"] or "默认模块"
        tot, okc = module_map.get(m, (0, 0))
        module_map[m] = (tot + 1, okc + (1 if r["status"] == "passed" else 0))
    module_stats = [{"module": m, "total": v[0], "passed": v[1],
                     "rate": round(v[1] / v[0] * 100, 1) if v[0] else 0} for m, v in module_map.items()]
    return ok({
        "task": t,
        "pass_rate": round(t["passed"] / t["executed"] * 100, 1) if t["executed"] else 0,
        "results": results,
        "module_stats": module_stats,
        "logs": [{"id": r["id"], "level": r["level"], "message": r["message"]}
                 for r in d.q("SELECT * FROM task_logs WHERE task_id=? ORDER BY id", (task_id,))],
    })


@router.get("/{task_id}/export")
def export_report(task_id: int, request: Request, fmt: str = "html", download: int = 1):
    get_user(request)
    fmt = (fmt or "html").lower()
    if fmt in ("html", "htm"):
        path = exporter.export_report_html(task_id)
        if not path:
            http_err(404, "报告不存在")
        if not download:
            with open(path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return FileResponse(path, filename=os.path.basename(path), media_type="text/html")
    elif fmt == "excel":
        path = exporter.export_report_excel(task_id)
    elif fmt == "pdf":
        path = exporter.export_report_pdf(task_id)
    else:
        http_err(400, "不支持的导出格式")
    if not path:
        http_err(404, "报告不存在")
    media = "application/pdf" if fmt == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return FileResponse(path, filename=os.path.basename(path), media_type=media)


@router.delete("/{task_id}")
def delete_report(task_id: int, request: Request):
    user = get_user(request)
    if not d.q1("SELECT id FROM tasks WHERE id=?", (task_id,)):
        http_err(404, "报告不存在")
    d.ex("DELETE FROM case_results WHERE task_id=?", (task_id,))
    d.ex("DELETE FROM task_logs WHERE task_id=?", (task_id,))
    d.ex("DELETE FROM tasks WHERE id=?", (task_id,))
    d.op_log(user["username"], "删除报告", f"任务#{task_id}")
    return ok(msg="报告已删除")
