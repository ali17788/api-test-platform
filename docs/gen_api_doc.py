# -*- coding: utf-8 -*-
"""AI驱动Web接口自动化测试平台 —— 后端接口文档生成器

从统一的接口元数据生成三份产物：
  1. openapi.json   —— OpenAPI 3.0 规格（可直接导入 Postman / Apifox / Swagger）
  2. 接口API文档.md —— 规范中文接口文档
  3. 接口API文档.html —— 可视化阅读版
"""
import json
import os
from collections import OrderedDict

OUT = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 统一元数据
# ============================================================
INFO = OrderedDict([
    ("title", "AI驱动Web接口自动化测试平台 API"),
    ("version", "1.0.0"),
    ("base_url", "http://127.0.0.1:8000"),
    ("desc", "零代码 · AI全自动 · 接口自动化测试平台后端服务。"
             "覆盖项目管理、环境配置、接口管理、AI用例生成、用例管理、测试执行、测试报告、仪表盘统计、用户与权限九大能力域。"),
])

TAGS = [
    ("认证管理", "登录鉴权与当前用户信息"),
    ("项目管理", "测试项目的增删改查与概览统计"),
    ("环境配置", "项目下的多套测试环境（域名/请求头/超时/重试）"),
    ("接口管理", "被测接口 CRUD、OpenAPI/Swagger/Postman 文档解析导入"),
    ("用例管理", "测试用例 CRUD、多条件筛选、批量执行与删除"),
    ("AI 能力", "AI 配置与连通性测试、AI 用例生成、用例文档智能整理"),
    ("测试执行", "执行任务启动、实时状态/日志轮询、终止、失败重跑"),
    ("测试报告", "报告列表/详情、HTML/Excel/PDF 导出、删除"),
    ("仪表盘", "首页全局统计数据聚合"),
    ("用户与权限", "菜单目录、角色管理（菜单权限模板）与用户管理（分配角色与菜单权限）"),
    ("系统服务", "健康检查、操作日志、用例文档导出"),
]

# 通用响应外壳示例
def wrap(data, msg="ok"):
    return {"code": 0, "msg": msg, "data": data}

# ============================================================
# 接口清单
# ============================================================
E = []
def ep(method, path, tag, name, desc, auth=True, path_params=None, query=None,
       body=None, resp=None, resp_msg="操作成功", notes=None, binary=False):
    E.append(dict(method=method, path=path, tag=tag, name=name, desc=desc, auth=auth,
                  path_params=path_params or [], query=query or [], body=body,
                  resp=resp if resp is not None else {}, resp_msg=resp_msg,
                  notes=notes or [], binary=binary))

def P(name, typ="string", desc="", required=False, default=None, enum=None):
    d = {"name": name, "type": typ, "desc": desc, "required": required}
    if default is not None:
        d["default"] = default
    if enum:
        d["enum"] = enum
    return d

def body_schema(props, required=None, desc=""):
    return {"desc": desc, "props": props, "required": required or []}

# ---------------- 认证管理 ----------------
ep("POST", "/api/auth/login", "认证管理", "用户登录",
   "校验用户名密码，成功后下发 Token，后续请求需在请求头携带。",
   auth=False,
   body=body_schema([P("username", "string", "用户名", True),
                     P("password", "string", "密码", True)],
                    ["username", "password"]),
   resp=wrap({"token": "8f3c...a91e2b", "username": "admin", "role": "admin",
              "role_name": "超级管理员",
              "menus": ["dashboard","projects","envs","apis","ai-generate","cases","execution","reports","ai-config","users"]}),
   resp_msg="登录成功",
   notes=["初始账号：admin / admin123", "Token 存于服务端 tokens 表，登出即失效",
          "role_name 为角色名称，menus 为当前用户实际拥有的菜单权限 key 列表"])

ep("POST", "/api/auth/logout", "认证管理", "退出登录",
   "销毁当前 Token。",
   resp=wrap(None, "已退出登录"), resp_msg="已退出登录")

ep("GET", "/api/auth/me", "认证管理", "获取当前用户",
   "返回当前登录用户的用户名、角色名称与实际菜单权限。",
   resp=wrap({"username": "admin", "role": "admin", "role_name": "超级管理员",
              "menus": ["dashboard","projects","envs","apis","ai-generate","cases","execution","reports","ai-config","users"]}))

# ---------------- 项目管理 ----------------
ep("GET", "/api/projects", "项目管理", "项目列表",
   "返回全部项目，并附带每个项目的接口数、用例数。",
   query=[P("keyword", "string", "项目名称模糊搜索", False, "")],
   resp=wrap([{"id": 1, "name": "电商中台接口", "description": "订单/用户/商品",
               "owner": "admin", "api_count": 4, "case_count": 28, "created_at": "2026-10-27 11:20:03"}]))

ep("POST", "/api/projects", "项目管理", "创建项目",
   "新建测试项目，创建者为当前登录用户。",
   body=body_schema([P("name", "string", "项目名称", True),
                     P("description", "string", "项目描述", False, "")], ["name"]),
   resp=wrap({"id": 1}, "项目创建成功"), resp_msg="项目创建成功")

ep("PUT", "/api/projects/{pid}", "项目管理", "编辑项目",
   "修改项目名称与描述。",
   path_params=[P("pid", "integer", "项目ID", True)],
   body=body_schema([P("name", "string", "项目名称", True),
                     P("description", "string", "项目描述", False, "")], ["name"]),
   resp=wrap(None, "项目更新成功"), resp_msg="项目更新成功")

ep("DELETE", "/api/projects/{pid}", "项目管理", "删除项目",
   "删除项目，级联清除该项目下的环境、接口、用例与执行任务。",
   path_params=[P("pid", "integer", "项目ID", True)],
   resp=wrap(None, "项目已删除"), resp_msg="项目已删除",
   notes=["危险操作：级联删除不可恢复"])

ep("GET", "/api/projects/{pid}/overview", "项目管理", "项目概览",
   "返回项目基本信息与接口数、用例数、环境数。",
   path_params=[P("pid", "integer", "项目ID", True)],
   resp=wrap({"project": {"id": 1, "name": "电商中台接口", "description": "订单/用户/商品", "owner": "admin"},
              "api_count": 4, "case_count": 28, "env_count": 2}))

# ---------------- 环境配置 ----------------
ep("GET", "/api/projects/{pid}/envs", "环境配置", "环境列表",
   "返回项目下所有测试环境，默认环境排在首位。",
   path_params=[P("pid", "integer", "项目ID", True)],
   resp=wrap([{"id": 1, "project_id": 1, "name": "本地Mock环境", "base_url": "http://127.0.0.1:8099",
               "headers": [{"key": "Authorization", "value": "mock"}],
               "timeout": 10, "retry": 1, "is_default": 1}]))

ep("POST", "/api/projects/{pid}/envs", "环境配置", "创建环境",
   "新增测试环境；若设为默认环境，会自动取消该项目下其它环境的默认标记。",
   path_params=[P("pid", "integer", "项目ID", True)],
   body=body_schema([P("name", "string", "环境名称", True),
                     P("base_url", "string", "接口域名/BaseURL", True),
                     P("headers", "array<object>", "全局请求头 [{\"key\",\"value\"}]", False, []),
                     P("timeout", "integer", "单请求超时（秒）", False, 10),
                     P("retry", "integer", "失败重试次数", False, 0),
                     P("is_default", "boolean", "是否为默认环境", False, False)],
                    ["name", "base_url"]),
   resp=wrap({"id": 1}, "环境创建成功"), resp_msg="环境创建成功")

