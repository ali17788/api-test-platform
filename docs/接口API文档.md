# AI驱动Web接口自动化测试平台 API

> 文档版本：**1.0.0**　|　基础地址：**`http://127.0.0.1:8000`**　|　接口总数：**54**（路径 38 个）　|　更新日期：2026-10-27

零代码 · AI全自动 · 接口自动化测试平台后端服务。覆盖项目管理、环境配置、接口管理、AI用例生成、用例管理、测试执行、测试报告、仪表盘统计、用户与权限九大能力域。

---

## 一、接口统计

### 1.1 按业务模块

| 模块 | 接口数 | 占比 | 说明 |
|---|---:|---:|---|
| 认证管理 | 3 | 5.6% | 登录鉴权与当前用户信息 |
| 项目管理 | 5 | 9.3% | 测试项目的增删改查与概览统计 |
| 环境配置 | 4 | 7.4% | 项目下的多套测试环境（域名/请求头/超时/重试） |
| 接口管理 | 7 | 13.0% | 被测接口 CRUD、OpenAPI/Swagger/Postman 文档解析导入 |
| 用例管理 | 8 | 14.8% | 测试用例 CRUD、多条件筛选、批量执行与删除 |
| AI 能力 | 6 | 11.1% | AI 配置与连通性测试、AI 用例生成、用例文档智能整理 |
| 测试执行 | 4 | 7.4% | 执行任务启动、实时状态/日志轮询、终止、失败重跑 |
| 测试报告 | 4 | 7.4% | 报告列表/详情、HTML/Excel/PDF 导出、删除 |
| 仪表盘 | 1 | 1.9% | 首页全局统计数据聚合 |
| 用户与权限 | 9 | 16.7% | 菜单目录、角色管理（菜单权限模板）与用户管理（分配角色与菜单权限） |
| 系统服务 | 3 | 5.6% | 健康检查、操作日志、用例文档导出 |
| **合计** | **54** | **100%** | — |

### 1.2 按 HTTP 方法

| 方法 | 数量 | 占比 |
|---|---:|---:|
| GET | 23 | 42.6% |
| POST | 18 | 33.3% |
| PUT | 6 | 11.1% |
| DELETE | 7 | 13.0% |
| **合计** | **54** | **100%** |

### 1.3 按鉴权要求

| 类型 | 数量 | 说明 |
|---|---:|---|
| 需鉴权 | 52 | 请求头需携带 `Authorization: <token>` |
| 免鉴权 | 2 | 登录、健康检查 |

---

## 二、通用约定

### 2.1 请求

| 项 | 说明 |
|---|---|
| BaseURL | `http://127.0.0.1:8000` |
| Content-Type | `application/json`（文件上传接口为 `multipart/form-data`） |
| 鉴权方式 | 请求头 `Authorization: <token>`（token 为登录接口返回，非 Bearer 前缀） |
| 字符编码 | UTF-8 |

### 2.2 统一响应结构

所有 JSON 接口统一返回如下外壳，`code = 0` 表示业务成功：

```json
{
  "code": 0,
  "msg": "操作成功",
  "data": "{...} 业务数据，对象或数组"
}
```

业务异常（参数错误、资源不存在等）同样使用该结构，HTTP 状态码与 `code` 保持一致，例如 `HTTP 400 + {"code":400,"msg":"...","data":null}`，前端可直接取 `msg` 提示用户。

| 字段 | 类型 | 说明 |
|---|---|---|
| `code` | int | 0=成功，非 0=业务失败 |
| `msg` | string | 结果描述，可直接用于前端提示 |
| `data` | any | 业务数据；列表接口为对象或数组，无数据时为 null |

### 2.3 错误码

| HTTP 状态码 | 场景 | 处理建议 |
|---|---|---|
| 400 | 参数缺失/非法、业务规则不满足（如「项目暂无接口」） | 提示 `msg` 内容 |
| 401 | 未登录或 Token 失效 | 清除本地 token，跳转登录页 |
| 404 | 资源不存在（项目/接口/用例/任务） | 提示资源已被删除 |
| 500 | 服务端异常 | 查看服务日志 |

### 2.4 异步任务说明

测试执行为异步模型：调用启动接口立即返回 `task_id`，前端以 **1 秒间隔**轮询
`GET /api/execution/{task_id}/status`，通过 `log_after` 增量拉取日志实现实时滚动效果；
`task.status` 变为 `completed` 时任务结束，可跳转报告详情。

---

## 三、接口详情

### 认证管理（3 个）

#### 1. 用户登录

`POST /api/auth/login`

- **描述**：校验用户名密码，成功后下发 Token，后续请求需在请求头携带。
- **鉴权**：不需要

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `username` | string | 是 | - | 用户名 |
| `password` | string | 是 | - | 密码 |

请求示例：

```json
{
  "username": "",
  "password": ""
}
```

**说明**

- 初始账号：admin / admin123
- Token 存于服务端 tokens 表，登出即失效
- role_name 为角色名称，menus 为当前用户实际拥有的菜单权限 key 列表

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "token": "8f3c...a91e2b",
    "username": "admin",
    "role": "admin",
    "role_name": "超级管理员",
    "menus": [
      "dashboard",
      "projects",
      "envs",
      "apis",
      "ai-generate",
      "cases",
      "execution",
      "reports",
      "ai-config",
      "users"
    ]
  }
}
```

---

#### 2. 退出登录

`POST /api/auth/logout`

- **描述**：销毁当前 Token。
- **鉴权**：需要

**响应示例**

```json
{
  "code": 0,
  "msg": "已退出登录",
  "data": null
}
```

---

#### 3. 获取当前用户

`GET /api/auth/me`

- **描述**：返回当前登录用户的用户名、角色名称与实际菜单权限。
- **鉴权**：需要

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "username": "admin",
    "role": "admin",
    "role_name": "超级管理员",
    "menus": [
      "dashboard",
      "projects",
      "envs",
      "apis",
      "ai-generate",
      "cases",
      "execution",
      "reports",
      "ai-config",
      "users"
    ]
  }
}
```

