# -*- coding: utf-8 -*-
"""端到端冒烟测试：登录 → 建项目 → 建环境 → 上传OpenAPI → AI生成用例 → 执行 → 报告 → 导出"""
import json
import time
import requests

BASE = "http://127.0.0.1:8000"
MOCK = "http://127.0.0.1:8099"

# 绕过环境代理，直连本机服务
_session = requests.Session()
_session.trust_env = False
requests = _session

OPENAPI = {
    "openapi": "3.0.0",
    "info": {"title": "演示业务系统接口", "version": "1.0.0"},
    "paths": {
        "/api/login": {
            "post": {
                "summary": "用户登录",
                "tags": ["用户模块"],
                "requestBody": {"content": {"application/json": {"schema": {
                    "type": "object",
                    "properties": {"username": {"type": "string"}, "password": {"type": "string"}}
                }}}},
                "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}}
            }
        },
        "/api/users": {
            "get": {
                "summary": "查询用户列表",
                "tags": ["用户模块"],
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer"}},
                    {"name": "size", "in": "query", "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}}
            }
        },
        "/api/users/{id}": {
            "get": {
                "summary": "查询用户详情",
                "tags": ["用户模块"],
                "parameters": [{"name": "id", "in": "path", "schema": {"type": "integer"}}],
                "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}}
            }
        },
        "/api/secure/profile": {
            "get": {
                "summary": "查询用户资料(需鉴权)",
                "tags": ["鉴权模块"],
                "responses": {
                    "200": {"content": {"application/json": {"schema": {"type": "object"}}}},
                    "401": {"content": {"application/json": {"schema": {"type": "object"}}}}
                }
            }
        }
    }
}


def call(method, path, token=None, **kw):
    headers = kw.pop("headers", {})
    if token:
        headers["Authorization"] = token
    r = getattr(requests, method)(BASE + path, headers=headers, **kw)
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text[:200]}
    return r.status_code, data


def check(name, cond, extra=""):
    print(("  ✅ " if cond else "  ❌ ") + name + ((" - " + str(extra)) if extra else ""))
    if not cond:
        raise SystemExit(f"测试失败：{name}")


print("=" * 70)
print("AI驱动Web接口自动化测试平台 - 端到端冒烟测试")
print("=" * 70)

# 1. 登录
print("\n[1] 用户登录")
code, d = call("post", "/api/auth/login", json={"username": "admin", "password": "admin123"})
check("登录接口", code == 200 and d["code"] == 0, d.get("msg", ""))
token = d["data"]["token"]

# 2. 项目
print("\n[2] 项目管理")
code, d = call("post", "/api/projects", token, json={"name": "演示项目-用户中心", "description": "端到端测试创建"})
check("创建项目", code == 200 and d["code"] == 0)
code, d = call("get", "/api/projects", token)
pid = [p for p in d["data"] if p["name"] == "演示项目-用户中心"][0]["id"]
check("项目列表查询", code == 200 and len(d["data"]) >= 1, f"项目ID={pid}")

# 3. 环境
print("\n[3] 测试环境配置")
code, d = call("post", f"/api/projects/{pid}/envs", token, json={
    "name": "本地Mock环境", "base_url": MOCK,
    "headers": [{"key": "Authorization", "value": "mock-token-abc"}],
    "timeout": 10, "retry": 1, "is_default": True
})
check("创建环境", code == 200 and d["code"] == 0)
code, d = call("get", f"/api/projects/{pid}/envs", token)
env_id = d["data"][0]["id"]
check("环境列表查询", len(d["data"]) == 1 and d["data"][0]["is_default"] == 1)

# 4. 上传 OpenAPI
print("\n[4] 接口文档解析")
files = {"file": ("demo_api.json", json.dumps(OPENAPI, ensure_ascii=False).encode("utf-8"), "application/json")}
code, d = call("post", f"/api/projects/{pid}/apis/upload", token, files=files)
check("OpenAPI 上传解析", code == 200 and d["code"] == 0, d.get("msg", ""))
print("     " + str(d.get("msg", "")))
code, d = call("get", f"/api/projects/{pid}/apis/all", token)
apis = d["data"]
check("接口列表", len(apis) >= 3, f"解析入库 {len(apis)} 个接口")