ep("PUT", "/api/envs/{eid}", "环境配置", "编辑环境",
   "修改指定环境配置。",
   path_params=[P("eid", "integer", "环境ID", True)],
   body=body_schema([P("name", "string", "环境名称", True),
                     P("base_url", "string", "接口域名/BaseURL", True),
                     P("headers", "array<object>", "全局请求头", False, []),
                     P("timeout", "integer", "超时（秒）", False, 10),
                     P("retry", "integer", "重试次数", False, 0),
                     P("is_default", "boolean", "默认环境", False, False)],
                    ["name", "base_url"]),
   resp=wrap(None, "环境更新成功"), resp_msg="环境更新成功")

ep("DELETE", "/api/envs/{eid}", "环境配置", "删除环境",
   "删除指定测试环境。",
   path_params=[P("eid", "integer", "环境ID", True)],
   resp=wrap(None, "环境已删除"), resp_msg="环境已删除")

# ---------------- 接口管理 ----------------
ep("GET", "/api/projects/{pid}/apis", "接口管理", "接口列表（分页）",
   "分页返回项目下接口，支持名称/路径模糊搜索。",
   path_params=[P("pid", "integer", "项目ID", True)],
   query=[P("keyword", "string", "名称或路径模糊搜索", False, ""),
          P("page", "integer", "页码", False, 1),
          P("size", "integer", "每页条数", False, 10)],
   resp=wrap({"total": 4, "list": [
       {"id": 1, "project_id": 1, "name": "查询用户列表", "method": "GET", "path": "/api/users",
        "module": "用户管理", "headers": {}, "query_params": {"page": 1, "size": 10},
        "body": {}, "response_schema": {"code": 0, "data": {"total": 100}}}]}))

ep("GET", "/api/projects/{pid}/apis/all", "接口管理", "接口全量列表",
   "不分页返回项目下全部接口，供下拉选择/批量操作使用。",
   path_params=[P("pid", "integer", "项目ID", True)],
   resp=wrap([{"id": 1, "name": "查询用户列表", "method": "GET", "path": "/api/users", "module": "用户管理"}]))

ep("GET", "/api/apis/{aid}", "接口管理", "接口详情",
   "返回单个接口的完整定义（请求头/查询参数/请求体/响应结构）。",
   path_params=[P("aid", "integer", "接口ID", True)],
   resp=wrap({"id": 1, "name": "查询用户列表", "method": "GET", "path": "/api/users",
              "module": "用户管理", "headers": {}, "query_params": {}, "body": {}, "response_schema": {}}))

ep("POST", "/api/projects/{pid}/apis", "接口管理", "新增接口",
   "手动录入被测接口定义。",
   path_params=[P("pid", "integer", "项目ID", True)],
   body=body_schema([P("name", "string", "接口名称", True),
                     P("method", "string", "请求方法", False, "GET", ["GET", "POST", "PUT", "DELETE", "PATCH"]),
                     P("path", "string", "接口路径", False, "/"),
                     P("module", "string", "所属模块", False, "默认模块"),
                     P("headers", "object", "请求头", False, {}),
                     P("query_params", "object", "查询参数", False, {}),
                     P("body", "object", "请求体", False, {}),
                     P("response_schema", "object", "响应结构", False, {})], ["name"]),
   resp=wrap({"id": 1}, "接口创建成功"), resp_msg="接口创建成功")

ep("PUT", "/api/apis/{aid}", "接口管理", "编辑接口",
   "修改接口定义。",
   path_params=[P("aid", "integer", "接口ID", True)],
   body=body_schema([P("name", "string", "接口名称", True),
                     P("method", "string", "请求方法", False, "GET"),
                     P("path", "string", "接口路径", False, "/"),
                     P("module", "string", "所属模块", False, "默认模块"),
                     P("headers", "object", "请求头", False, {}),
                     P("query_params", "object", "查询参数", False, {}),
                     P("body", "object", "请求体", False, {}),
                     P("response_schema", "object", "响应结构", False, {})], ["name"]),
   resp=wrap(None, "接口更新成功"), resp_msg="接口更新成功")

ep("DELETE", "/api/apis/{aid}", "接口管理", "删除接口",
   "删除接口，并级联删除其下的全部测试用例。",
   path_params=[P("aid", "integer", "接口ID", True)],
   resp=wrap(None, "接口已删除"), resp_msg="接口已删除")

ep("POST", "/api/projects/{pid}/apis/upload", "接口管理", "上传接口文档解析",
   "上传接口文档自动解析批量入库，同 method+path 自动去重。支持 5 类格式：OpenAPI/Swagger（json/yaml）、"
   "Postman Collection（json）、PDF、HTML、Markdown/文本。",
   path_params=[P("pid", "integer", "项目ID", True)],
   query=[P("file", "file(binary)", "文档文件，multipart/form-data 上传，≤20MB", True)],
   resp=wrap({"parsed": 12, "inserted": 9},
             "接口文档解析完成，共 12 个有效接口，新增入库 9 个（重复已跳过）"),
   resp_msg="接口文档解析完成",
   notes=["Content-Type: multipart/form-data",
          "支持后缀：.json / .yaml / .yml / .pdf / .html / .htm / .md / .txt，其他后缀返回 400",
          "PDF 需为文本版（Word/Markdown 导出），扫描件图片版无法提取文本",
          "PDF/HTML 解析为启发式：识别「请求方法+接口路径」行或「接口名称/接口路径/请求方式」标签，"
          "并解析含「参数名/类型/必填/说明」的参数表，按 GET/DELETE→query、其余→body 归类"])

# ---------------- 用例管理 ----------------
ep("GET", "/api/projects/{pid}/cases", "用例管理", "用例列表（分页）",
   "多条件筛选分页查询用例，结果按【模块→接口→用例类型→优先级】标准化排序。",
   path_params=[P("pid", "integer", "项目ID", True)],
   query=[P("api_id", "integer", "按接口筛选", False),
          P("case_type", "string", "用例类型：正向/反向/边界/异常", False, ""),
          P("priority", "string", "优先级：P0/P1/P2", False, ""),
          P("keyword", "string", "用例名称模糊搜索", False, ""),
          P("page", "integer", "页码", False, 1),
          P("size", "integer", "每页条数", False, 10)],
   resp=wrap({"total": 28, "list": [
       {"id": 1, "project_id": 1, "api_id": 1, "api_name": "查询用户列表", "method": "GET", "path": "/api/users",
        "module": "用户管理", "name": "查询用户列表-正向-正常分页查询", "case_type": "正向",
        "priority": "P0", "steps": "1. 构造分页参数 2. 发起GET请求 3. 校验响应", "request_data": {"page": 1, "size": 10},
        "expected": {"status_code": 200, "body_contains": "code"}, "source": "AI", "last_status": "passed"}]}))

ep("GET", "/api/cases/{cid}", "用例管理", "用例详情",
   "返回单条用例完整定义。",
   path_params=[P("cid", "integer", "用例ID", True)],
   resp=wrap({"id": 1, "name": "查询用户列表-正向-正常分页查询", "case_type": "正向",
              "priority": "P0", "request_data": {}, "expected": {"status_code": 200}}))

ep("POST", "/api/projects/{pid}/cases", "用例管理", "新增用例",
   "手动创建测试用例，source 标记为 MANUAL。",
   path_params=[P("pid", "integer", "项目ID", True)],
   body=body_schema([P("api_id", "integer", "所属接口ID", True),
                     P("name", "string", "用例名称", True),
                     P("case_type", "string", "用例类型", False, "正向", ["正向", "反向", "边界", "异常"]),
                     P("priority", "string", "优先级", False, "P1", ["P0", "P1", "P2"]),
                     P("steps", "string", "测试步骤描述", False, ""),
                     P("request_data", "object", "请求数据（query/body）", False, {}),
                     P("expected", "object", "预期结果（状态码/响应包含等断言）", False, {})],
                    ["api_id", "name"]),
   resp=wrap({"id": 1}, "用例创建成功"), resp_msg="用例创建成功")