---

### 项目管理（5 个）

#### 4. 项目列表

`GET /api/projects`

- **描述**：返回全部项目，并附带每个项目的接口数、用例数。
- **鉴权**：需要

**查询参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `keyword` | string | 否 | `` | 项目名称模糊搜索 |

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "id": 1,
      "name": "电商中台接口",
      "description": "订单/用户/商品",
      "owner": "admin",
      "api_count": 4,
      "case_count": 28,
      "created_at": "2026-10-27 11:20:03"
    }
  ]
}
```

---

#### 5. 创建项目

`POST /api/projects`

- **描述**：新建测试项目，创建者为当前登录用户。
- **鉴权**：需要

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `name` | string | 是 | - | 项目名称 |
| `description` | string | 否 | `` | 项目描述 |

请求示例：

```json
{
  "name": "",
  "description": ""
}
```

**响应示例**

```json
{
  "code": 0,
  "msg": "项目创建成功",
  "data": {
    "id": 1
  }
}
```

---

#### 6. 编辑项目

`PUT /api/projects/{pid}`

- **描述**：修改项目名称与描述。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `pid` | integer | 是 | - | 项目ID |

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `name` | string | 是 | - | 项目名称 |
| `description` | string | 否 | `` | 项目描述 |

请求示例：

```json
{
  "name": "",
  "description": ""
}
```

**响应示例**

```json
{
  "code": 0,
  "msg": "项目更新成功",
  "data": null
}
```

---

#### 7. 删除项目

`DELETE /api/projects/{pid}`

- **描述**：删除项目，级联清除该项目下的环境、接口、用例与执行任务。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `pid` | integer | 是 | - | 项目ID |

**说明**

- 危险操作：级联删除不可恢复

**响应示例**

```json
{
  "code": 0,
  "msg": "项目已删除",
  "data": null
}
```

---

#### 8. 项目概览

`GET /api/projects/{pid}/overview`

- **描述**：返回项目基本信息与接口数、用例数、环境数。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `pid` | integer | 是 | - | 项目ID |

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "project": {
      "id": 1,
      "name": "电商中台接口",
      "description": "订单/用户/商品",
      "owner": "admin"
    },
    "api_count": 4,
    "case_count": 28,
    "env_count": 2
  }
}
```

---

### 环境配置（4 个）

#### 9. 环境列表

`GET /api/projects/{pid}/envs`

- **描述**：返回项目下所有测试环境，默认环境排在首位。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `pid` | integer | 是 | - | 项目ID |

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "id": 1,
      "project_id": 1,
      "name": "本地Mock环境",
      "base_url": "http://127.0.0.1:8099",
      "headers": [
        {
          "key": "Authorization",
          "value": "mock"
        }
      ],
      "timeout": 10,
      "retry": 1,
      "is_default": 1
    }
  ]
}
```

---

#### 10. 创建环境

`POST /api/projects/{pid}/envs`

- **描述**：新增测试环境；若设为默认环境，会自动取消该项目下其它环境的默认标记。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `pid` | integer | 是 | - | 项目ID |

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `name` | string | 是 | - | 环境名称 |
| `base_url` | string | 是 | - | 接口域名/BaseURL |
| `headers` | array<object> | 否 | `[]` | 全局请求头 [{"key","value"}] |
| `timeout` | integer | 否 | `10` | 单请求超时（秒） |
| `retry` | integer | 否 | `0` | 失败重试次数 |
| `is_default` | boolean | 否 | `False` | 是否为默认环境 |

请求示例：

```json
{
  "name": "",
  "base_url": "",
  "headers": [],
  "timeout": 10,
  "retry": 0,
  "is_default": false
}
```

**响应示例**

```json
{
  "code": 0,
  "msg": "环境创建成功",
  "data": {
    "id": 1
  }
}
```

---

#### 11. 编辑环境

`PUT /api/envs/{eid}`

- **描述**：修改指定环境配置。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `eid` | integer | 是 | - | 环境ID |

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `name` | string | 是 | - | 环境名称 |
| `base_url` | string | 是 | - | 接口域名/BaseURL |
| `headers` | array<object> | 否 | `[]` | 全局请求头 |
| `timeout` | integer | 否 | `10` | 超时（秒） |
| `retry` | integer | 否 | `0` | 重试次数 |
| `is_default` | boolean | 否 | `False` | 默认环境 |

请求示例：

```json
{
  "name": "",
  "base_url": "",
  "headers": [],
  "timeout": 10,
  "retry": 0,
  "is_default": false
}
```

**响应示例**

```json
{
  "code": 0,
  "msg": "环境更新成功",
  "data": null
}
```

---

#### 12. 删除环境

`DELETE /api/envs/{eid}`

- **描述**：删除指定测试环境。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `eid` | integer | 是 | - | 环境ID |

**响应示例**

```json
{
  "code": 0,
  "msg": "环境已删除",
  "data": null
}
```

---

### 接口管理（7 个）

#### 13. 接口列表（分页）

`GET /api/projects/{pid}/apis`

- **描述**：分页返回项目下接口，支持名称/路径模糊搜索。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `pid` | integer | 是 | - | 项目ID |

**查询参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `keyword` | string | 否 | `` | 名称或路径模糊搜索 |
| `page` | integer | 否 | `1` | 页码 |
| `size` | integer | 否 | `10` | 每页条数 |

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "total": 4,
    "list": [
      {
        "id": 1,
        "project_id": 1,
        "name": "查询用户列表",
        "method": "GET",
        "path": "/api/users",
        "module": "用户管理",
        "headers": {},
        "query_params": {
          "page": 1,
          "size": 10
        },
        "body": {},
        "response_schema": {
          "code": 0,
          "data": {
            "total": 100
          }
        }
      }
    ]
  }
}
```

