# -*- coding: utf-8 -*-
"""AI 能力层：OpenAI 兼容大模型对接 + 规则引擎兜底生成"""
import json
import re
import requests as http
import db as d
from utils import jloads

PROMPT = """你是一名资深接口测试用例设计师。请根据下面的接口信息，生成标准化接口测试用例。

接口信息：
{api_info}

生成要求：
1. 用例类型覆盖：{types_desc}
2. 每条用例包含字段：name(用例名称，中文，简洁明了), case_type(正向/反向/边界/异常), priority(P0/P1/P2), steps(测试步骤描述), request_data(该用例的请求参数，object：query参数与body参数平铺), expected(预期结果，object：status_code 数字 + assertions 数组，每项为 {{"type":"status_code"|"json_path"|"contains","expr":"表达式/字段名","op":"eq|ne|gt|lt|contains","value":"期望值"}})
3. request_data 中只包含与默认参数有差异的字段（用例即变体）
4. 严格输出 JSON 数组，不要输出任何其他文字、不要 markdown 代码块

请输出用例 JSON 数组："""

TYPES_DESC = {
    "positive": "仅正向用例：正常合法参数，验证接口正常响应（生成1-2条）",
    "full": "全量用例：正向用例(1-2条)、反向用例(参数为空/缺失必填/格式错误/超长/非法值，3-4条)、边界用例(最大值/最小值/临界值，1-2条)、异常用例(未授权/超时/重复请求，1-2条)",
}


def get_config():
    r = d.q1("SELECT * FROM ai_config WHERE id=1")
    cfg = d.row_to_dict(r) or {}
    return {"model": cfg.get("model") or "deepseek-chat",
            "api_key": cfg.get("api_key") or "",
            "base_url": (cfg.get("base_url") or "https://api.deepseek.com/v1").rstrip("/"),
            "timeout": cfg.get("timeout") or 60}


def test_connection(cfg=None):
    cfg = cfg or get_config()
    if not cfg["api_key"]:
        return False, "未配置 API Key"
    try:
        resp = http.post(
            cfg["base_url"] + "/chat/completions",
            headers={"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"},
            json={"model": cfg["model"],
                  "messages": [{"role": "user", "content": "回复：OK"}],
                  "max_tokens": 8, "temperature": 0},
            timeout=min(cfg["timeout"], 30))
        if resp.status_code == 200:
            return True, "连接成功"
        return False, f"连接失败：HTTP {resp.status_code} {resp.text[:200]}"
    except Exception as e:
        return False, f"连接失败：{str(e)[:200]}"


def _extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(json)?|```$", "", text, flags=re.M).strip()
    m = re.search(r"[\[{].*[\]}]", text, flags=re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        try:
            return json.loads(text)
        except Exception:
            return None


def generate_cases_for_api(api: dict, gen_type: str = "full"):
    """返回 (cases, used_ai, note)"""
    cfg = get_config()
    if cfg["api_key"]:
        cases = _generate_by_llm(api, gen_type, cfg)
        if cases:
            return cases, True, "AI 大模型生成"
    return _generate_by_rules(api, gen_type), False, "规则引擎生成（未配置 AI Key，已自动降级）"


def _generate_by_llm(api, gen_type, cfg):
    api_info = json.dumps({
        "接口名称": api["name"], "请求方式": api["method"], "路径": api["path"], "模块": api["module"],
        "默认Query参数": jloads(api.get("query_params"), {}),
        "默认请求体": jloads(api.get("body"), {}),
        "响应模型": jloads(api.get("response_schema"), {}),
    }, ensure_ascii=False)
    try:
        resp = http.post(
            cfg["base_url"] + "/chat/completions",
            headers={"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"},
            json={"model": cfg["model"],
                  "messages": [{"role": "user",
                                "content": PROMPT.format(api_info=api_info, types_desc=TYPES_DESC[gen_type])}],
                  "temperature": 0.2},
            timeout=cfg["timeout"])
        if resp.status_code != 200:
            return None
        content = resp.json()["choices"][0]["message"]["content"]
        data = _extract_json(content)
        cases = []
        if isinstance(data, list):
            for c in data:
                if not isinstance(c, dict) or not c.get("name"):
                    continue
                cases.append({
                    "name": str(c["name"])[:120],
                    "case_type": c.get("case_type", "正向"),
                    "priority": c.get("priority", "P1"),
                    "steps": str(c.get("steps", "")),
                    "request_data": c.get("request_data") or {},
                    "expected": c.get("expected") or {"status_code": 200, "assertions": []},
                })
        return cases or None
    except Exception:
        return None


# ---------------- 规则引擎兜底（无 AI Key 也可完整使用产品） ----------------
def _generate_by_rules(api, gen_type):
    from services.parser import params_of_api
    fields = params_of_api(api)
    cases = []

    def add(name, ctype, prio, steps, req_data, status_code, assertions=None):
        cases.append({"name": name, "case_type": ctype, "priority": prio, "steps": steps,
                      "request_data": req_data,
                      "expected": {"status_code": status_code, "assertions": assertions or []}})

    # 正向：默认参数
    valid = {f["name"]: f["value"] for f in fields}
    add(f"正向-使用默认合法参数请求 {api['name']}", "正向", "P0",
        f"以默认合法参数请求 {api['method']} {api['path']}，验证接口正常响应", valid, 200,
        [{"type": "status_code", "expr": "", "op": "eq", "value": 200}])
    if gen_type == "positive":
        return cases

    # 反向：每个字段做空值/非法值变体
    for f in fields[:4]:
        fname, ftype = f["name"], f["type"]
        empty = {fname: "" if ftype == "str" else None}
        add(f"反向-参数 {fname} 为空", "反向", "P1",
            f"请求时将参数 {fname} 置空，验证接口参数校验", empty, 400)
        add(f"反向-参数 {fname} 类型非法", "反向", "P2",
            f"请求时将参数 {fname} 传入非法类型值，验证接口异常处理", {fname: "@@非法值123"}, 400)
    # 反向：必填全缺失
    if fields:
        add(f"反向-缺失全部必填参数", "反向", "P1", "请求时不携带任何参数，验证接口必填校验", {}, 400)
    # 反向：超长
    if fields:
        f0 = fields[0]
        add(f"反向-参数 {f0['name']} 超长输入", "反向", "P2",
            f"参数 {f0['name']} 传入超长字符串（1000字符），验证字段长度校验",
            {f0["name"]: "x" * 1000}, 400)
    # 边界：数值型字段
    num_fields = [f for f in fields if f["type"] in ("int", "float")]
    for f in num_fields[:2]:
        add(f"边界-参数 {f['name']} 取最小值", "边界", "P2",
            f"参数 {f['name']} 取数值最小边界值 0 验证", {f["name"]: 0}, 200)
        add(f"边界-参数 {f['name']} 取最大值", "边界", "P2",
            f"参数 {f['name']} 取数值最大边界值 999999 验证", {f["name"]: 999999}, 200)
    # 异常：未授权
    add(f"异常-未授权访问 {api['name']}", "异常", "P1",
        "请求时不携带认证信息，验证接口鉴权拦截", {}, 401)
    add(f"异常-错误Token访问", "异常", "P2",
        "请求时携带无效Token，验证鉴权校验", {}, 401)
    return cases