ep("PUT", "/api/cases/{cid}", "用例管理", "编辑用例",
   "修改测试用例。",
   path_params=[P("cid", "integer", "用例ID", True)],
   body=body_schema([P("api_id", "integer", "所属接口ID", True),
                     P("name", "string", "用例名称", True),
                     P("case_type", "string", "用例类型", False, "正向"),
                     P("priority", "string", "优先级", False, "P1"),
                     P("steps", "string", "测试步骤", False, ""),
                     P("request_data", "object", "请求数据", False, {}),
                     P("expected", "object", "预期结果", False, {})], ["api_id", "name"]),
   resp=wrap(None, "用例更新成功"), resp_msg="用例更新成功")

ep("DELETE", "/api/cases/{cid}", "用例管理", "删除用例",
   "删除单条用例。",
   path_params=[P("cid", "integer", "用例ID", True)],
   resp=wrap(None, "用例已删除"), resp_msg="用例已删除")

ep("POST", "/api/cases/batch-delete", "用例管理", "批量删除用例",
   "按 ID 批量删除用例。请求体为整型 ID 数组，或对象 {\"ids\": [...]} 两种形式均可。",
   body=body_schema([P("ids", "array<integer>", "用例ID数组（请求体直接传数组 [1,2,3]，或对象 {\"ids\":[1,2,3]}）", True)], ["ids"]),
   resp=wrap(None, "已删除 5 条用例"), resp_msg="已删除 N 条用例",
   notes=["Content-Type: application/json", "请求体为顶层数组时直接传 [1,2,3]，无需包裹字段"])

ep("POST", "/api/cases/run", "用例管理", "快速执行用例",
   "立即执行单条或批量选中的用例，返回执行任务ID。环境优先级：显式 env_id → 项目默认环境 → 项目首个环境。",
   body=body_schema([P("ids", "array<integer>", "用例ID数组（批量执行）", False, []),
                     P("case_id", "integer", "单条用例ID（单条执行）", False, 0),
                     P("env_id", "integer", "执行环境ID，不传则用项目默认/首个环境", False)]),
   resp=wrap({"task_id": 12, "total": 5}, "执行任务已启动"), resp_msg="执行任务已启动",
   notes=["任务异步执行，需轮询 /api/execution/{task_id}/status 获取进度",
          "请求 URL = 环境 BaseURL + 接口路径；接口路径若已是 http(s) 完整地址则直接使用",
          "项目无任何环境且接口路径非完整 URL 时，返回 400 提示先配置环境"])

ep("GET", "/api/projects/{pid}/cases/all", "用例管理", "用例全量列表",
   "不分页返回项目下全部用例（含接口与模块信息）。",
   path_params=[P("pid", "integer", "项目ID", True)],
   resp=wrap([{"id": 1, "name": "查询用户列表-正向-正常分页查询", "module": "用户管理",
               "method": "GET", "path": "/api/users", "case_type": "正向", "priority": "P0"}]))

# ---------------- AI 能力 ----------------
ep("GET", "/api/ai/config", "AI 能力", "获取 AI 配置",
   "读取系统级 AI 配置，api_key 明文返回供前端回填，另附脱敏字段。",
   resp=wrap({"model": "deepseek-chat", "api_key": "sk-xxxx", "api_key_masked": "sk-xx****xxxx",
              "base_url": "https://api.deepseek.com/v1", "timeout": 60, "configured": True}))

ep("POST", "/api/ai/config", "AI 能力", "保存 AI 配置",
   "保存模型、Key、BaseURL、超时时间，全局即时生效。",
   body=body_schema([P("model", "string", "模型标识", False, "deepseek-chat"),
                     P("api_key", "string", "API Key", False, ""),
                     P("base_url", "string", "OpenAI 兼容接口地址", False, "https://api.deepseek.com/v1"),
                     P("timeout", "integer", "请求超时（秒，5-600）", False, 60)],
                    ["base_url"]),
   resp=wrap(None, "AI 配置保存成功，已全局生效"), resp_msg="AI 配置保存成功，已全局生效",
   notes=["未配置 API Key 时，用例生成自动降级为内置规则引擎"])

ep("POST", "/api/ai/config/test", "AI 能力", "测试 AI 连通性",
   "用传入配置（或已保存配置）发起一次真实调用，验证可用性。",
   body=body_schema([P("model", "string", "模型标识", False, "deepseek-chat"),
                     P("api_key", "string", "API Key", False, ""),
                     P("base_url", "string", "接口地址", False, "https://api.deepseek.com/v1"),
                     P("timeout", "integer", "超时（秒）", False, 60)]),
   resp=wrap({"success": True, "message": "连接成功：模型响应正常"}))

ep("POST", "/api/ai/generate", "AI 能力", "AI 生成测试用例",
   "为单个接口或整个项目批量生成测试用例；生成前自动清除该接口的旧 AI 用例，避免重复堆积。",
   body=body_schema([P("project_id", "integer", "项目ID", True),
                     P("scope", "string", "生成范围", False, "all", ["all", "single"]),
                     P("api_id", "integer", "接口ID（scope=single 时必填）", False),
                     P("gen_type", "string", "生成类型", False, "full", ["positive", "full"])],
                    ["project_id"]),
   resp=wrap({"api_count": 4, "case_count": 28, "used_ai": False,
              "engine": "内置规则引擎（降级）"}, "成功生成 28 条用例"),
   resp_msg="成功生成 N 条用例",
   notes=["positive = 仅正向用例；full = 正向 + 反向 + 边界 + 异常",
          "used_ai=false 表示未配置 Key，已降级使用内置规则引擎"])

ep("POST", "/api/ai/organize/{pid}", "AI 能力", "AI 整理用例文档",
   "统一规范化项目下所有用例的命名、优先级与类型，并按【模块→接口→类型→优先级】归档。",
   path_params=[P("pid", "integer", "项目ID", True)],
   resp=wrap({"total": 28, "normalized": 3,
              "order_rule": "按 模块 → 接口 → 用例类型（正向/反向/边界/异常）→ 优先级（P0/P1/P2）自动分类归档"},
             "用例文档整理完成：共 28 条用例已按标准格式分类归档"),
   resp_msg="用例文档整理完成")

ep("GET", "/api/ai/models", "AI 能力", "可选模型列表",
   "返回系统内置可选择的模型清单。",
   resp=wrap([{"value": "deepseek-chat", "label": "DeepSeek Chat"},
              {"value": "gpt-4o-mini", "label": "GPT-4o mini"},
              {"value": "qwen-max", "label": "通义千问 Max"},
              {"value": "custom", "label": "自定义兼容模型"}]))

# ---------------- 测试执行 ----------------
ep("POST", "/api/execution/start", "测试执行", "启动执行任务",
   "按项目+环境+范围创建执行任务并立即异步启动，返回任务ID。",
   body=body_schema([P("project_id", "integer", "项目ID", True),
                     P("env_id", "integer", "环境ID，不传则用默认环境", False),
                     P("scope", "string", "执行范围", False, "all", ["all", "selected", "failed"]),
                     P("case_ids", "array<integer>", "用例ID数组（scope=selected）", False, []),
                     P("task_name", "string", "任务名称，留空自动生成", False, "")],
                    ["project_id"]),
   resp=wrap({"task_id": 12, "total": 28}, "任务已启动"), resp_msg="任务已启动",
   notes=["scope=failed 时自动筛选上一次执行失败的用例"])