---

#### 14. 接口全量列表

`GET /api/projects/{pid}/apis/all`

- **描述**：不分页返回项目下全部接口，供下拉选择/批量操作使用。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `pid` | integer | 是 | - | 项目ID |

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "id": 1,
      "name": "查询用户列表",
      "method": "GET",
      "path": "/api/users",
      "module": "用户管理"
    }
  ]
}
```

---

#### 15. 接口详情

`GET /api/apis/{aid}`

- **描述**：返回单个接口的完整定义（请求头/查询参数/请求体/响应结构）。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `aid` | integer | 是 | - | 接口ID |

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "id": 1,
    "name": "查询用户列表",
    "method": "GET",
    "path": "/api/users",
    "module": "用户管理",
    "headers": {},
    "query_params": {},
    "body": {},
    "response_schema": {}
  }
}
```

---

#### 16. 新增接口

`POST /api/projects/{pid}/apis`

- **描述**：手动录入被测接口定义。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `pid` | integer | 是 | - | 项目ID |

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `name` | string | 是 | - | 接口名称 |
| `method` | string | 否 | `GET` | 请求方法 |
| `path` | string | 否 | `/` | 接口路径 |
| `module` | string | 否 | `默认模块` | 所属模块 |
| `headers` | object | 否 | `{}` | 请求头 |
| `query_params` | object | 否 | `{}` | 查询参数 |
| `body` | object | 否 | `{}` | 请求体 |
| `response_schema` | object | 否 | `{}` | 响应结构 |

请求示例：

```json
{
  "name": "",
  "method": "GET",
  "path": "/",
  "module": "默认模块",
  "headers": {},
  "query_params": {},
  "body": {},
  "response_schema": {}
}
```

**响应示例**

```json
{
  "code": 0,
  "msg": "接口创建成功",
  "data": {
    "id": 1
  }
}
```

---

#### 17. 编辑接口

`PUT /api/apis/{aid}`

- **描述**：修改接口定义。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `aid` | integer | 是 | - | 接口ID |

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `name` | string | 是 | - | 接口名称 |
| `method` | string | 否 | `GET` | 请求方法 |
| `path` | string | 否 | `/` | 接口路径 |
| `module` | string | 否 | `默认模块` | 所属模块 |
| `headers` | object | 否 | `{}` | 请求头 |
| `query_params` | object | 否 | `{}` | 查询参数 |
| `body` | object | 否 | `{}` | 请求体 |
| `response_schema` | object | 否 | `{}` | 响应结构 |

请求示例：

```json
{
  "name": "",
  "method": "GET",
  "path": "/",
  "module": "默认模块",
  "headers": {},
  "query_params": {},
  "body": {},
  "response_schema": {}
}
```

**响应示例**

```json
{
  "code": 0,
  "msg": "接口更新成功",
  "data": null
}
```

---

#### 18. 删除接口

`DELETE /api/apis/{aid}`

- **描述**：删除接口，并级联删除其下的全部测试用例。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `aid` | integer | 是 | - | 接口ID |

**响应示例**

```json
{
  "code": 0,
  "msg": "接口已删除",
  "data": null
}
```

---

#### 19. 上传接口文档解析

`POST /api/projects/{pid}/apis/upload`

- **描述**：上传接口文档自动解析批量入库，同 method+path 自动去重。支持 5 类格式：OpenAPI/Swagger（json/yaml）、Postman Collection（json）、PDF、HTML、Markdown/文本。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `pid` | integer | 是 | - | 项目ID |

**查询参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `file` | file(binary) | 是 | - | 文档文件，multipart/form-data 上传，≤20MB |

**说明**

- Content-Type: multipart/form-data
- 支持后缀：.json / .yaml / .yml / .pdf / .html / .htm / .md / .txt，其他后缀返回 400
- PDF 需为文本版（Word/Markdown 导出），扫描件图片版无法提取文本
- PDF/HTML 解析为启发式：识别「请求方法+接口路径」行或「接口名称/接口路径/请求方式」标签，并解析含「参数名/类型/必填/说明」的参数表，按 GET/DELETE→query、其余→body 归类

**响应示例**

```json
{
  "code": 0,
  "msg": "接口文档解析完成，共 12 个有效接口，新增入库 9 个（重复已跳过）",
  "data": {
    "parsed": 12,
    "inserted": 9
  }
}
```

---

### 用例管理（8 个）

#### 20. 用例列表（分页）

`GET /api/projects/{pid}/cases`

- **描述**：多条件筛选分页查询用例，结果按【模块→接口→用例类型→优先级】标准化排序。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `pid` | integer | 是 | - | 项目ID |

