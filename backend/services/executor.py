# -*- coding: utf-8 -*-
"""执行引擎层：自动化 HTTP 请求、自动断言、超时重试、任务调度、日志采集、终止控制"""
import json
import time
import threading
import traceback
import requests as http
from datetime import datetime

import db as d
from utils import jloads, jdumps

# 运行中任务的控制句柄：task_id -> {"stop": False}
_RUNNING = {}
_LOG_SEQ = {}


def _log(task_id, level, msg):
    ts = datetime.now().strftime("%H:%M:%S")
    d.ex("INSERT INTO task_logs(task_id,level,message) VALUES(?,?,?)",
         (task_id, level, f"[{ts}] {msg}"))


def _resolve_env(env, api):
    """环境兜底：未传入环境时，依次取项目默认环境 → 项目首个环境。
    若接口路径本身已是完整 URL（含 http 域名），则无需域名拼接。"""
    path = (api.get("path") or "/")
    if path.startswith("http://") or path.startswith("https://"):
        return env
    if env and (env.get("base_url") or "").strip():
        return env
    pid = api.get("project_id")
    if pid:
        row = d.q1("SELECT * FROM environments WHERE project_id=? ORDER BY is_default DESC, id LIMIT 1", (pid,))
        if row:
            return d.row_to_dict(row)
    return env


def _build_request(api, case, env):
    """合并 环境配置 + 接口默认 + 用例变体 -> 最终请求"""
    env = _resolve_env(env, api)
    env_headers = {}
    for h in (jloads(env.get("headers"), []) if env else []):
        if isinstance(h, dict) and h.get("key"):
            env_headers[h["key"]] = h.get("value", "")
    api_headers = jloads(api.get("headers"), {})
    default_query = jloads(api.get("query_params"), {})
    default_body = jloads(api.get("body"), {})
    override = jloads(case.get("request_data"), {})
    if not isinstance(override, dict):
        override = {}

    api_path = (api.get("path") or "/")
    if api_path.startswith("http://") or api_path.startswith("https://"):
        url = api_path                       # 接口自带完整域名
    else:
        base = (env.get("base_url") or "").strip().rstrip("/") if env else ""
        if not base:
            raise ValueError("未配置测试环境域名（BaseURL），请先在「环境配置」中添加环境并设为默认")
        url = base + (api_path if api_path.startswith("/") else "/" + api_path)
    query = dict(default_query)
    body = dict(default_body) if isinstance(default_body, dict) else {}
    for k, v in override.items():
        # 变体参数：优先视作 body 字段，若命中 query 默认键则放 query
        if k in default_query:
            query[k] = v
        else:
            body[k] = v
    headers = {**env_headers, **api_headers}
    # 用例显式要求移除认证（异常-未授权用例）
    if "未授权" in (case.get("name") or "") or "错误Token" in (case.get("name") or ""):
        headers = {k: v for k, v in headers.items() if k.lower() not in ("authorization", "token", "cookie")}
    return {"method": api["method"].lower(), "url": url, "headers": headers,
            "params": query, "json": body if body else None}


def _run_assertions(expected, resp):
    """执行断言：返回 (passed, results)"""
    results = []
    all_pass = True
    exp_code = expected.get("status_code")
    if exp_code is not None:
        passed = int(resp.status_code) == int(exp_code)
        all_pass = all_pass and passed
        results.append({"type": "状态码断言", "expr": f"HTTP {resp.status_code}",
                        "expected": f"等于 {exp_code}", "passed": passed})
    for a in (expected.get("assertions") or []):
        if not isinstance(a, dict):
            continue
        atype = a.get("type", "")
        expr = a.get("expr", "")
        op = a.get("op", "eq")
        value = a.get("value")
        try:
            if atype == "status_code":
                actual = resp.status_code
            elif atype == "json_path":
                actual = _dig_json(resp.json(), expr)
            elif atype == "contains":
                actual = resp.text
                op = "contains"
            else:
                continue
            passed = _compare(actual, op, value)
            detail = {"type": f"{expr or atype}", "expected": f"{op} {value}", "actual": str(actual)[:120], "passed": passed}
            results.append(detail)
            all_pass = all_pass and passed
        except Exception as e:
            results.append({"type": expr or atype, "expected": f"{op} {value}",
                            "actual": f"断言执行异常: {e}", "passed": False})
            all_pass = False
    return all_pass, results