ep("GET", "/api/execution/{task_id}/status", "测试执行", "任务状态与实时日志",
   "轮询接口：返回任务进度统计与增量日志（前端 1s 轮询实现实时滚动效果）。",
   path_params=[P("task_id", "integer", "任务ID", True)],
   query=[P("log_after", "integer", "增量拉取日志起始ID，0=全部", False, 0)],
   resp=wrap({"task": {"id": 12, "name": "测试任务-001", "status": "running", "total": 28,
                       "executed": 10, "passed": 7, "failed": 3, "env_name": "本地Mock环境",
                       "started_at": "2026-10-27 11:30:00"},
              "running": True,
              "logs": [{"id": 101, "level": "INFO", "message": "[3/28] 执行用例：用户登录-反向-密码错误"}]}),
   notes=["建议轮询间隔 1000ms，单次最多返回 200 条日志"])

ep("POST", "/api/execution/{task_id}/stop", "测试执行", "终止执行任务",
   "向运行中的任务发送终止指令，已执行结果保留。",
   path_params=[P("task_id", "integer", "任务ID", True)],
   resp=wrap(None, "终止指令已发送"), resp_msg="终止指令已发送")

ep("POST", "/api/execution/{task_id}/rerun-failed", "测试执行", "重跑失败用例",
   "提取指定任务中的失败用例，创建新任务重新执行。",
   path_params=[P("task_id", "integer", "原任务ID", True)],
   resp=wrap({"task_id": 13, "total": 19}, "已创建重跑任务，共 19 条失败用例"),
   resp_msg="已创建重跑任务")

# ---------------- 测试报告 ----------------
ep("GET", "/api/reports/project/{pid}", "测试报告", "报告列表",
   "分页返回项目下的历史执行任务（即测试报告），含通过率。",
   path_params=[P("pid", "integer", "项目ID", True)],
   query=[P("page", "integer", "页码", False, 1), P("size", "integer", "每页条数", False, 10)],
   resp=wrap({"total": 3, "list": [
       {"id": 12, "name": "测试任务-001", "status": "completed", "total": 28, "executed": 28,
        "passed": 9, "failed": 19, "pass_rate": 32.1, "env_name": "本地Mock环境",
        "env_base_url": "http://127.0.0.1:8099", "env_deleted": False,
        "created_at": "2026-10-27 11:30:00"}]}),
   notes=["`env_base_url` 为执行时的环境域名快照，用于确认该次执行打到哪台机器；"
          "环境被删除后 `env_deleted=true` 且域名无法回溯（仅保留名称）"])

ep("GET", "/api/reports/{task_id}", "测试报告", "报告详情",
   "返回报告全量数据：任务概览、通过率、每条用例执行结果、模块成功率、完整执行日志。",
   path_params=[P("task_id", "integer", "任务ID", True)],
   resp=wrap({"task": {"id": 12, "name": "测试任务-001", "status": "completed", "total": 28,
                       "executed": 28, "passed": 9, "failed": 19,
                       "env_name": "本地Mock环境", "env_base_url": "http://127.0.0.1:8099",
                       "env_deleted": False},
              "pass_rate": 32.1,
              "results": [{"case_id": 1, "case_name": "查询用户列表-正向-正常分页查询", "module": "用户管理",
                           "method": "GET", "path": "/api/users", "status": "passed",
                           "status_code": 200, "duration_ms": 12,
                           "request_info": {"method": "get", "url": "http://127.0.0.1:8099/api/users",
                                            "headers": {}, "params": {"page": 1}},
                           "response": {"code": 0, "data": {}},
                           "assertions": [{"name": "状态码校验", "expected": 200, "actual": 200, "passed": True}],
                           "fail_reason": ""}],
              "module_stats": [{"module": "鉴权模块", "total": 6, "passed": 6, "rate": 100.0}],
              "logs": [{"id": 1, "level": "INFO", "message": "任务启动：共 28 条用例"},
                       {"id": 2, "level": "INFO",
                        "message": "执行环境：本地Mock环境（http://127.0.0.1:8099）　超时 10s　重试 1次"}]}),
   notes=["`results[].request_info.url` 为环境域名 + 接口路径拼接后的最终请求地址，"
          "是确认「实际打到哪个环境」的最直接证据"])

ep("GET", "/api/reports/{task_id}/export", "测试报告", "导出报告文件",
   "导出测试报告为 HTML / Excel / PDF 文件（二进制流）。",
   path_params=[P("task_id", "integer", "任务ID", True)],
   query=[P("fmt", "string", "导出格式", False, "html", ["html", "excel", "pdf"]),
          P("download", "integer", "1=下载附件，0=HTML在线预览（仅html）", False, 1)],
   resp={"（文件流）": "Content-Disposition: attachment; filename=测试报告_xxx.html"},
   binary=True)

ep("DELETE", "/api/reports/{task_id}", "测试报告", "删除报告",
   "删除报告，级联清除用例结果与执行日志。",
   path_params=[P("task_id", "integer", "任务ID", True)],
   resp=wrap(None, "报告已删除"), resp_msg="报告已删除")

# ---------------- 仪表盘 ----------------
ep("GET", "/api/dashboard", "仪表盘", "首页统计数据",
   "聚合返回项目数、接口数、用例数、近7天通过率趋势、用例状态分布、最近10条任务。",
   resp=wrap({"projects": 1, "apis": 4, "cases": 28, "week_rate": 32.1,
              "trend": [{"date": "10-27", "executed": 28, "passed": 9, "rate": 32.1}],
              "pie": {"passed": 9, "failed": 19, "skipped": 0, "pending": 0},
              "recent": [{"id": 12, "name": "测试任务-001", "pass_rate": 32.1}]}))

# ---------------- 用户与权限 ----------------
MENU_KEYS_DESC = "菜单 key 取自「菜单目录」接口，对应前端左侧功能入口；权限模型见下方说明。"
ep("GET", "/api/menus", "用户与权限", "菜单目录",
   "返回平台全部功能菜单（权限最小单元）的定义，含 key / 标题 / 图标 / 路由。",
   resp=wrap([{"key": "dashboard", "title": "首页仪表盘", "icon": "DataLine", "path": "/dashboard"}]),
   resp_msg="操作成功",
   notes=["所有管理接口均要求调用方拥有 users 菜单权限（即超级管理员）"])

ep("GET", "/api/roles", "用户与权限", "角色列表",
   "返回全部角色及其菜单权限集合，内置角色（is_system=true）不可删除。",
   resp=wrap([{"id": 1, "name": "超级管理员", "code": "admin",
               "description": "拥有平台全部功能与系统配置权限",
               "menu_keys": ["dashboard","projects","envs","apis","ai-generate","cases","execution","reports","ai-config","users"],
               "is_system": True}]))

ep("POST", "/api/roles", "用户与权限", "创建角色",
   "新建角色并配置其菜单权限集合。",
   body=body_schema([P("name", "string", "角色名称", True),
                     P("code", "string", "角色编码（英文唯一标识）", True),
                     P("description", "string", "角色描述", False, ""),
                     P("menu_keys", "array", MENU_KEYS_DESC, False, "[]")],
                    ["name", "code"]),
   resp=wrap({"id": 4}, "角色创建成功"), resp_msg="角色创建成功",
   notes=["code 不可与已有角色重复"])