**查询参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `api_id` | integer | 否 | - | 按接口筛选 |
| `case_type` | string | 否 | `` | 用例类型：正向/反向/边界/异常 |
| `priority` | string | 否 | `` | 优先级：P0/P1/P2 |
| `keyword` | string | 否 | `` | 用例名称模糊搜索 |
| `page` | integer | 否 | `1` | 页码 |
| `size` | integer | 否 | `10` | 每页条数 |

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "total": 28,
    "list": [
      {
        "id": 1,
        "project_id": 1,
        "api_id": 1,
        "api_name": "查询用户列表",
        "method": "GET",
        "path": "/api/users",
        "module": "用户管理",
        "name": "查询用户列表-正向-正常分页查询",
        "case_type": "正向",
        "priority": "P0",
        "steps": "1. 构造分页参数 2. 发起GET请求 3. 校验响应",
        "request_data": {
          "page": 1,
          "size": 10
        },
        "expected": {
          "status_code": 200,
          "body_contains": "code"
        },
        "source": "AI",
        "last_status": "passed"
      }
    ]
  }
}
```

---

#### 21. 用例详情

`GET /api/cases/{cid}`

- **描述**：返回单条用例完整定义。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `cid` | integer | 是 | - | 用例ID |

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "id": 1,
    "name": "查询用户列表-正向-正常分页查询",
    "case_type": "正向",
    "priority": "P0",
    "request_data": {},
    "expected": {
      "status_code": 200
    }
  }
}
```

---

#### 22. 新增用例

`POST /api/projects/{pid}/cases`

- **描述**：手动创建测试用例，source 标记为 MANUAL。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `pid` | integer | 是 | - | 项目ID |

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `api_id` | integer | 是 | - | 所属接口ID |
| `name` | string | 是 | - | 用例名称 |
| `case_type` | string | 否 | `正向` | 用例类型 |
| `priority` | string | 否 | `P1` | 优先级 |
| `steps` | string | 否 | `` | 测试步骤描述 |
| `request_data` | object | 否 | `{}` | 请求数据（query/body） |
| `expected` | object | 否 | `{}` | 预期结果（状态码/响应包含等断言） |

请求示例：

```json
{
  "api_id": 0,
  "name": "",
  "case_type": "正向",
  "priority": "P1",
  "steps": "",
  "request_data": {},
  "expected": {}
}
```

**响应示例**

```json
{
  "code": 0,
  "msg": "用例创建成功",
  "data": {
    "id": 1
  }
}
```

---

#### 23. 编辑用例

`PUT /api/cases/{cid}`

- **描述**：修改测试用例。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `cid` | integer | 是 | - | 用例ID |

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `api_id` | integer | 是 | - | 所属接口ID |
| `name` | string | 是 | - | 用例名称 |
| `case_type` | string | 否 | `正向` | 用例类型 |
| `priority` | string | 否 | `P1` | 优先级 |
| `steps` | string | 否 | `` | 测试步骤 |
| `request_data` | object | 否 | `{}` | 请求数据 |
| `expected` | object | 否 | `{}` | 预期结果 |

请求示例：

```json
{
  "api_id": 0,
  "name": "",
  "case_type": "正向",
  "priority": "P1",
  "steps": "",
  "request_data": {},
  "expected": {}
}
```

**响应示例**

```json
{
  "code": 0,
  "msg": "用例更新成功",
  "data": null
}
```

---

#### 24. 删除用例

`DELETE /api/cases/{cid}`

- **描述**：删除单条用例。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `cid` | integer | 是 | - | 用例ID |

**响应示例**

```json
{
  "code": 0,
  "msg": "用例已删除",
  "data": null
}
```

---

#### 25. 批量删除用例

`POST /api/cases/batch-delete`

- **描述**：按 ID 批量删除用例。请求体为整型 ID 数组，或对象 {"ids": [...]} 两种形式均可。
- **鉴权**：需要

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `ids` | array<integer> | 是 | - | 用例ID数组（请求体直接传数组 [1,2,3]，或对象 {"ids":[1,2,3]}） |

请求示例：

```json
{
  "ids": []
}
```

**说明**

- Content-Type: application/json
- 请求体为顶层数组时直接传 [1,2,3]，无需包裹字段

**响应示例**

```json
{
  "code": 0,
  "msg": "已删除 5 条用例",
  "data": null
}
```

---

#### 26. 快速执行用例

`POST /api/cases/run`

- **描述**：立即执行单条或批量选中的用例，返回执行任务ID。环境优先级：显式 env_id → 项目默认环境 → 项目首个环境。
- **鉴权**：需要

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `ids` | array<integer> | 否 | `[]` | 用例ID数组（批量执行） |
| `case_id` | integer | 否 | `0` | 单条用例ID（单条执行） |
| `env_id` | integer | 否 | - | 执行环境ID，不传则用项目默认/首个环境 |

请求示例：

```json
{
  "ids": [],
  "case_id": 0,
  "env_id": 0
}
```

**说明**

- 任务异步执行，需轮询 /api/execution/{task_id}/status 获取进度
- 请求 URL = 环境 BaseURL + 接口路径；接口路径若已是 http(s) 完整地址则直接使用
- 项目无任何环境且接口路径非完整 URL 时，返回 400 提示先配置环境

**响应示例**

```json
{
  "code": 0,
  "msg": "执行任务已启动",
  "data": {
    "task_id": 12,
    "total": 5
  }
}
```

---

#### 27. 用例全量列表

`GET /api/projects/{pid}/cases/all`