def _dig_json(data, path):
    if not path:
        return data
    path = path.lstrip("$.")
    cur = data
    for part in path.replace("[", ".[").split("."):
        if not part:
            continue
        if part.startswith("["):
            cur = cur[int(part.strip("[]"))]
        else:
            cur = cur[part]
    return cur


def _compare(actual, op, expected):
    try:
        if op == "eq":
            return str(actual) == str(expected) or actual == expected
        if op == "ne":
            return str(actual) != str(expected)
        if op == "gt":
            return float(actual) > float(expected)
        if op == "lt":
            return float(actual) < float(expected)
        if op == "contains":
            return str(expected) in str(actual)
    except Exception:
        return False
    return False


def _execute_one(task_id, case_row, api_row, env, timeout, retry):
    """执行单条用例，写结果，返回状态"""
    try:
        req = _build_request(api_row, case_row, env)
    except ValueError as e:
        # 环境/URL 配置类问题：快速失败并给出可操作提示
        _log(task_id, "ERROR", f"✗ 用例失败 [{case_row['name']}] {e}")
        d.ex("""INSERT INTO case_results(task_id,case_id,case_name,api_name,module,case_type,status,request_info,response_info,assertions,fail_reason,duration)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
             (task_id, case_row["id"], case_row["name"], api_row.get("name", ""), api_row.get("module", ""),
              case_row["case_type"], "failed", "{}", "{}", "[]", str(e), 0))
        d.ex("UPDATE cases SET last_status='failed' WHERE id=?", (case_row["id"],))
        return "failed"
    _log(task_id, "INFO",
         f"▶ 执行用例 [{case_row['name']}] {req['method'].upper()} {req['url']} 参数: {json.dumps(req['params'], ensure_ascii=False)}")
    attempts = retry + 1
    last_err, resp = "", None
    start = time.time()
    for i in range(attempts):
        try:
            resp = http.request(req["method"], req["url"], headers=req["headers"],
                                params=req["params"], json=req["json"], timeout=timeout)
            break
        except Exception as e:
            last_err = str(e)
            if i < attempts - 1:
                _log(task_id, "WARN", f"请求失败正在重试({i + 1}/{retry}): {last_err}")
    duration = round(time.time() - start, 3)

    status, fail_reason, assertion_results, resp_info = "failed", "", [], {}
    if resp is None:
        fail_reason = f"请求异常: {last_err}"
        _log(task_id, "ERROR", f"✗ 用例失败 [{case_row['name']}] {fail_reason}")
    else:
        try:
            body = resp.json()
        except Exception:
            body = None
        resp_info = {"status_code": resp.status_code,
                     "headers": {k: v for k, v in list(resp.headers.items())[:15]},
                     "body": (body if body is not None else resp.text[:2000])}
        expected = jloads(case_row["expected"], {})
        all_pass, assertion_results = _run_assertions(expected, resp)
        status = "passed" if all_pass else "failed"
        if not all_pass:
            fails = [r for r in assertion_results if not r.get("passed")]
            fail_reason = "; ".join(
                f"{r.get('type')}: 期望 {r.get('expected')} 实际 {r.get('actual', '')}" for r in fails)[:500]
        _log(task_id, "INFO" if all_pass else "ERROR",
             f"{'✓ 用例通过' if all_pass else '✗ 用例失败'} [{case_row['name']}] HTTP {resp.status_code} 耗时{duration}s")
        if not all_pass:
            _log(task_id, "INFO", f"  断言详情: {json.dumps(assertion_results, ensure_ascii=False)[:400]}")

    d.ex("""INSERT INTO case_results(task_id,case_id,case_name,api_name,module,case_type,status,request_info,response_info,assertions,fail_reason,duration)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
         (task_id, case_row["id"], case_row["name"], api_row["name"], api_row["module"],
          case_row["case_type"], status, jdumps(req), jdumps(resp_info),
          jdumps(assertion_results), fail_reason, duration))
    d.ex("UPDATE cases SET last_status=? WHERE id=?", (status, case_row["id"]))
    return status