ep("PUT", "/api/roles/{rid}", "用户与权限", "编辑角色",
   "修改角色名称、描述与菜单权限；内置角色的 code 不可修改。",
   path_params=[P("rid", "integer", "角色ID", True)],
   body=body_schema([P("name", "string", "角色名称", True),
                     P("code", "string", "角色编码（内置角色忽略）", False, ""),
                     P("description", "string", "角色描述", False, ""),
                     P("menu_keys", "array", MENU_KEYS_DESC, False, "[]")], ["name"]),
   resp=wrap(None, "角色更新成功"), resp_msg="角色更新成功")

ep("DELETE", "/api/roles/{rid}", "用户与权限", "删除角色",
   "删除自定义角色；内置角色不可删，已绑定用户的角色需先调整用户后再删。",
   path_params=[P("rid", "integer", "角色ID", True)],
   resp=wrap(None, "角色已删除"), resp_msg="角色已删除",
   notes=["内置角色不可删除", "仍有用户绑定的角色不可删除"])

ep("GET", "/api/users", "用户与权限", "用户列表",
   "返回全部用户（不含密码），附带角色名称与实际菜单权限。",
   resp=wrap([{"id": 1, "username": "admin", "nickname": "管理员", "role_id": 1,
               "role_name": "超级管理员", "status": "active",
               "menus": ["dashboard","projects","envs","apis","ai-generate","cases","execution","reports","ai-config","users"],
               "created_at": "2026-10-27 11:20:03"}]))

ep("POST", "/api/users", "用户与权限", "创建用户",
   "新建用户并分配角色；菜单权限优先使用传入的 menu_keys，为空则继承所选角色权限。",
   body=body_schema([P("username", "string", "登录用户名（唯一）", True),
                     P("password", "string", "初始密码（至少6位）", True),
                     P("nickname", "string", "昵称", False, ""),
                     P("role_id", "integer", "所属角色ID", True),
                     P("status", "string", "账号状态：active / disabled", False, "active"),
                     P("menu_keys", "array", MENU_KEYS_DESC, False, "[]")],
                    ["username", "password", "role_id"]),
   resp=wrap({"id": 2}, "用户创建成功"), resp_msg="用户创建成功")

ep("PUT", "/api/users/{uid}", "用户与权限", "编辑用户",
   "修改用户昵称、密码（留空则不改）、角色、状态与菜单权限。",
   path_params=[P("uid", "integer", "用户ID", True)],
   body=body_schema([P("nickname", "string", "昵称", False, ""),
                     P("password", "string", "新密码（留空不修改，至少6位）", False, ""),
                     P("role_id", "integer", "所属角色ID", False, None),
                     P("status", "string", "账号状态：active / disabled", False, "active"),
                     P("menu_keys", "array", MENU_KEYS_DESC, False, "[]")]),
   resp=wrap(None, "用户更新成功"), resp_msg="用户更新成功",
   notes=["不能禁用或变更当前登录账号自身", "至少需保留一名拥有 users 权限的管理员"])

ep("DELETE", "/api/users/{uid}", "用户与权限", "删除用户",
   "删除指定用户，需管理员权限。",
   path_params=[P("uid", "integer", "用户ID", True)],
   resp=wrap(None, "用户已删除"), resp_msg="用户已删除",
   notes=["不能删除当前登录账号", "至少需保留一名管理员"])

# ---------------- 系统服务 ----------------
ep("GET", "/api/health", "系统服务", "健康检查",
   "服务存活探测，无需鉴权。",
   auth=False,
   resp=wrap({"status": "running", "product": "AI驱动Web接口自动化测试平台"}))

ep("GET", "/api/logs", "系统服务", "操作日志",
   "返回最近 50 条系统操作日志。",
   resp=wrap([{"id": 1, "username": "admin", "action": "AI生成用例",
               "detail": "项目#1 接口4个 生成用例28条", "created_at": "2026-10-27 11:25:00"}]))

ep("GET", "/api/projects/{pid}/cases/export", "系统服务", "导出用例文档",
   "导出项目用例文档为 Word / Excel / PDF 文件（二进制流）。",
   path_params=[P("pid", "integer", "项目ID", True)],
   query=[P("fmt", "string", "导出格式", False, "word", ["word", "excel", "xlsx", "pdf"])],
   resp={"（文件流）": "Content-Disposition: attachment; filename=接口测试用例_xxx.docx"},
   binary=True)


# ============================================================
# 统计
# ============================================================
def build_stats():
    by_tag = OrderedDict()
    by_method = OrderedDict()
    for t, _ in TAGS:
        by_tag[t] = []
    for e in E:
        by_tag.setdefault(e["tag"], []).append(e)
        by_method[e["method"]] = by_method.get(e["method"], 0) + 1
    return by_tag, by_method


# ============================================================
# 生成 OpenAPI 3.0
# ============================================================
TYPE_MAP = {
    "string": "string", "integer": "integer", "number": "number", "boolean": "boolean",
    "object": "object", "array<object>": "array", "array<integer>": "array",
    "file(binary)": "string",
}


def to_openapi():
    paths = OrderedDict()
    for e in E:
        p = e["path"]
        if p not in paths:
            paths[p] = OrderedDict()
        op = OrderedDict()
        op["tags"] = [e["tag"]]
        op["summary"] = e["name"]
        op["description"] = e["desc"]
        op["operationId"] = e["method"].lower() + p.replace("/", "_").replace("{", "").replace("}", "")
        params = []
        for pp in e["path_params"]:
            params.append({"name": pp["name"], "in": "path", "required": True,
                           "description": pp["desc"],
                           "schema": {"type": TYPE_MAP.get(pp["type"], "string")}})
        for q in e["query"]:
            is_file = q["type"].startswith("file")
            params.append({"name": q["name"], "in": "query", "required": q["required"],
                           "description": q["desc"],
                           "schema": {"type": TYPE_MAP.get(q["type"], "string"),
                                      **({"format": "binary"} if is_file else {}),
                                      **({"default": q["default"]} if q.get("default") is not None else {}),
                                      **({"enum": q["enum"]} if q.get("enum") else {})}})
        if params:
            op["parameters"] = params
        if e["body"]:
            props = OrderedDict()
            for pr in e["body"]["props"]:
                s = {"type": TYPE_MAP.get(pr["type"], "string"), "description": pr["desc"]}
                if pr["type"].startswith("array"):
                    inner = "object" if "object" in pr["type"] else "integer"
                    s["items"] = {"type": inner}
                if pr.get("default") is not None:
                    s["default"] = pr["default"]
                if pr.get("enum"):
                    s["enum"] = pr["enum"]
                props[pr["name"]] = s
            schema = {"type": "object", "properties": props}
            if e["body"]["required"]:
                schema["required"] = e["body"]["required"]
            op["requestBody"] = {"required": True, "content": {"application/json": {"schema": schema}}}
        if e["auth"]:
            op["security"] = [{"TokenAuth": []}]
        resp_content = {}
        if e["binary"]:
            resp_content = {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}}
        else:
            resp_content = {"application/json": {
                "schema": {"type": "object", "properties": {
                    "code": {"type": "integer", "example": 0},
                    "msg": {"type": "string", "example": e["resp_msg"]},
                    "data": {}}},
                "example": e["resp"]}}
        op["responses"] = {
            "200": {"description": e["resp_msg"], "content": resp_content},
            "400": {"description": "业务参数错误（code!=0）"},
            "401": {"description": "未登录或 Token 失效"},
            "404": {"description": "资源不存在"},
        }
        if e["notes"]:
            op["description"] = e["desc"] + "\n\n" + "\n".join("- " + n for n in e["notes"])
        paths[p][e["method"].lower()] = op

    return OrderedDict([
        ("openapi", "3.0.3"),
        ("info", {"title": INFO["title"], "version": INFO["version"], "description": INFO["desc"]}),
        ("servers", [{"url": INFO["base_url"], "description": "本地服务"}]),
        ("tags", [{"name": t, "description": dd} for t, dd in TAGS]),
        ("components", {"securitySchemes": {"TokenAuth": {
            "type": "apiKey", "in": "header", "name": "Authorization",
            "description": "登录接口返回的 token 原样放入 Authorization 请求头"}}}),
        ("paths", paths),
    ])