- **描述**：不分页返回项目下全部用例（含接口与模块信息）。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `pid` | integer | 是 | - | 项目ID |

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "id": 1,
      "name": "查询用户列表-正向-正常分页查询",
      "module": "用户管理",
      "method": "GET",
      "path": "/api/users",
      "case_type": "正向",
      "priority": "P0"
    }
  ]
}
```

---

### AI 能力（6 个）

#### 28. 获取 AI 配置

`GET /api/ai/config`

- **描述**：读取系统级 AI 配置，api_key 明文返回供前端回填，另附脱敏字段。
- **鉴权**：需要

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "model": "deepseek-chat",
    "api_key": "sk-xxxx",
    "api_key_masked": "sk-xx****xxxx",
    "base_url": "https://api.deepseek.com/v1",
    "timeout": 60,
    "configured": true
  }
}
```

---

#### 29. 保存 AI 配置

`POST /api/ai/config`

- **描述**：保存模型、Key、BaseURL、超时时间，全局即时生效。
- **鉴权**：需要

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `model` | string | 否 | `deepseek-chat` | 模型标识 |
| `api_key` | string | 否 | `` | API Key |
| `base_url` | string | 否 | `https://api.deepseek.com/v1` | OpenAI 兼容接口地址 |
| `timeout` | integer | 否 | `60` | 请求超时（秒，5-600） |

请求示例：

```json
{
  "model": "deepseek-chat",
  "api_key": "",
  "base_url": "https://api.deepseek.com/v1",
  "timeout": 60
}
```

**说明**

- 未配置 API Key 时，用例生成自动降级为内置规则引擎

**响应示例**

```json
{
  "code": 0,
  "msg": "AI 配置保存成功，已全局生效",
  "data": null
}
```

---

#### 30. 测试 AI 连通性

`POST /api/ai/config/test`

- **描述**：用传入配置（或已保存配置）发起一次真实调用，验证可用性。
- **鉴权**：需要

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `model` | string | 否 | `deepseek-chat` | 模型标识 |
| `api_key` | string | 否 | `` | API Key |
| `base_url` | string | 否 | `https://api.deepseek.com/v1` | 接口地址 |
| `timeout` | integer | 否 | `60` | 超时（秒） |

请求示例：

```json
{
  "model": "deepseek-chat",
  "api_key": "",
  "base_url": "https://api.deepseek.com/v1",
  "timeout": 60
}
```

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "success": true,
    "message": "连接成功：模型响应正常"
  }
}
```

---

#### 31. AI 生成测试用例

`POST /api/ai/generate`

- **描述**：为单个接口或整个项目批量生成测试用例；生成前自动清除该接口的旧 AI 用例，避免重复堆积。
- **鉴权**：需要

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `project_id` | integer | 是 | - | 项目ID |
| `scope` | string | 否 | `all` | 生成范围 |
| `api_id` | integer | 否 | - | 接口ID（scope=single 时必填） |
| `gen_type` | string | 否 | `full` | 生成类型 |

请求示例：

```json
{
  "project_id": 0,
  "scope": "all",
  "api_id": 0,
  "gen_type": "full"
}
```

**说明**

- positive = 仅正向用例；full = 正向 + 反向 + 边界 + 异常
- used_ai=false 表示未配置 Key，已降级使用内置规则引擎

**响应示例**

```json
{
  "code": 0,
  "msg": "成功生成 28 条用例",
  "data": {
    "api_count": 4,
    "case_count": 28,
    "used_ai": false,
    "engine": "内置规则引擎（降级）"
  }
}
```

---

#### 32. AI 整理用例文档

`POST /api/ai/organize/{pid}`

- **描述**：统一规范化项目下所有用例的命名、优先级与类型，并按【模块→接口→类型→优先级】归档。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `pid` | integer | 是 | - | 项目ID |

**响应示例**

```json
{
  "code": 0,
  "msg": "用例文档整理完成：共 28 条用例已按标准格式分类归档",
  "data": {
    "total": 28,
    "normalized": 3,
    "order_rule": "按 模块 → 接口 → 用例类型（正向/反向/边界/异常）→ 优先级（P0/P1/P2）自动分类归档"
  }
}
```

---

#### 33. 可选模型列表

`GET /api/ai/models`

- **描述**：返回系统内置可选择的模型清单。
- **鉴权**：需要

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "value": "deepseek-chat",
      "label": "DeepSeek Chat"
    },
    {
      "value": "gpt-4o-mini",
      "label": "GPT-4o mini"
    },
    {
      "value": "qwen-max",
      "label": "通义千问 Max"
    },
    {
      "value": "custom",
      "label": "自定义兼容模型"
    }
  ]
}
```

---

### 测试执行（4 个）

#### 34. 启动执行任务

`POST /api/execution/start`

- **描述**：按项目+环境+范围创建执行任务并立即异步启动，返回任务ID。
- **鉴权**：需要

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `project_id` | integer | 是 | - | 项目ID |
| `env_id` | integer | 否 | - | 环境ID，不传则用默认环境 |
| `scope` | string | 否 | `all` | 执行范围 |
| `case_ids` | array<integer> | 否 | `[]` | 用例ID数组（scope=selected） |
| `task_name` | string | 否 | `` | 任务名称，留空自动生成 |

请求示例：

```json
{
  "project_id": 0,
  "env_id": 0,
  "scope": "all",
  "case_ids": [],
  "task_name": ""
}
```

**说明**

- scope=failed 时自动筛选上一次执行失败的用例

**响应示例**

```json
{
  "code": 0,
  "msg": "任务已启动",
  "data": {
    "task_id": 12,
    "total": 28
  }
}
```

---

#### 35. 任务状态与实时日志

`GET /api/execution/{task_id}/status`