def start_task(task_id: int):
    th = threading.Thread(target=_run_task, args=(task_id,), daemon=True)
    th.start()


def _run_task(task_id: int):
    _RUNNING[task_id] = {"stop": False}
    task = d.q1("SELECT * FROM tasks WHERE id=?", (task_id,))
    if not task:
        return
    env = d.q1("SELECT * FROM environments WHERE id=?", (task["env_id"],)) if task["env_id"] else None
    env = d.row_to_dict(env) if env else None
    if env is None:
        # 任务未指定环境（如用例页快速执行），回退到该项目的默认/首个环境
        row = d.q1("SELECT * FROM environments WHERE project_id=? ORDER BY is_default DESC, id LIMIT 1",
                   (task["project_id"],))
        env = d.row_to_dict(row) if row else None
    case_ids = jloads(task["case_ids"], [])
    d.ex("UPDATE tasks SET status='running' WHERE id=?", (task_id,))
    if env:
        d.ex("UPDATE tasks SET env_id=?, env_name=? WHERE id=?", (env["id"], env["name"], task_id))
        env_desc = f"{env['name']}（{env['base_url'] or '未填域名'}）"
    else:
        env_desc = "未配置环境（仅接口路径为完整 URL 时可用）"
    _log(task_id, "INFO", f"任务启动：共 {len(case_ids)} 条用例")
    _log(task_id, "INFO", f"执行环境：{env_desc}　超时 {(env or {}).get('timeout', 10)}s　"
                          f"重试 {(env or {}).get('retry', 0)}次")
    if not env:
        _log(task_id, "WARN", "当前项目未配置测试环境，仅接口路径为完整 URL（http开头）时才能正常请求")
    t0 = time.time()
    for idx, cid in enumerate(case_ids):
        if _RUNNING.get(task_id, {}).get("stop"):
            _log(task_id, "WARN", "任务被用户手动终止")
            for rid in case_ids[idx:]:
                cr = d.q1("SELECT * FROM cases WHERE id=?", (rid,))
                if cr:
                    d.ex("""INSERT INTO case_results(task_id,case_id,case_name,api_name,module,case_type,status,request_info,response_info,assertions,fail_reason,duration)
                            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                         (task_id, rid, cr["name"], "", "", cr["case_type"], "skipped", "{}", "{}", "[]", "任务终止跳过", 0))
            d.ex("UPDATE tasks SET status='stopped', finished_at=datetime('now','localtime'), duration=? WHERE id=?",
                 (round(time.time() - t0, 2), task_id))
            _RUNNING.pop(task_id, None)
            return
        case_row = d.q1("SELECT * FROM cases WHERE id=?", (cid,))
        api_row = d.q1("SELECT * FROM apis WHERE id=?", (case_row["api_id"],)) if case_row else None
        if not case_row or not api_row:
            d.ex("UPDATE tasks SET executed=executed+1, skipped=skipped+1 WHERE id=?", (task_id,))
            continue
        timeout = (env or {}).get("timeout") or 10
        retry = (env or {}).get("retry") or 0
        try:
            status = _execute_one(task_id, d.row_to_dict(case_row), d.row_to_dict(api_row), env, timeout, retry)
            col = {"passed": "passed", "failed": "failed"}.get(status, "skipped")
            d.ex(f"UPDATE tasks SET executed=executed+1, {col}={col}+1 WHERE id=?", (task_id,))
        except Exception as e:
            traceback.print_exc()
            _log(task_id, "ERROR", f"用例执行异常: {e}")
            d.ex("UPDATE tasks SET executed=executed+1, failed=failed+1 WHERE id=?", (task_id,))
    duration = round(time.time() - t0, 2)
    d.ex("UPDATE tasks SET status='finished', finished_at=datetime('now','localtime'), duration=? WHERE id=?",
         (duration, task_id))
    t = d.q1("SELECT * FROM tasks WHERE id=?", (task_id,))
    _log(task_id, "INFO",
         f"任务完成：总计{t['total']} 成功{t['passed']} 失败{t['failed']} 跳过{t['skipped']} 耗时{duration}s")
    _RUNNING.pop(task_id, None)


def stop_task(task_id: int) -> bool:
    if task_id in _RUNNING:
        _RUNNING[task_id]["stop"] = True
        return True
    return False