# ============================================================
# 生成 Markdown
# ============================================================
def jstr(o, indent=0):
    return json.dumps(o, ensure_ascii=False, indent=2)


def md_params_table(items, kind):
    if not items:
        return ""
    rows = ["| 参数名 | 类型 | 必填 | 默认值 | 说明 |", "|---|---|---|---|---|"]
    for it in items:
        dft = it.get("default", "-")
        if isinstance(dft, (dict, list)):
            dft = "`" + json.dumps(dft, ensure_ascii=False) + "`"
        elif dft == "-":
            pass
        else:
            dft = f"`{dft}`"
        rows.append(f"| `{it['name']}` | {it['type']} | {'是' if it['required'] else '否'} | {dft} | {it['desc']} |")
    return "\n".join(rows)


def build_markdown():
    by_tag, by_method = build_stats()
    total = len(E)
    paths_set = {e["path"] for e in E}
    L = []
    A = L.append
    A(f"# {INFO['title']}")
    A("")
    A(f"> 文档版本：**{INFO['version']}**　|　基础地址：**`{INFO['base_url']}`**　|　"
      f"接口总数：**{total}**（路径 {len(paths_set)} 个）　|　更新日期：2026-10-27")
    A("")
    A(INFO["desc"])
    A("")
    A("---")
    A("")
    A("## 一、接口统计")
    A("")
    A("### 1.1 按业务模块")
    A("")
    A("| 模块 | 接口数 | 占比 | 说明 |")
    A("|---|---:|---:|---|")
    tag_desc = dict(TAGS)
    for t, items in by_tag.items():
        A(f"| {t} | {len(items)} | {len(items)/total*100:.1f}% | {tag_desc.get(t,'')} |")
    A(f"| **合计** | **{total}** | **100%** | — |")
    A("")
    A("### 1.2 按 HTTP 方法")
    A("")
    A("| 方法 | 数量 | 占比 |")
    A("|---|---:|---:|")
    for m in ["GET", "POST", "PUT", "DELETE"]:
        if m in by_method:
            A(f"| {m} | {by_method[m]} | {by_method[m]/total*100:.1f}% |")
    A(f"| **合计** | **{total}** | **100%** |")
    A("")
    A("### 1.3 按鉴权要求")
    A("")
    need = sum(1 for e in E if e["auth"])
    A("| 类型 | 数量 | 说明 |")
    A("|---|---:|---|")
    A(f"| 需鉴权 | {need} | 请求头需携带 `Authorization: <token>` |")
    A(f"| 免鉴权 | {total - need} | 登录、健康检查 |")
    A("")
    A("---")
    A("")
    A("## 二、通用约定")
    A("")
    A("### 2.1 请求")
    A("")
    A("| 项 | 说明 |")
    A("|---|---|")
    A(f"| BaseURL | `{INFO['base_url']}` |")
    A("| Content-Type | `application/json`（文件上传接口为 `multipart/form-data`） |")
    A("| 鉴权方式 | 请求头 `Authorization: <token>`（token 为登录接口返回，非 Bearer 前缀） |")
    A("| 字符编码 | UTF-8 |")
    A("")
    A("### 2.2 统一响应结构")
    A("")
    A("所有 JSON 接口统一返回如下外壳，`code = 0` 表示业务成功：")
    A("")
    A("```json")
    A(jstr({"code": 0, "msg": "操作成功", "data": "{...} 业务数据，对象或数组"}))
    A("```")
    A("")
    A("业务异常（参数错误、资源不存在等）同样使用该结构，HTTP 状态码与 `code` 保持一致，"
      "例如 `HTTP 400 + {\"code\":400,\"msg\":\"...\",\"data\":null}`，前端可直接取 `msg` 提示用户。")
    A("")
    A("| 字段 | 类型 | 说明 |")
    A("|---|---|---|")
    A("| `code` | int | 0=成功，非 0=业务失败 |")
    A("| `msg` | string | 结果描述，可直接用于前端提示 |")
    A("| `data` | any | 业务数据；列表接口为对象或数组，无数据时为 null |")
    A("")
    A("### 2.3 错误码")
    A("")
    A("| HTTP 状态码 | 场景 | 处理建议 |")
    A("|---|---|---|")
    A("| 400 | 参数缺失/非法、业务规则不满足（如「项目暂无接口」） | 提示 `msg` 内容 |")
    A("| 401 | 未登录或 Token 失效 | 清除本地 token，跳转登录页 |")
    A("| 404 | 资源不存在（项目/接口/用例/任务） | 提示资源已被删除 |")
    A("| 500 | 服务端异常 | 查看服务日志 |")
    A("")
    A("### 2.4 异步任务说明")
    A("")
    A("测试执行为异步模型：调用启动接口立即返回 `task_id`，前端以 **1 秒间隔**轮询")
    A("`GET /api/execution/{task_id}/status`，通过 `log_after` 增量拉取日志实现实时滚动效果；")
    A("`task.status` 变为 `completed` 时任务结束，可跳转报告详情。")
    A("")
    A("---")
    A("")
    A("## 三、接口详情")
    A("")
    idx = 0
    for t, items in by_tag.items():
        A(f"### {t}（{len(items)} 个）")
        A("")
        for e in items:
            idx += 1
            A(f"#### {idx}. {e['name']}")
            A("")
            A(f"`{e['method']} {e['path']}`")
            A("")
            A(f"- **描述**：{e['desc']}")
            A(f"- **鉴权**：{'需要' if e['auth'] else '不需要'}")
            if e["path_params"]:
                A("")
                A("**路径参数**")
                A("")
                A(md_params_table(e["path_params"], "path"))
            if e["query"]:
                A("")
                A("**查询参数**")
                A("")
                A(md_params_table(e["query"], "query"))
            if e["body"]:
                A("")
                A("**请求体（application/json）**")
                A("")
                A(md_params_table(e["body"]["props"], "body"))
                A("")
                A("请求示例：")
                A("")
                example = OrderedDict()
                for pr in e["body"]["props"]:
                    if pr.get("default") is not None:
                        example[pr["name"]] = pr["default"]
                    else:
                        example[pr["name"]] = "" if pr["type"] == "string" else (
                            0 if pr["type"] == "integer" else ([] if pr["type"].startswith("array") else {}))
                A("```json")
                A(jstr(example))
                A("```")
            if e["notes"]:
                A("")
                A("**说明**")
                A("")
                for n in e["notes"]:
                    A(f"- {n}")
            A("")
            A("**响应示例**")
            A("")
            if e["binary"]:
                A("返回文件二进制流，响应头 `Content-Disposition: attachment; filename=...`。")
            else:
                A("```json")
                A(jstr(e["resp"]))
                A("```")
            A("")
            A("---")
            A("")
    A("## 四、数据字典")
    A("")
    A("### 4.1 核心表")
    A("")
    A("| 表名 | 说明 | 主要字段 |")
    A("|---|---|---|")
    A("| `users` | 用户 | id, username, password(哈希), role |")
    A("| `tokens` | 登录令牌 | token, user_id |")
    A("| `projects` | 测试项目 | id, name, description, owner, created_at |")
    A("| `environments` | 测试环境 | id, project_id, name, base_url, headers, timeout, retry, is_default |")
    A("| `apis` | 被测接口 | id, project_id, name, method, path, module, headers, query_params, body, response_schema |")
    A("| `cases` | 测试用例 | id, project_id, api_id, name, case_type, priority, steps, request_data, expected, source, last_status |")
    A("| `tasks` | 执行任务/报告 | id, project_id, name, env_id, env_name, case_ids, status, total, executed, passed, failed, created_at |")
    A("| `case_results` | 用例执行结果 | id, task_id, case_id, case_name, module, status, status_code, duration_ms, request, response, assertions, fail_reason |")
    A("| `task_logs` | 执行日志 | id, task_id, level, message |")
    A("| `op_logs` | 操作审计日志 | id, username, action, detail, created_at |")
    A("| `ai_config` | AI 配置 | id, model, api_key, base_url, timeout |")
    A("")
    A("### 4.2 枚举值")
    A("")
    A("| 字段 | 取值 |")
    A("|---|---|")
    A("| `case_type` | 正向 / 反向 / 边界 / 异常 |")
    A("| `priority` | P0 / P1 / P2 |")
    A("| `case.source` | AI（AI生成） / MANUAL（手动创建） |")
    A("| `case.last_status` / `result.status` | passed / failed / skipped / pending |")
    A("| `task.status` | pending / running / completed / stopped |")
    A("| `log.level` | INFO / WARN / ERROR |")
    A("")
    A("---")
    A("")
    A("## 五、调用示例")
    A("")
    A("### 5.1 登录并拉取仪表盘（curl）")
    A("")
    A("```bash")
    A('# 1. 登录获取 token')
    A(f"TOKEN=$(curl -s -X POST {INFO['base_url']}/api/auth/login \\")
    A('  -H "Content-Type: application/json" \\')
    A('  -d \'{"username":"admin","password":"admin123"}\' | python3 -c "import sys,json;print(json.load(sys.stdin)[\'data\'][\'token\'])")')
    A("")
    A("# 2. 携带 token 调用业务接口")
    A(f'curl -s {INFO["base_url"]}/api/dashboard -H "Authorization: $TOKEN"')
    A("```")
    A("")
    A("### 5.2 完整自动化流程（Python）")
    A("")
    A("```python")
    A("import requests")
    A("")
    A(f'BASE = "{INFO["base_url"]}"')
    A("s = requests.Session()")
    A("")
    A("# 1. 登录")
    A('''tok = s.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin123"}').json()["data"]["token"]''')
    A('s.headers.update({"Authorization": tok})')
    A("")
    A("# 2. 创建项目")
    A('pid = s.post(f"{BASE}/api/projects", json={"name": "示例项目"}).json()["data"]["id"]')
    A("")
    A("# 3. 创建环境")
    A('s.post(f"{BASE}/api/projects/{pid}/envs", json={')
    A('    "name": "本地Mock环境", "base_url": "http://127.0.0.1:8099",')
    A('    "headers": [{"key": "Authorization", "value": "mock"}],')
    A('    "timeout": 10, "retry": 1, "is_default": True')
    A("})")
    A("")
    A("# 4. AI 生成用例（未配 Key 时自动降级规则引擎）")
    A('s.post(f"{BASE}/api/ai/generate", json={"project_id": pid, "scope": "all", "gen_type": "full"})')
    A("")
    A("# 5. 启动执行任务")
    A('task_id = s.post(f"{BASE}/api/execution/start", json={"project_id": pid, "scope": "all"}).json()["data"]["task_id"]')
    A("")
    A("# 6. 轮询任务状态")
    A("import time")
    A("while True:")
    A('    r = s.get(f"{BASE}/api/execution/{task_id}/status").json()["data"]')
    A('    print(r["task"]["executed"], "/", r["task"]["total"])')
    A('    if not r["running"]:')
    A("        break")
    A("    time.sleep(1)")
    A("")
    A("# 7. 获取报告")
    A('report = s.get(f"{BASE}/api/reports/{task_id}").json()["data"]')
    A('print("通过率:", report["pass_rate"])')
    A("```")
    A("")
    A("---")
    A("")
    A("## 六、变更记录")
    A("")
    A("| 版本 | 日期 | 说明 |")
    A("|---|---|---|")
    A("| 1.0.0 | 2026-10-27 | 首个正式版本，覆盖 8 大能力域共 %d 个接口 |" % total)
    A("")
    return "\n".join(L)