- **描述**：轮询接口：返回任务进度统计与增量日志（前端 1s 轮询实现实时滚动效果）。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `task_id` | integer | 是 | - | 任务ID |

**查询参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `log_after` | integer | 否 | `0` | 增量拉取日志起始ID，0=全部 |

**说明**

- 建议轮询间隔 1000ms，单次最多返回 200 条日志

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "task": {
      "id": 12,
      "name": "测试任务-001",
      "status": "running",
      "total": 28,
      "executed": 10,
      "passed": 7,
      "failed": 3,
      "env_name": "本地Mock环境",
      "started_at": "2026-10-27 11:30:00"
    },
    "running": true,
    "logs": [
      {
        "id": 101,
        "level": "INFO",
        "message": "[3/28] 执行用例：用户登录-反向-密码错误"
      }
    ]
  }
}
```

---

#### 36. 终止执行任务

`POST /api/execution/{task_id}/stop`

- **描述**：向运行中的任务发送终止指令，已执行结果保留。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `task_id` | integer | 是 | - | 任务ID |

**响应示例**

```json
{
  "code": 0,
  "msg": "终止指令已发送",
  "data": null
}
```

---

#### 37. 重跑失败用例

`POST /api/execution/{task_id}/rerun-failed`

- **描述**：提取指定任务中的失败用例，创建新任务重新执行。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `task_id` | integer | 是 | - | 原任务ID |

**响应示例**

```json
{
  "code": 0,
  "msg": "已创建重跑任务，共 19 条失败用例",
  "data": {
    "task_id": 13,
    "total": 19
  }
}
```

---

### 测试报告（4 个）

#### 38. 报告列表

`GET /api/reports/project/{pid}`

- **描述**：分页返回项目下的历史执行任务（即测试报告），含通过率。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `pid` | integer | 是 | - | 项目ID |

**查询参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `page` | integer | 否 | `1` | 页码 |
| `size` | integer | 否 | `10` | 每页条数 |

**说明**

- `env_base_url` 为执行时的环境域名快照，用于确认该次执行打到哪台机器；环境被删除后 `env_deleted=true` 且域名无法回溯（仅保留名称）

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "total": 3,
    "list": [
      {
        "id": 12,
        "name": "测试任务-001",
        "status": "completed",
        "total": 28,
        "executed": 28,
        "passed": 9,
        "failed": 19,
        "pass_rate": 32.1,
        "env_name": "本地Mock环境",
        "env_base_url": "http://127.0.0.1:8099",
        "env_deleted": false,
        "created_at": "2026-10-27 11:30:00"
      }
    ]
  }
}
```

---

#### 39. 报告详情

`GET /api/reports/{task_id}`

- **描述**：返回报告全量数据：任务概览、通过率、每条用例执行结果、模块成功率、完整执行日志。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `task_id` | integer | 是 | - | 任务ID |

**说明**

- `results[].request_info.url` 为环境域名 + 接口路径拼接后的最终请求地址，是确认「实际打到哪个环境」的最直接证据

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "task": {
      "id": 12,
      "name": "测试任务-001",
      "status": "completed",
      "total": 28,
      "executed": 28,
      "passed": 9,
      "failed": 19,
      "env_name": "本地Mock环境",
      "env_base_url": "http://127.0.0.1:8099",
      "env_deleted": false
    },
    "pass_rate": 32.1,
    "results": [
      {
        "case_id": 1,
        "case_name": "查询用户列表-正向-正常分页查询",
        "module": "用户管理",
        "method": "GET",
        "path": "/api/users",
        "status": "passed",
        "status_code": 200,
        "duration_ms": 12,
        "request_info": {
          "method": "get",
          "url": "http://127.0.0.1:8099/api/users",
          "headers": {},
          "params": {
            "page": 1
          }
        },
        "response": {
          "code": 0,
          "data": {}
        },
        "assertions": [
          {
            "name": "状态码校验",
            "expected": 200,
            "actual": 200,
            "passed": true
          }
        ],
        "fail_reason": ""
      }
    ],
    "module_stats": [
      {
        "module": "鉴权模块",
        "total": 6,
        "passed": 6,
        "rate": 100.0
      }
    ],
    "logs": [
      {
        "id": 1,
        "level": "INFO",
        "message": "任务启动：共 28 条用例"
      },
      {
        "id": 2,
        "level": "INFO",
        "message": "执行环境：本地Mock环境（http://127.0.0.1:8099）　超时 10s　重试 1次"
      }
    ]
  }
}
```

---

#### 40. 导出报告文件

`GET /api/reports/{task_id}/export`

- **描述**：导出测试报告为 HTML / Excel / PDF 文件（二进制流）。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `task_id` | integer | 是 | - | 任务ID |

**查询参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `fmt` | string | 否 | `html` | 导出格式 |
| `download` | integer | 否 | `1` | 1=下载附件，0=HTML在线预览（仅html） |

**响应示例**

返回文件二进制流，响应头 `Content-Disposition: attachment; filename=...`。

---

#### 41. 删除报告

`DELETE /api/reports/{task_id}`

- **描述**：删除报告，级联清除用例结果与执行日志。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `task_id` | integer | 是 | - | 任务ID |

**响应示例**

```json
{
  "code": 0,
  "msg": "报告已删除",
  "data": null
}
```

---

### 仪表盘（1 个）

#### 42. 首页统计数据

`GET /api/dashboard`

- **描述**：聚合返回项目数、接口数、用例数、近7天通过率趋势、用例状态分布、最近10条任务。
- **鉴权**：需要

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "projects": 1,
    "apis": 4,
    "cases": 28,
    "week_rate": 32.1,
    "trend": [
      {
        "date": "10-27",
        "executed": 28,
        "passed": 9,
        "rate": 32.1
      }
    ],
    "pie": {
      "passed": 9,
      "failed": 19,
      "skipped": 0,
      "pending": 0
    },
    "recent": [
      {
        "id": 12,
        "name": "测试任务-001",
        "pass_rate": 32.1
      }
    ]
  }
}
```

