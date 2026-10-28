# -*- coding: utf-8 -*-
"""演示数据初始化：创建一个完整的可体验项目（项目+环境+接口+AI用例+一次执行报告）"""
import json
import sys
import os
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE = "http://127.0.0.1:8000"
MOCK = "http://127.0.0.1:8099"

s = requests.Session()
s.trust_env = False

OPENAPI = {
    "openapi": "3.0.0",
    "info": {"title": "用户中心系统接口", "version": "1.0.0"},
    "paths": {
        "/api/login": {
            "post": {
                "summary": "用户登录", "tags": ["用户模块"],
                "requestBody": {"content": {"application/json": {"schema": {
                    "type": "object",
                    "properties": {"username": {"type": "string"}, "password": {"type": "string"}}}}}},
                "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}}
            }
        },
        "/api/users": {
            "get": {
                "summary": "查询用户列表（分页）", "tags": ["用户模块"],
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer"}},
                    {"name": "size", "in": "query", "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}}
            }
        },
        "/api/users/{id}": {
            "get": {
                "summary": "查询用户详情", "tags": ["用户模块"],
                "parameters": [{"name": "id", "in": "path", "schema": {"type": "integer"}}],
                "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}}
            }
        },
        "/api/secure/profile": {
            "get": {
                "summary": "查询用户资料（需鉴权）", "tags": ["鉴权模块"],
                "responses": {
                    "200": {"content": {"application/json": {"schema": {"type": "object"}}}},
                    "401": {"content": {"application/json": {"schema": {"type": "object"}}}}
                }
            }
        }
    }
}


def main():
    r = s.post(BASE + "/api/auth/login", json={"username": "admin", "password": "admin123"}).json()
    token = r["data"]["token"]
    H = {"Authorization": token}

    r = s.post(BASE + "/api/projects", headers=H,
               json={"name": "用户中心接口测试项目", "description": "演示项目：验证登录、用户查询、鉴权等核心接口"}).json()
    # 取回新建项目 ID
    projects = s.get(BASE + "/api/projects", headers=H).json()["data"]
    pid = [p for p in projects if p["name"] == "用户中心接口测试项目"][0]["id"]
    print("✓ 创建演示项目，ID =", pid)

    s.post(f"{BASE}/api/projects/{pid}/envs", headers=H, json={
        "name": "本地测试环境", "base_url": MOCK,
        "headers": [{"key": "Authorization", "value": "mock-token-abc"}],
        "timeout": 10, "retry": 1, "is_default": True
    })
    s.post(f"{BASE}/api/projects/{pid}/envs", headers=H, json={
        "name": "预发环境", "base_url": "https://staging.example.com",
        "headers": [{"key": "Authorization", "value": "Bearer xxx"}],
        "timeout": 15, "retry": 2, "is_default": False
    })
    print("✓ 创建 2 套测试环境（本地测试环境为默认）")

    files = {"file": ("用户中心_openapi.json", json.dumps(OPENAPI, ensure_ascii=False).encode("utf-8"), "application/json")}
    r = s.post(f"{BASE}/api/projects/{pid}/apis/upload", headers=H, files=files).json()
    print("✓ 接口文档解析：", r["msg"])

    r = s.post(BASE + "/api/ai/generate", headers=H,
               json={"project_id": pid, "scope": "all", "gen_type": "full"}).json()
    print("✓ AI 用例生成：", r["msg"], "|", r["data"]["engine"])

    r = s.post(f"{BASE}/api/ai/organize/{pid}", headers=H).json()
    print("✓ 用例文档整理：", r["msg"])

    r = s.post(BASE + "/api/execution/start", headers=H,
               json={"project_id": pid, "scope": "all", "task_name": "用户中心全量回归测试"}).json()
    task_id = r["data"]["task_id"]
    for _ in range(60):
        st = s.get(f"{BASE}/api/execution/{task_id}/status", headers=H).json()["data"]["task"]
        if st["status"] != "running":
            break
        time.sleep(1)
    rate = round(st["passed"] / st["executed"] * 100, 1) if st["executed"] else 0
    print(f"✓ 执行完成：总{st['total']} 成功{st['passed']} 失败{st['failed']} 通过率{rate}% 耗时{st['duration']}s")

    # ---------- 演示项目 2：多格式文档（PDF / HTML）解析 ----------
    samples = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "samples")
    pdf_html = [("接口文档_用户中心.pdf", "pdf"), ("接口文档_订单服务.html", "html"), ("接口文档_商品模块.html", "html")]
    if os.path.isdir(samples) and all(os.path.exists(os.path.join(samples, f)) for f, _ in pdf_html):
        r = s.post(BASE + "/api/projects", headers=H,
                   json={"name": "多格式文档解析演示", "description": "演示 PDF / HTML 格式接口文档的智能解析与用例生成"}).json()
        projects = s.get(BASE + "/api/projects", headers=H).json()["data"]
        pid2 = [p for p in projects if p["name"] == "多格式文档解析演示"][0]["id"]
        s.post(f"{BASE}/api/projects/{pid2}/envs", headers=H, json={
            "name": "本地Mock环境", "base_url": MOCK,
            "headers": [{"key": "Authorization", "value": "mock-token-abc"}],
            "timeout": 10, "retry": 1, "is_default": True
        })
        total = 0
        for fname, kind in pdf_html:
            with open(os.path.join(samples, fname), "rb") as fp:
                rr = s.post(f"{BASE}/api/projects/{pid2}/apis/upload", headers=H,
                            files={"file": (fname, fp.read())}).json()
            cnt = (rr.get("data") or {}).get("inserted", 0)
            total += cnt
            print(f"✓ {kind.upper()} 文档解析 {fname}：{rr.get('msg', '')}")
        print(f"✓ 多格式文档共入库 {total} 个接口")
        if total:
            r = s.post(BASE + "/api/ai/generate", headers=H,
                       json={"project_id": pid2, "scope": "all", "gen_type": "full"}).json()
            print("✓ AI 用例生成：", r["msg"])
            print("  （该项目接口来自真实业务文档，未指向 Mock 服务，故不自动执行；"
                  "配置好环境后可在「测试执行」手动运行）")

    print("\n演示数据初始化完成！")
    print("访问 http://127.0.0.1:8000  账号 admin / admin123")
    print("提示：进入项目后即可在「测试执行」页面重新执行，或在「用例管理」中执行单条用例查看实时日志。")


if __name__ == "__main__":
    main()