# ============================================================
# 生成 HTML
# ============================================================
def build_html():
    by_tag, by_method = build_stats()
    total = len(E)
    tag_desc = dict(TAGS)
    tag_rows = "".join(
        f"<tr><td><b>{t}</b></td><td class=num>{len(items)}</td>"
        f"<td class=num>{len(items)/total*100:.1f}%</td><td>{tag_desc.get(t,'')}</td></tr>"
        for t, items in by_tag.items())
    total = len(E)
    method_rows = "".join(
        f"<tr><td><span class='m m-{m}'>{m}</span></td><td class=num>{by_method.get(m,0)}</td>"
        f"<td class=num>{by_method.get(m,0)/total*100:.1f}%</td></tr>"
        for m in ["GET", "POST", "PUT", "DELETE"] if m in by_method)
    need = sum(1 for e in E if e["auth"])

    # 模块分布条形
    bars = "".join(
        f"<div class='bar-row'><span class='bar-label'>{t}</span>"
        f"<span class='bar-track'><i style='width:{len(items)/max(len(i) for i in by_tag.values())*100:.0f}%'></i></span>"
        f"<span class='bar-val'>{len(items)}</span></div>"
        for t, items in by_tag.items())

    sections = []
    idx = 0
    for t, items in by_tag.items():
        blocks = []
        for e in items:
            idx += 1
            pth = ""
            if e["path_params"]:
                pth = "<div class='sub'>路径参数</div>" + tbl(e["path_params"])
            qry = ""
            if e["query"]:
                qry = "<div class='sub'>查询参数</div>" + tbl(e["query"])
            bdy = ""
            if e["body"]:
                bdy = "<div class='sub'>请求体（application/json）</div>" + tbl(e["body"]["props"])
                example = OrderedDict()
                for pr in e["body"]["props"]:
                    if pr.get("default") is not None:
                        example[pr["name"]] = pr["default"]
                    else:
                        example[pr["name"]] = "" if pr["type"] == "string" else (
                            0 if pr["type"] == "integer" else ([] if pr["type"].startswith("array") else {}))
                bdy += f"<pre class='code'>{esc(jstr(example))}</pre>"
            note = ""
            if e["notes"]:
                note = "<div class='sub'>说明</div><ul class='notes'>" + "".join(
                    f"<li>{esc(n)}</li>" for n in e["notes"]) + "</ul>"
            if e["binary"]:
                resp_block = "<div class='sub'>响应</div><p>返回文件二进制流，响应头 <code>Content-Disposition: attachment</code>。</p>"
            else:
                resp_block = "<div class='sub'>响应示例</div><pre class='code'>" + esc(jstr(e["resp"])) + "</pre>"
            blocks.append(f"""
<div class="api" id="api-{idx}">
  <div class="api-head">
    <span class="m m-{e['method']}">{e['method']}</span>
    <code class="path">{esc(e['path'])}</code>
    <span class="api-name">{esc(e['name'])}</span>
    <span class="badge {'auth' if e['auth'] else 'noauth'}">{'需鉴权' if e['auth'] else '免鉴权'}</span>
  </div>
  <p class="desc">{esc(e['desc'])}</p>
  {pth}{qry}{bdy}{note}{resp_block}
</div>""")
        sections.append(f"<h2 class='sec'><span class='sec-idx'>{tag_desc.get(t,'')}</span>{t} <em>{len(items)} 个接口</em></h2>"
                        + "".join(blocks))
    nav = "".join(f"<li><a href='#{t}'>{t}<em>{len(items)}</em></a></li>" for t, items in by_tag.items())

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{INFO['title']} v{INFO['version']}</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;color:#1d2129;background:#f5f7fa}}
.wrap{{display:flex;max-width:1280px;margin:0 auto}}
.side{{width:230px;flex:0 0 230px;padding:24px 16px;position:sticky;top:0;height:100vh;overflow:auto;background:#fff;border-right:1px solid #e5e6eb}}
.side h3{{font-size:13px;color:#86909c;margin:16px 0 8px;font-weight:600}}
.side ul{{list-style:none;padding:0;margin:0}}
.side li a{{display:flex;justify-content:space-between;align-items:center;padding:7px 10px;border-radius:6px;color:#4e5969;text-decoration:none;font-size:13px}}
.side li a:hover{{background:#f2f3f5;color:#1677ff}}
.side li em{{font-style:normal;font-size:12px;color:#a9aeb8}}
.main{{flex:1;padding:28px 32px;min-width:0}}
h1{{font-size:24px;margin:0 0 6px}}
.meta{{color:#86909c;font-size:13px;margin-bottom:24px}}
h2.sec{{font-size:18px;margin:32px 0 14px;padding:14px 16px;background:#fff;border-left:4px solid #1677ff;border-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,.04)}}
h2.sec em{{font-style:normal;font-size:13px;color:#86909c;margin-left:8px}}
table{{width:100%;border-collapse:collapse;margin:6px 0 14px;background:#fff;font-size:13px;border-radius:6px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.04)}}
th{{background:#f5f7fa;text-align:left;padding:9px 12px;font-weight:600;color:#4e5969;border-bottom:1px solid #e5e6eb}}
td{{padding:8px 12px;border-bottom:1px solid #f0f0f0;vertical-align:top}}
td.num{{text-align:right;font-variant-numeric:tabular-nums}}
code{{font-family:"SF Mono",Menlo,Consolas,monospace;font-size:12.5px}}
.path{{background:#f2f3f5;padding:2px 8px;border-radius:4px;color:#333}}
.api{{background:#fff;border-radius:8px;padding:16px 18px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.api-head{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:6px}}
.api-name{{font-weight:600;font-size:15px}}
.badge{{font-size:11px;padding:2px 8px;border-radius:10px}}
.badge.auth{{background:#e8f3ff;color:#1677ff}}
.badge.noauth{{background:#f2f3f5;color:#86909c}}
.desc{{color:#4e5969;margin:4px 0 10px}}
.sub{{font-size:13px;font-weight:600;color:#4e5969;margin:14px 0 4px}}
pre.code{{background:#f7f8fa;border:1px solid #e5e6eb;border-radius:6px;padding:12px 14px;overflow:auto;font-size:12.5px;line-height:1.6;margin:6px 0 0}}
.m{{font-size:11px;font-weight:700;padding:3px 8px;border-radius:4px;color:#fff;letter-spacing:.5px}}
.m-GET{{background:#1677ff}}.m-POST{{background:#00b42a}}.m-PUT{{background:#ff7d00}}.m-DELETE{{background:#f53f3f}}
.notes{{margin:4px 0 0;padding-left:20px;color:#4e5969;font-size:13px}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}}
.card{{background:#fff;border-radius:8px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.card .v{{font-size:26px;font-weight:700;color:#1677ff}}
.card .k{{font-size:12px;color:#86909c}}
.bars{{background:#fff;border-radius:8px;padding:16px 18px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.bar-row{{display:flex;align-items:center;gap:10px;margin-bottom:7px;font-size:13px}}
.bar-label{{width:88px;color:#4e5969;text-align:right;flex:0 0 88px}}
.bar-track{{flex:1;height:14px;background:#f2f3f5;border-radius:7px;overflow:hidden}}
.bar-track i{{display:block;height:100%;background:linear-gradient(90deg,#1677ff,#4096ff);border-radius:7px}}
.bar-val{{width:28px;color:#4e5969;font-variant-numeric:tabular-nums}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px}}
.panel{{background:#fff;border-radius:8px;padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.panel h4{{margin:0 0 10px;font-size:14px}}
@media(max-width:900px){{.cards{{grid-template-columns:repeat(2,1fr)}}.two{{grid-template-columns:1fr}}.side{{display:none}}}}
</style></head><body>
<div class="wrap">
<nav class="side"><h3>接口目录</h3><ul>{nav}</ul></nav>
<main class="main">
<h1>{INFO['title']}</h1>
<div class="meta">版本 {INFO['version']}　·　BaseURL <code>{INFO['base_url']}</code>　·　共 {total} 个接口　·　2026-10-27</div>
<div class="cards">
  <div class="card"><div class="v">{total}</div><div class="k">接口总数</div></div>
  <div class="card"><div class="v">{len({e["path"] for e in E})}</div><div class="k">路径数</div></div>
  <div class="card"><div class="v">{len(by_tag)}</div><div class="k">业务模块</div></div>
  <div class="card"><div class="v">{need}</div><div class="k">需鉴权接口</div></div>
</div>
<div class="bars">
  <h4 style="margin:0 0 12px;font-size:14px">模块分布</h4>
  {bars}
</div>
<div class="two">
  <div class="panel"><h4>按业务模块</h4><table><tr><th>模块</th><th>数量</th><th>占比</th><th>说明</th></tr>{tag_rows}</table></div>
  <div class="panel"><h4>按 HTTP 方法</h4><table><tr><th>方法</th><th>数量</th><th>占比</th></tr>{method_rows}</table>
  <h4 style="margin-top:18px">统一响应</h4><pre class="code">{esc(jstr({"code":0,"msg":"操作成功","data":"{业务数据}"}))}</pre>
  <p style="font-size:13px;color:#4e5969;margin:8px 0 0">鉴权：请求头 <code>Authorization: &lt;token&gt;</code>（登录接口返回）</p></div>
</div>
{''.join(sections)}
</main></div></body></html>"""


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def tbl(items):
    rows = []
    for it in items:
        dft = it.get("default", "-")
        if isinstance(dft, (dict, list)):
            dft = "<code>" + esc(json.dumps(dft, ensure_ascii=False)) + "</code>"
        elif dft == "-":
            dft = "-"
        else:
            dft = f"<code>{esc(dft)}</code>"
        rows.append(f"<tr><td><code>{esc(it['name'])}</code></td><td>{esc(it['type'])}</td>"
                    f"<td>{'是' if it['required'] else '否'}</td><td>{dft}</td><td>{esc(it['desc'])}</td></tr>")
    return ("<table><tr><th>参数名</th><th>类型</th><th>必填</th><th>默认值</th><th>说明</th></tr>"
            + "".join(rows) + "</table>")


# ============================================================
if __name__ == "__main__":
    spec = to_openapi()
    with open(os.path.join(OUT, "openapi.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    with open(os.path.join(OUT, "接口API文档.md"), "w", encoding="utf-8") as f:
        f.write(build_markdown())
    with open(os.path.join(OUT, "接口API文档.html"), "w", encoding="utf-8") as f:
        f.write(build_html())
    by_tag, by_method = build_stats()
    print(f"接口总数: {len(E)}  路径数: {len({e['path'] for e in E})}")
    print("按模块:", {t: len(v) for t, v in by_tag.items()})
    print("按方法:", dict(by_method))