---

### 用户与权限（9 个）

#### 43. 菜单目录

`GET /api/menus`

- **描述**：返回平台全部功能菜单（权限最小单元）的定义，含 key / 标题 / 图标 / 路由。
- **鉴权**：需要

**说明**

- 所有管理接口均要求调用方拥有 users 菜单权限（即超级管理员）

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "key": "dashboard",
      "title": "首页仪表盘",
      "icon": "DataLine",
      "path": "/dashboard"
    }
  ]
}
```

---

#### 44. 角色列表

`GET /api/roles`

- **描述**：返回全部角色及其菜单权限集合，内置角色（is_system=true）不可删除。
- **鉴权**：需要

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "id": 1,
      "name": "超级管理员",
      "code": "admin",
      "description": "拥有平台全部功能与系统配置权限",
      "menu_keys": [
        "dashboard",
        "projects",
        "envs",
        "apis",
        "ai-generate",
        "cases",
        "execution",
        "reports",
        "ai-config",
        "users"
      ],
      "is_system": true
    }
  ]
}
```

---

#### 45. 创建角色

`POST /api/roles`

- **描述**：新建角色并配置其菜单权限集合。
- **鉴权**：需要

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `name` | string | 是 | - | 角色名称 |
| `code` | string | 是 | - | 角色编码（英文唯一标识） |
| `description` | string | 否 | `` | 角色描述 |
| `menu_keys` | array | 否 | `[]` | 菜单 key 取自「菜单目录」接口，对应前端左侧功能入口；权限模型见下方说明。 |

请求示例：

```json
{
  "name": "",
  "code": "",
  "description": "",
  "menu_keys": "[]"
}
```

**说明**

- code 不可与已有角色重复

**响应示例**

```json
{
  "code": 0,
  "msg": "角色创建成功",
  "data": {
    "id": 4
  }
}
```

---

#### 46. 编辑角色

`PUT /api/roles/{rid}`

- **描述**：修改角色名称、描述与菜单权限；内置角色的 code 不可修改。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `rid` | integer | 是 | - | 角色ID |

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `name` | string | 是 | - | 角色名称 |
| `code` | string | 否 | `` | 角色编码（内置角色忽略） |
| `description` | string | 否 | `` | 角色描述 |
| `menu_keys` | array | 否 | `[]` | 菜单 key 取自「菜单目录」接口，对应前端左侧功能入口；权限模型见下方说明。 |

请求示例：

```json
{
  "name": "",
  "code": "",
  "description": "",
  "menu_keys": "[]"
}
```

**响应示例**

```json
{
  "code": 0,
  "msg": "角色更新成功",
  "data": null
}
```

---

#### 47. 删除角色

`DELETE /api/roles/{rid}`

- **描述**：删除自定义角色；内置角色不可删，已绑定用户的角色需先调整用户后再删。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `rid` | integer | 是 | - | 角色ID |

**说明**

- 内置角色不可删除
- 仍有用户绑定的角色不可删除

**响应示例**

```json
{
  "code": 0,
  "msg": "角色已删除",
  "data": null
}
```

---

#### 48. 用户列表

`GET /api/users`

- **描述**：返回全部用户（不含密码），附带角色名称与实际菜单权限。
- **鉴权**：需要

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "id": 1,
      "username": "admin",
      "nickname": "管理员",
      "role_id": 1,
      "role_name": "超级管理员",
      "status": "active",
      "menus": [
        "dashboard",
        "projects",
        "envs",
        "apis",
        "ai-generate",
        "cases",
        "execution",
        "reports",
        "ai-config",
        "users"
      ],
      "created_at": "2026-10-27 11:20:03"
    }
  ]
}
```

---

#### 49. 创建用户

`POST /api/users`

- **描述**：新建用户并分配角色；菜单权限优先使用传入的 menu_keys，为空则继承所选角色权限。
- **鉴权**：需要

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `username` | string | 是 | - | 登录用户名（唯一） |
| `password` | string | 是 | - | 初始密码（至少6位） |
| `nickname` | string | 否 | `` | 昵称 |
| `role_id` | integer | 是 | - | 所属角色ID |
| `status` | string | 否 | `active` | 账号状态：active / disabled |
| `menu_keys` | array | 否 | `[]` | 菜单 key 取自「菜单目录」接口，对应前端左侧功能入口；权限模型见下方说明。 |

请求示例：

```json
{
  "username": "",
  "password": "",
  "nickname": "",
  "role_id": 0,
  "status": "active",
  "menu_keys": "[]"
}
```

**响应示例**

```json
{
  "code": 0,
  "msg": "用户创建成功",
  "data": {
    "id": 2
  }
}
```

---

#### 50. 编辑用户

`PUT /api/users/{uid}`

- **描述**：修改用户昵称、密码（留空则不改）、角色、状态与菜单权限。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `uid` | integer | 是 | - | 用户ID |

**请求体（application/json）**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `nickname` | string | 否 | `` | 昵称 |
| `password` | string | 否 | `` | 新密码（留空不修改，至少6位） |
| `role_id` | integer | 否 | - | 所属角色ID |
| `status` | string | 否 | `active` | 账号状态：active / disabled |
| `menu_keys` | array | 否 | `[]` | 菜单 key 取自「菜单目录」接口，对应前端左侧功能入口；权限模型见下方说明。 |

请求示例：

```json
{
  "nickname": "",
  "password": "",
  "role_id": 0,
  "status": "active",
  "menu_keys": "[]"
}
```

**说明**

- 不能禁用或变更当前登录账号自身
- 至少需保留一名拥有 users 权限的管理员

**响应示例**

```json
{
  "code": 0,
  "msg": "用户更新成功",
  "data": null
}
```

---

#### 51. 删除用户

`DELETE /api/users/{uid}`

- **描述**：删除指定用户，需管理员权限。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `uid` | integer | 是 | - | 用户ID |

**说明**

- 不能删除当前登录账号
- 至少需保留一名管理员

**响应示例**

```json
{
  "code": 0,
  "msg": "用户已删除",
  "data": null
}
```

---

### 系统服务（3 个）

#### 52. 健康检查

`GET /api/health`

- **描述**：服务存活探测，无需鉴权。
- **鉴权**：不需要

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "status": "running",
    "product": "AI驱动Web接口自动化测试平台"
  }
}
```