# 5. AI 生成用例
print("\n[5] AI 用例生成")
code, d = call("post", "/api/ai/generate", token, json={"project_id": pid, "scope": "all", "gen_type": "full"})
check("批量生成用例", code == 200 and d["code"] == 0, f"生成 {d.get('data', {}).get('case_count', 0)} 条，引擎：{d.get('data', {}).get('engine', '')}")
print("     " + str(d.get("msg", "")))
generated = d["data"]["case_count"]

code, d = call("get", f"/api/projects/{pid}/cases?size=5", token)
check("用例列表查询", d["data"]["total"] == generated, f"总数 {d['data']['total']}")
types = {}
for c in d["data"]["list"]:
    types[c["case_type"]] = types.get(c["case_type"], 0) + 1
print(f"     用例类型分布（首页）: {types}")

# 6. AI 整理文档
print("\n[6] AI 用例文档整理")
code, d = call("post", f"/api/ai/organize/{pid}", token)
check("文档整理", code == 200 and d["code"] == 0, d.get("msg", ""))

# 7. 执行
print("\n[7] 自动化执行")
code, d = call("post", "/api/execution/start", token, json={"project_id": pid, "env_id": env_id, "scope": "all"})
check("启动执行任务", code == 200 and d["code"] == 0)
task_id = d["data"]["task_id"]
for _ in range(60):
    code, d = call("get", f"/api/execution/{task_id}/status?log_after=0", token)
    t = d["data"]["task"]
    if t["status"] != "running":
        break
    time.sleep(1)
check("任务执行完成", t["status"] == "finished",
      f"总{t['total']} 已执行{t['executed']} 成功{t['passed']} 失败{t['failed']} 跳过{t['skipped']} 耗时{t['duration']}s")
code, d = call("get", f"/api/execution/{task_id}/status?log_after=0", token)
check("实时日志采集", len(d["data"]["logs"]) > 0, f"日志 {len(d['data']['logs'])} 条")

# 8. 报告
print("\n[8] 测试报告")
code, d = call("get", f"/api/reports/{task_id}", token)
check("报告详情", code == 200 and d["data"]["task"]["id"] == task_id,
      f"通过率 {d['data']['pass_rate']}% 模块统计 {len(d['data']['module_stats'])} 项")
mod_rates = [(m["module"], str(m["rate"]) + "%") for m in d["data"]["module_stats"]]
print("     模块成功率:", mod_rates)

# 9. 导出
print("\n[9] 文档与报告导出")
for fmt in ("word", "excel", "pdf"):
    r = requests.get(f"{BASE}/api/projects/{pid}/cases/export?fmt={fmt}", headers={"Authorization": token})
    check(f"用例文档 {fmt.upper()} 导出", r.status_code == 200 and len(r.content) > 2000, f"{len(r.content)} bytes")
for fmt in ("html", "excel", "pdf"):
    r = requests.get(f"{BASE}/api/reports/{task_id}/export?fmt={fmt}", headers={"Authorization": token})
    check(f"测试报告 {fmt.upper()} 导出", r.status_code == 200 and len(r.content) > 1000, f"{len(r.content)} bytes")

# 10. 仪表盘
print("\n[10] 首页仪表盘")
code, d = call("get", "/api/dashboard", token)
dd = d["data"]
check("仪表盘统计", dd["projects"] >= 1 and dd["apis"] >= 3 and dd["cases"] >= generated,
      f"项目{dd['projects']} 接口{dd['apis']} 用例{dd['cases']} 近7日通过率{dd['week_rate']}%")

# 11. AI 配置
print("\n[11] AI 配置")
code, d = call("get", "/api/ai/config", token)
check("读取AI配置", code == 200)
code, d = call("post", "/api/ai/config/test", token, json={"model": "deepseek-chat", "api_key": "", "base_url": "https://api.deepseek.com/v1", "timeout": 60})
check("连通性测试(无Key返回明确提示)", code == 200 and d["data"]["success"] is False, d["data"]["message"])

print("\n" + "=" * 70)
print("🎉 全部端到端测试通过！产品核心流程闭环验证成功")
print("=" * 70)
print(f"访问地址：http://127.0.0.1:8000   演示账号：admin / admin123")
