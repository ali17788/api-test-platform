# -*- coding: utf-8 -*-
"""端到端验证：
  1. PDF / HTML / Markdown 接口文档上传解析
  2. AI 生成用例
  3. 用例页执行 URL 域名拼接（回归此前的「未拼接域名」缺陷）
  4. 无环境项目的执行兜底提示
"""
import json
import os
import time

import requests

BASE = "http://127.0.0.1:8000"
SAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "samples")
s = requests.Session()
s.trust_env = False


def login():
    r = s.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin123"})
    tok = r.json()["data"]["token"]
    s.headers.update({"Authorization": tok})
    return tok


def new_project(name):
    r = s.post(f"{BASE}/api/projects", json={"name": name, "description": "回归验证"})
    return r.json()["data"]["id"]


def upload(pid, filename):
    path = os.path.join(SAMPLES, filename)
    with open(path, "rb") as f:
        r = s.post(f"{BASE}/api/projects/{pid}/apis/upload",
                   files={"file": (filename, f.read())})
    j = r.json()
    return r.status_code, (j.get("data") if j.get("code") == 0 else j.get("msg"))


def wait_task(task_id, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = s.get(f"{BASE}/api/execution/{task_id}/status").json()["data"]
        if not r["running"]:
            return r["task"]
        time.sleep(0.6)
    return None


def main():
    print("=" * 68)
    login()

    # ---------- 1. 上传解析（PDF / HTML / Markdown）----------
    pid = new_project("回归验证-文档解析")
    # 造一个不支持格式的样本
    with open(os.path.join(SAMPLES, "接口清单.xlsx"), "wb") as f:
        f.write(b"\x50\x4b\x03\x04 not a real xlsx")
    print("[1] 上传解析")
    for fn in ["接口文档_用户中心.pdf", "接口文档_订单服务.html", "接口文档_商品模块.html",
               "接口文档_用户中心.md", "接口清单.xlsx"]:
        code, res = upload(pid, fn)
        if isinstance(res, dict):
            print(f"    ✓ {fn:<28} 解析 {res['parsed']} 个，入库 {res['inserted']} 个")
        else:
            print(f"    {'✗' if '不支持' in str(res) else '!'} {fn:<28} {res}")

    apis = s.get(f"{BASE}/api/projects/{pid}/apis/all").json()["data"]
    print(f"    项目接口总数：{len(apis)}")
    for a in apis:
        print(f"      - {a['method']:<6} {a['path']:<24} {a['name']}  [{a['module']}]")

    # ---------- 2. 环境 + AI 生成用例 ----------
    print("[2] 环境配置与 AI 生成用例")
    s.post(f"{BASE}/api/projects/{pid}/envs", json={
        "name": "本地Mock环境", "base_url": "http://127.0.0.1:8099",
        "headers": [{"key": "Authorization", "value": "mock"}],
        "timeout": 10, "retry": 1, "is_default": True})
    g = s.post(f"{BASE}/api/ai/generate", json={"project_id": pid, "scope": "all", "gen_type": "full"}).json()
    print("    ", g["msg"], "| 引擎:", g["data"]["engine"], "| 用例数:", g["data"]["case_count"])

    # ---------- 3. 用例页执行（域名拼接回归）----------
    print("[3] 用例页执行：URL 域名拼接验证")
    case_ids = [c["id"] for c in s.get(f"{BASE}/api/projects/{pid}/cases/all").json()["data"]][:6]
    r = s.post(f"{BASE}/api/cases/run", json={"ids": case_ids})
    if r.json().get("code") != 0:
        print("    启动失败：", r.json().get("msg"))
    else:
        task_id = r.json()["data"]["task_id"]
        task = wait_task(task_id)
        rep = s.get(f"{BASE}/api/reports/{task_id}").json()["data"]
        print(f"    任务#{task_id} 环境={task and task.get('env_name')} "
              f"执行{task['executed']} 通过{task['passed']} 失败{task['failed']}")
        bad = 0
        for res in rep["results"][:6]:
            req = json.loads(res["request_info"]) if isinstance(res["request_info"], str) else res["request_info"]
            resp = json.loads(res["response_info"]) if isinstance(res["response_info"], str) else res["response_info"]
            url = req.get("url", "")
            code = (resp or {}).get("status_code", "-")
            ok = url.startswith("http")
            bad += 0 if ok else 1
            print(f"      {'✓' if ok else '✗'} {url:<52} HTTP {code} "
                  f"{'通过' if res['status'] == 'passed' else '失败'} {res['fail_reason'][:40]}")
        print("    结论：", "全部 URL 已正确拼接域名" if bad == 0 else f"仍有 {bad} 条 URL 缺少域名")

    # ---------- 4. 无环境项目兜底 ----------
    print("[4] 无环境项目执行兜底")
    pid2 = new_project("回归验证-无环境")
    s.post(f"{BASE}/api/projects/{pid2}/apis", json={"name": "示例接口", "method": "GET",
                                                     "path": "/api/demo", "module": "默认模块"})
    aid = s.get(f"{BASE}/api/projects/{pid2}/apis/all").json()["data"][0]["id"]
    s.post(f"{BASE}/api/projects/{pid2}/cases", json={"api_id": aid, "name": "示例接口-正向-正常请求",
                                                      "case_type": "正向", "priority": "P1"})
    cid = s.get(f"{BASE}/api/projects/{pid2}/cases/all").json()["data"][0]["id"]
    r = s.post(f"{BASE}/api/cases/run", json={"ids": [cid]})
    print("    ", "预期拦截 →", r.json().get("msg"))

    # 补上环境后可执行
    s.post(f"{BASE}/api/projects/{pid2}/envs", json={"name": "补录环境", "base_url": "http://127.0.0.1:8099",
                                                     "timeout": 10, "retry": 0, "is_default": True})
    r = s.post(f"{BASE}/api/cases/run", json={"ids": [cid]})
    if r.json().get("code") == 0:
        t = wait_task(r.json()["data"]["task_id"])
        print(f"    补录环境后执行成功：HTTP 请求已发出（执行{t['executed']}条）")
    print("=" * 68)


if __name__ == "__main__":
    main()
