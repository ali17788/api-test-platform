# -*- coding: utf-8 -*-
"""AI 驱动 Web 接口自动化测试工具 - 后端服务入口"""
import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import db as d
from utils import ok
from auth import router as auth_router
from projects import router as projects_router
from apis import router as apis_router
from cases import router as cases_router
from users import router as users_router
from ai import router as ai_router
from execution import router as exec_router
from reports import router as reports_router
from dashboard import router as dash_router
from services import exporter

# 用例文档导出路由
from fastapi import Request

app = FastAPI(title="AI驱动Web接口自动化测试平台", version="1.0.0",
              description="零代码 · AI全自动 · 接口自动化测试平台 后端服务")


@app.exception_handler(StarletteHTTPException)
async def _http_exc_handler(request, exc):
    """统一错误响应体：{code, msg, data}，与业务响应保持一致"""
    detail = exc.detail if isinstance(exc.detail, str) else "请求失败"
    return JSONResponse(status_code=exc.status_code,
                        content={"code": exc.status_code, "msg": detail, "data": None})


@app.exception_handler(Exception)
async def _server_exc_handler(request, exc):
    traceback.print_exc()
    return JSONResponse(status_code=500,
                        content={"code": 500, "msg": f"服务端异常：{exc}", "data": None})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

d.init_db()

for r in (auth_router, projects_router, apis_router, cases_router, users_router, ai_router, exec_router, reports_router, dash_router):
    app.include_router(r)

@app.get("/api/health")
def health():
    return ok({"status": "running", "product": "AI驱动Web接口自动化测试平台"})


@app.get("/api/projects/{pid}/cases/export")
def export_cases(pid: int, request: Request, fmt: str = "word"):
    from utils import get_user, http_err
    get_user(request)
    p = d.q1("SELECT * FROM projects WHERE id=?", (pid,))
    if not p:
        http_err(404, "项目不存在")
    fmt = (fmt or "word").lower()
    if fmt == "word":
        path = exporter.export_cases_word(pid, p["name"])
        return FileResponse(path, filename=os.path.basename(path),
                            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    if fmt in ("excel", "xlsx"):
        path = exporter.export_cases_excel(pid, p["name"])
        return FileResponse(path, filename=os.path.basename(path),
                            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if fmt == "pdf":
        path = exporter.export_cases_pdf(pid, p["name"])
        return FileResponse(path, filename=os.path.basename(path), media_type="application/pdf")
    http_err(400, "不支持的导出格式")


@app.get("/api/logs")
def op_logs(request: Request):
    from utils import get_user as gu
    gu(request)
    rows = d.q("SELECT * FROM op_logs ORDER BY id DESC LIMIT 50")
    return ok([d.row_to_dict(r) for r in rows])


# ---------- 前端静态资源（生产部署：前端 build 后置于 web 目录） ----------
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
if os.path.isdir(WEB_DIR):
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
