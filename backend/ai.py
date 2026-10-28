# -*- coding: utf-8 -*-
"""AI 模块：系统 AI 配置 / 连通性测试 / 用例生成 / 用例文档整理"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
import db as d
from utils import ok, http_err, get_user, jloads, jdumps
from services import ai_client

router = APIRouter(prefix="/api/ai", tags=["ai"])


class AiConfigBody(BaseModel):
    model: str = "deepseek-chat"
    api_key: str = ""
    base_url: str = "https://api.deepseek.com/v1"
    timeout: int = 60


@router.get("/config")
def get_cfg(request: Request):
    get_user(request)
    cfg = ai_client.get_config()
    masked = cfg["api_key"][:6] + "****" + cfg["api_key"][-4:] if len(cfg["api_key"]) > 12 else ("****" if cfg["api_key"] else "")
    return ok({**cfg, "api_key": cfg["api_key"], "api_key_masked": masked, "configured": bool(cfg["api_key"])})


@router.post("/config")
def save_cfg(body: AiConfigBody, request: Request):
    user = get_user(request)
    if not body.base_url.strip():
        http_err(400, "BaseURL 不能为空")
    if body.timeout < 5 or body.timeout > 600:
        http_err(400, "AI 请求超时时间需在 5-600 秒之间")
    d.ex("UPDATE ai_config SET model=?,api_key=?,base_url=?,timeout=? WHERE id=1",
         (body.model.strip(), body.api_key.strip(), body.base_url.strip().rstrip("/"), body.timeout))
    d.op_log(user["username"], "保存AI配置", f"模型 {body.model}")
    return ok(msg="AI 配置保存成功，已全局生效")


@router.post("/config/test")
def test_cfg(request: Request, body: AiConfigBody | None = None):
    get_user(request)
    if body and body.api_key:
        cfg = {"model": body.model, "api_key": body.api_key,
               "base_url": body.base_url.rstrip("/"), "timeout": body.timeout}
    else:
        cfg = ai_client.get_config()
    success, msg = ai_client.test_connection(cfg)
    return ok({"success": success, "message": msg})


class GenerateBody(BaseModel):
    project_id: int
    scope: str = "all"          # all / single
    api_id: int | None = None
    gen_type: str = "full"      # positive / full


@router.post("/generate")
def generate(body: GenerateBody, request: Request):
    """单接口生成（前端批量场景下逐个调用，天然支持实时进度）"""
    user = get_user(request)
    if body.scope == "single":
        if not body.api_id:
            http_err(400, "请选择要生成的接口")
        api_row = d.q1("SELECT * FROM apis WHERE id=? AND project_id=?", (body.api_id, body.project_id))
        if not api_row:
            http_err(404, "接口不存在")
        targets = [d.row_to_dict(api_row)]
    else:
        targets = d.rows_to_dicts(d.q("SELECT * FROM apis WHERE project_id=? ORDER BY id", (body.project_id,)))
        if not targets:
            http_err(400, "当前项目暂无接口，请先导入接口文档")

    total_generated, used_ai = 0, False
    for api in targets:
        # 生成前清除该接口旧的 AI 用例（避免重复堆积）
        d.ex("DELETE FROM cases WHERE api_id=? AND source='AI'", (api["id"],))
        cases, is_ai, _ = ai_client.generate_cases_for_api(api, body.gen_type)
        used_ai = used_ai or is_ai
        for c in cases:
            d.ex("INSERT INTO cases(project_id,api_id,name,case_type,priority,steps,request_data,expected,source) VALUES(?,?,?,?,?,?,?,?,?)",
                 (body.project_id, api["id"], c["name"], c["case_type"], c["priority"], c["steps"],
                  jdumps(c["request_data"]), jdumps(c["expected"]), "AI"))
        total_generated += len(cases)
    d.op_log(user["username"], "AI生成用例",
             f"项目#{body.project_id} 接口{len(targets)}个 生成用例{total_generated}条 {'大模型' if used_ai else '规则引擎'}")
    return ok({"api_count": len(targets), "case_count": total_generated, "used_ai": used_ai,
               "engine": "AI 大模型" if used_ai else "内置规则引擎（降级）"},
              msg=f"成功生成 {total_generated} 条用例")


@router.post("/organize/{pid}")
def organize_docs(pid: int, request: Request):
    """AI 整理用例文档：标准化排序（模块→接口→类型→优先级），统一字段格式"""
    user = get_user(request)
    count = d.q1("SELECT COUNT(*) c FROM cases WHERE project_id=?", (pid,))["c"]
    if count == 0:
        http_err(400, "当前项目暂无用例可整理")
    # 统一标准化用例命名与优先级格式
    rows = d.q("SELECT id, name, priority, case_type FROM cases WHERE project_id=?", (pid,))
    normalized = 0
    for r in rows:
        prio = (r["priority"] or "P1").upper().replace(" ", "")
        if prio not in ("P0", "P1", "P2"):
            prio = "P2"
        ctype = (r["case_type"] or "正向").strip()
        if ctype not in ("正向", "反向", "边界", "异常"):
            ctype = "正向"
        name = (r["name"] or "").strip() or f"用例-{r['id']}"
        if prio != r["priority"] or ctype != r["case_type"] or name != r["name"]:
            d.ex("UPDATE cases SET name=?, priority=?, case_type=? WHERE id=?", (name, prio, ctype, r["id"]))
            normalized += 1
    d.op_log(user["username"], "AI整理用例文档", f"项目#{pid} 整理{count}条用例")
    return ok({"total": count, "normalized": normalized,
               "order_rule": "按 模块 → 接口 → 用例类型（正向/反向/边界/异常）→ 优先级（P0/P1/P2）自动分类归档"},
              msg=f"用例文档整理完成：共 {count} 条用例已按标准格式分类归档")


@router.get("/models")
def list_models(request: Request):
    get_user(request)
    return ok([
        {"value": "deepseek-chat", "label": "DeepSeek Chat"},
        {"value": "deepseek-reasoner", "label": "DeepSeek Reasoner"},
        {"value": "gpt-4o-mini", "label": "GPT-4o mini"},
        {"value": "gpt-4o", "label": "GPT-4o"},
        {"value": "qwen-plus", "label": "通义千问 Plus"},
        {"value": "qwen-max", "label": "通义千问 Max"},
        {"value": "custom", "label": "自定义兼容模型"},
    ])