---

#### 53. 操作日志

`GET /api/logs`

- **描述**：返回最近 50 条系统操作日志。
- **鉴权**：需要

**响应示例**

```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "id": 1,
      "username": "admin",
      "action": "AI生成用例",
      "detail": "项目#1 接口4个 生成用例28条",
      "created_at": "2026-10-27 11:25:00"
    }
  ]
}
```

---

#### 54. 导出用例文档

`GET /api/projects/{pid}/cases/export`

- **描述**：导出项目用例文档为 Word / Excel / PDF 文件（二进制流）。
- **鉴权**：需要

**路径参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `pid` | integer | 是 | - | 项目ID |

**查询参数**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `fmt` | string | 否 | `word` | 导出格式 |

**响应示例**

返回文件二进制流，响应头 `Content-Disposition: attachment; filename=...`。

---

## 四、数据字典

### 4.1 核心表

| 表名 | 说明 | 主要字段 |
|---|---|---|
| `users` | 用户 | id, username, password(哈希), role |
| `tokens` | 登录令牌 | token, user_id |
| `projects` | 测试项目 | id, name, description, owner, created_at |
| `environments` | 测试环境 | id, project_id, name, base_url, headers, timeout, retry, is_default |
| `apis` | 被测接口 | id, project_id, name, method, path, module, headers, query_params, body, response_schema |
| `cases` | 测试用例 | id, project_id, api_id, name, case_type, priority, steps, request_data, expected, source, last_status |
| `tasks` | 执行任务/报告 | id, project_id, name, env_id, env_name, case_ids, status, total, executed, passed, failed, created_at |
| `case_results` | 用例执行结果 | id, task_id, case_id, case_name, module, status, status_code, duration_ms, request, response, assertions, fail_reason |
| `task_logs` | 执行日志 | id, task_id, level, message |
| `op_logs` | 操作审计日志 | id, username, action, detail, created_at |
| `ai_config` | AI 配置 | id, model, api_key, base_url, timeout |

### 4.2 枚举值

| 字段 | 取值 |
|---|---|
| `case_type` | 正向 / 反向 / 边界 / 异常 |
| `priority` | P0 / P1 / P2 |
| `case.source` | AI（AI生成） / MANUAL（手动创建） |
| `case.last_status` / `result.status` | passed / failed / skipped / pending |
| `task.status` | pending / running / completed / stopped |
| `log.level` | INFO / WARN / ERROR |

---

## 五、调用示例

### 5.1 登录并拉取仪表盘（curl）

```bash
# 1. 登录获取 token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['token'])")

# 2. 携带 token 调用业务接口
curl -s http://127.0.0.1:8000/api/dashboard -H "Authorization: $TOKEN"
```

### 5.2 完整自动化流程（Python）

```python
import requests

BASE = "http://127.0.0.1:8000"
s = requests.Session()

# 1. 登录
tok = s.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin123"}').json()["data"]["token"]
s.headers.update({"Authorization": tok})

# 2. 创建项目
pid = s.post(f"{BASE}/api/projects", json={"name": "示例项目"}).json()["data"]["id"]

# 3. 创建环境
s.post(f"{BASE}/api/projects/{pid}/envs", json={
    "name": "本地Mock环境", "base_url": "http://127.0.0.1:8099",
    "headers": [{"key": "Authorization", "value": "mock"}],
    "timeout": 10, "retry": 1, "is_default": True
})

# 4. AI 生成用例（未配 Key 时自动降级规则引擎）
s.post(f"{BASE}/api/ai/generate", json={"project_id": pid, "scope": "all", "gen_type": "full"})

# 5. 启动执行任务
task_id = s.post(f"{BASE}/api/execution/start", json={"project_id": pid, "scope": "all"}).json()["data"]["task_id"]

# 6. 轮询任务状态
import time
while True:
    r = s.get(f"{BASE}/api/execution/{task_id}/status").json()["data"]
    print(r["task"]["executed"], "/", r["task"]["total"])
    if not r["running"]:
        break
    time.sleep(1)

# 7. 获取报告
report = s.get(f"{BASE}/api/reports/{task_id}").json()["data"]
print("通过率:", report["pass_rate"])
```

---

## 六、变更记录

| 版本 | 日期 | 说明 |
|---|---|---|
| 1.0.0 | 2026-10-27 | 首个正式版本，覆盖 8 大能力域共 54 个接口 |
