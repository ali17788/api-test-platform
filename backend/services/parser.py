# -*- coding: utf-8 -*-
"""接口文档解析服务

支持格式：
  1. OpenAPI / Swagger（json、yaml）
  2. Postman Collection v2.x（json）
  3. PDF  —— 文本型接口文档（Word/Markdown 导出的接口说明书）
  4. HTML —— 网页版接口文档（ShowDoc / 语雀 / Wiki / Swagger 静态页等表格型文档）
  5. Markdown / 纯文本接口说明（.md / .txt）

PDF / HTML / 文本走同一套「启发式解析引擎」：
  接口识别（方法+路径行 / 标签式字段 / 表格行）+ 参数表识别（表头列映射）
"""
import io
import json
import os
import re

import yaml

SUPPORTED_EXT = (".json", ".yaml", ".yml", ".pdf", ".html", ".htm", ".xhtml", ".md", ".markdown", ".txt")

METHODS = ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS")
_METHOD_RE = re.compile(r"(?:^|[\s\|\-—:,：（(])(" + "|".join(METHODS) + r")(?:$|[\s\|\-—:,：）)])")
_PATH_RE = re.compile(r"((?:https?://[^\s，,；;）)\]｜|]+)|(?:/[A-Za-z0-9_\\\-\./:{}\$][A-Za-z0-9_\\\-\./:{}\$]*))")

# 参数表表头别名
_ALIAS = {
    "name": ("参数名", "字段名", "字段", "名称", "参数", "参数名称", "key"),
    "type": ("类型", "数据类型", "参数类型", "字段类型", "type"),
    "required": ("必填", "是否必填", "必选", "是否必须", "required"),
    "desc": ("说明", "描述", "备注", "含义", "参数说明", "字段说明", "desc"),
    "default": ("默认值", "示例", "示例值", "样例", "default", "example"),
}
_TYPE_SAMPLE = {
    "int": 1, "integer": 1, "long": 1, "number": 1, "float": 1.0, "double": 1.0,
    "boolean": True, "bool": True, "array": [], "object": {}, "file": "",
    "date": "2025-01-01", "datetime": "2025-01-01 00:00:00",
}


# ============================================================
# 入口
# ============================================================
def parse_document(filename: str, content: bytes):
    """返回 (apis, err)。apis: [{name,method,path,module,headers,query_params,body,response_schema}]"""
    ext = os.path.splitext((filename or "").lower())[1]
    if ext == ".pdf":
        return _parse_pdf(content)
    if ext in (".html", ".htm", ".xhtml"):
        return _parse_html(content)
    if ext in (".md", ".markdown", ".txt"):
        text = _smart_decode(content)
        return _finish_text(text, "文本")
    # 未知后缀（如 .docx/.xlsx/.doc）：先按文本试一次，仍无结果则明确提示
    if ext and ext not in SUPPORTED_EXT:
        text = _smart_decode(content)
        apis = _parse_text_doc(text)
        if apis:
            return apis, None
        return None, f"不支持的文件类型 {ext}，当前支持：{' / '.join(SUPPORTED_EXT)}"
    # json / yaml / 其他：按原逻辑尝试结构化解析
    text = _smart_decode(content)
    data = None
    try:
        data = json.loads(text)
    except Exception:
        try:
            data = yaml.safe_load(text)
        except Exception:
            if ext not in (".json", ".yaml", ".yml"):
                # 非结构化后缀：最后尝试文本启发式
                return _finish_text(text, "文本")
            return None, "文件内容既非 JSON 也非 YAML，无法解析"
    if not isinstance(data, dict):
        return None, "文档结构不合法（顶层应为对象）"
    if "info" in data and "item" in data and ("schema" in (data.get("info") or {})):
        return _parse_postman(data), None
    if "openapi" in data or "swagger" in data:
        return _parse_openapi(data), None
    if "paths" in data:
        return _parse_openapi(data), None
    return None, "无法识别文档类型：仅支持 OpenAPI/Swagger、Postman Collection、PDF、HTML 格式"


def _infer_headings(lines):
    """PDF 文本标题还原：
    - 编号标题（3.1 xxx / 4.2 xxx）→ 3 级（接口名）
    - 短行且其下 4 行内出现接口定义 → 2 级（模块名）
    """
    api_idx = {i for i, (lv, t) in enumerate(lines) if _is_api_line(t)}
    out = []
    for i, (lv, t) in enumerate(lines):
        if lv:
            out.append((lv, t))
            continue
        cells = _split_row(t) or []
        if len(t) > 24 or _is_api_line(t) or _is_param_header(cells):
            out.append((0, t))
            continue
        if re.match(r"^\d+(?:[.\-]\d+)*[\s、]", t):
            out.append((3, t))
            continue
        # 模块名特征：短、不含空格、非分隔行、非参数说明行
        if (len(t) <= 20 and " " not in t and "（" not in t
                and not all(re.fullmatch(r"[-:：\s]+", c) for c in cells)
                and any(j in api_idx for j in range(i + 1, min(len(lines), i + 5)))):
            out.append((2, t))
            continue
        out.append((0, t))
    return out


def _finish_text(text, source):
    return _finish_blocks(_parse_text_doc_lines(text), source)


def _finish_blocks(apis, source):
    if not apis:
        return None, (f"已读取{source}内容，但未识别到接口定义。"
                      "请确认文档中包含「请求方法 + 接口路径」信息，例如：POST /api/login，"
                      "或以「接口名称 / 接口路径 / 请求方式」标签形式描述。")
    return apis, None


def _smart_decode(content: bytes) -> str:
    head = content[:2048].decode("latin-1", errors="ignore")
    enc = None
    m = re.search(r'charset\s*=\s*["\']?\s*([\w\-]+)', head, re.I)
    if m:
        enc = m.group(1).lower()
    for e in [enc, "utf-8", "gbk", "gb18030", "big5", "latin-1"]:
        if not e:
            continue
        try:
            return content.decode(e)
        except Exception:
            continue
    return content.decode("utf-8", errors="ignore")


# ============================================================
# PDF
# ============================================================
def _parse_pdf(content: bytes):
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return None, "缺少 PDF 解析依赖，请安装：pip install pypdf"
    try:
        reader = PdfReader(io.BytesIO(content))
    except Exception as e:
        return None, f"PDF 读取失败：{e}"
    pages = []
    try:
        for p in reader.pages:
            pages.append(p.extract_text() or "")
    except Exception as e:
        return None, f"PDF 文本提取失败：{e}"
    text = "\n".join(pages)
    if len(text.strip()) < 10:
        return None, ("PDF 未提取到文本内容，可能是扫描件/图片版文档。"
                      "请提供文本版 PDF（由 Word / Markdown 导出），或改用 HTML 版本。")
    lines = []
    for ln in _normalize_pdf_text(text).splitlines():
        ln = ln.strip()
        if ln:
            lines.append((0, ln))
    # PDF 抽取后标题层级信息丢失，需启发式还原（模块/接口名）
    return _finish_blocks(_parse_blocks(_infer_headings(lines)), "PDF")


def _normalize_pdf_text(text: str) -> str:
    """PDF 抽取文本常出现断行、缺空格，做轻度规整"""
    lines = []
    for ln in text.splitlines():
        ln = ln.replace("\xa0", " ").replace("\t", " ").strip()
        if ln:
            lines.append(ln)
    return "\n".join(lines)


# ============================================================
# HTML
# ============================================================
def _parse_html(content: bytes):
    text = _smart_decode(content)
    lines, tables = _html_to_blocks(text)
    if not lines:
        # 纯文本兜底（可能是不带标签的片段）
        lines = [(0, ln.strip()) for ln in text.splitlines() if ln.strip()]
    apis = _parse_blocks(lines)
    if not apis:
        return None, ("已读取 HTML 内容，但未识别到接口定义。"
                      "请确认页面中包含「请求方法 + 接口路径」，例如 POST /api/login，"
                      "或存在含「参数名 / 类型 / 说明」的参数表格。")
    return apis, None


def _html_to_blocks(html_text: str):
    """返回 (lines, tables)。lines: [(heading_level, text)]，表格行以 ' | ' 拼接成文本行"""
    lines, tables = [], []
    try:
        from lxml import html as lhtml
    except ImportError:
        return _fallback_html_blocks(html_text)
    try:
        doc = lhtml.fromstring(html_text)
    except Exception:
        return _fallback_html_blocks(html_text)
    for el in doc.xpath("//script | //style | //noscript"):
        parent = el.getparent()
        if parent is not None:
            parent.remove(el)

    table_set = set()
    for tb in doc.xpath("//table"):
        rows = []
        for tr in tb.xpath(".//tr"):
            cells = [_clean(c.text_content()) for c in tr.xpath(".//th | .//td")]
            if any(cells):
                rows.append(cells)
        if rows:
            tables.append(rows)
            table_set.update(id(r) for r in rows)

    heading_tags = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}

    def emit(el):
        tag = el.tag if isinstance(el.tag, str) else ""
        tag = tag.lower()
        txt = _clean(el.text_content())
        if not txt:
            return
        if tag in heading_tags:
            lines.append((heading_tags[tag], txt))
        elif tag == "tr":
            cells = [_clean(c.text_content()) for c in el.xpath(".//th | .//td")]
            cells = [c for c in cells if c]
            lines.append((0, " | ".join(cells) if len(cells) > 1 else (cells[0] if cells else txt)))
        elif tag in ("p", "li", "pre", "code", "dt", "dd", "caption", "summary", "title"):
            lines.append((0, txt))

    for el in doc.iter():
        if not isinstance(el.tag, str):
            continue
        tag = el.tag.lower()
        if tag in heading_tags or tag in ("p", "li", "pre", "code", "dt", "dd", "caption", "summary", "title", "tr"):
            emit(el)
    return lines, tables


def _fallback_html_blocks(html_text: str):
    """无 lxml 时的标准库兜底解析"""
    from html.parser import HTMLParser

    class _P(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.lines = []
            self.tables = []
            self._rows = None
            self._cells = None
            self._buf = []
            self._tag = None

        def handle_starttag(self, tag, attrs):
            tag = tag.lower()
            if tag == "table":
                self._rows = []
            elif tag == "tr" and self._rows is not None:
                self._cells = []
            elif tag in ("td", "th") and self._cells is not None:
                self._buf = []
                self._tag = "cell"
            elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                self._buf = []
                self._tag = "h" + tag[1]
            elif tag in ("p", "li", "pre", "code"):
                self._buf = []
                self._tag = "p"

        def handle_endtag(self, tag):
            tag = tag.lower()
            txt = _clean("".join(self._buf))
            if tag in ("td", "th") and self._cells is not None:
                self._cells.append(txt)
                self._buf = []
                self._tag = None
            elif tag == "tr" and self._rows is not None:
                cells = [c for c in (self._cells or []) if c]
                if cells:
                    self._rows.append(cells)
                    self.lines.append((0, " | ".join(cells) if len(cells) > 1 else cells[0]))
                self._cells = None
                self._tag = None
            elif tag == "table" and self._rows is not None:
                if self._rows:
                    self.tables.append(self._rows)
                self._rows = None
            elif tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "pre", "code"):
                if txt:
                    lvl = int(tag[1]) if tag.startswith("h") else 0
                    self.lines.append((lvl, txt))
                self._buf = []
                self._tag = None

        def handle_data(self, data):
            if self._tag is not None:
                self._buf.append(data)

    p = _P()
    try:
        p.feed(html_text)
    except Exception:
        pass
    return p.lines, p.tables


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


# ============================================================
# 启发式解析引擎（PDF 文本 / HTML 文本 / Markdown 共用）
# ============================================================
def _parse_text_doc(text: str):
    return _parse_blocks(_parse_text_doc_lines(text))


def _parse_text_doc_lines(text: str):
    lines = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        level = 0
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            level, ln = len(m.group(1)), m.group(2).strip()
        lines.append((level, ln))
    return _parse_blocks(lines)


def _parse_blocks(lines):
    apis = _scan_text(lines)
    if not apis:
        apis = _scan_labels(lines)
    if not apis:
        return []
    _attach_params(apis, lines)
    for a in apis:
        a.pop("_idx", None)
    return apis


def _mk(name, method, path, module, idx=0):
    return {
        "name": (name or f"{method} {path}").strip()[:100],
        "method": (method or "GET").upper(),
        "path": _norm_path(path),
        "module": (module or "默认模块").strip()[:50],
        "headers": {},
        "query_params": {},
        "body": {},
        "response_schema": {},
        "_idx": idx,
    }


def _norm_path(path: str) -> str:
    p = (path or "").strip().strip("，,。.；;：:）)")
    if p.startswith("http"):
        try:
            from urllib.parse import urlparse
            p = urlparse(p).path or "/"
        except Exception:
            p = "/"
    if not p.startswith("/"):
        p = "/" + p
    return p or "/"


def _scan_text(lines):
    """从「方法 + 路径」文本行识别接口"""
    apis, seen = [], set()
    for i, (lv, t) in enumerate(lines):
        ms = list(_METHOD_RE.finditer(t))
        if not ms:
            continue
        for m in ms:
            method = m.group(1).upper()
            rest = t[m.end():]
            pm = _PATH_RE.search(rest) or _PATH_RE.search(t)
            if not pm:
                continue
            path = pm.group(1)
            if len(path) < 2 and not path.startswith("/"):
                continue
            key = (method, _norm_path(path))
            if key in seen:
                continue
            seen.add(key)
            # 名称：同行剩余文本 → 上方「接口名称」标签 → 上方最近标题
            tail = t.replace(m.group(0), " ", 1).replace(path, " ", 1)
            tail = re.sub(r"^[\s\|\-—:：,，]+|[\s\|\-—:：,，]+$", "", tail).strip()
            name, name_level = "", 0
            if len(tail) >= 2 and not _looks_like_label(tail) and not _PATH_RE.search(tail):
                name = _clean_name(tail)
            else:
                for j in range(i - 1, max(-1, i - 8), -1):
                    lv2, t2 = lines[j]
                    mm = re.search(r"(?:接口名称|接口名|名称|功能名称)\s*[:：]\s*(.+)", t2)
                    if mm:
                        name = _clean_name(mm.group(1))
                        break
                    if lv2 and 2 <= len(t2) <= 40 and not _is_api_line(t2):
                        name, name_level = _clean_name(t2), lv2
                        break
            # 模块：比接口名更高层级的标题，或「所属模块」标签
            module = None
            for j in range(i - 1, max(-1, i - 40), -1):
                lv2, t2 = lines[j]
                mm = re.search(r"(?:所属模块|模块|分组|分类)\s*[:：]\s*(.+)", t2)
                if mm:
                    module = mm.group(1).strip()
                    break
                if lv2 and (name_level == 0 or lv2 < name_level) and len(t2) <= 30 \
                        and _clean_name(t2) != name and not _is_api_line(t2):
                    module = _clean_name(t2)
                    break
            apis.append(_mk(name, method, path, module, i))
            break
    return apis


def _clean_name(s: str) -> str:
    """清理标题中的编号前缀与装饰符号：'3.1 查询用户列表' -> '查询用户列表'"""
    s = (s or "").strip().strip("*·-—").strip()
    s = re.sub(r"^\d+(?:[.\-]\d+)*\s*[、.．]?\s*", "", s)
    return s.strip()[:60]


def _is_api_line(t: str) -> bool:
    return bool(_METHOD_RE.search(t) and _PATH_RE.search(t))


def _looks_like_label(s: str) -> bool:
    return bool(re.match(r"^(接口名称|接口名|名称|请求方式|请求方法|方法|接口路径|请求地址|接口地址|URL|路径)\s*[:：]", s))


def _scan_labels(lines):
    """标签式文档：接口名称 / 接口路径 / 请求方式 分行书写"""
    apis, cur, start_idx = [], {}, 0

    def flush(idx):
        if cur.get("path"):
            apis.append(_mk(cur.get("name"), cur.get("method", "GET"), cur["path"],
                            cur.get("module"), cur.get("_start", idx)))
        cur.clear()

    re_name = re.compile(r"(?:接口名称|接口名|功能名称|^名称)\s*[:：]\s*(.+)")
    re_path = re.compile(r"(?:接口路径|请求地址|接口地址|请求URL|接口URL|URL|url|路径|Path|path)\s*[:：]\s*(.+)")
    re_meth = re.compile(r"(?:请求方式|请求方法|方法|Method|method|HTTP方法)\s*[:：]\s*\**\s*(" + "|".join(METHODS) + r")")
    re_mod = re.compile(r"(?:所属模块|模块|分组|分类)\s*[:：]\s*(.+)")

    for i, (lv, t) in enumerate(lines):
        m = re_name.search(t)
        if m and not re_path.search(t) and not re_meth.search(t):
            flush(i)
            cur["name"] = m.group(1).strip()
            cur["_start"] = i          # 接口块起始行，用于参数归属
            continue
        m = re_path.search(t)
        if m:
            cur.setdefault("_start", i)
            cur["path"] = m.group(1).strip()
            continue
        m = re_meth.search(t)
        if m:
            cur.setdefault("_start", i)
            cur["method"] = m.group(1).upper()
            continue
        m = re_mod.search(t)
        if m:
            cur.setdefault("_start", i)
            cur["module"] = m.group(1).strip()
            continue
    flush(len(lines))
    # 去重
    out, seen = [], set()
    for a in apis:
        k = (a["method"], a["path"])
        if k in seen:
            continue
        seen.add(k)
        out.append(a)
    return out


def _attach_params(apis, lines):
    """按接口所在区间，向下寻找参数表并填充 query/body/response"""
    bounds = []
    for i, a in enumerate(apis):
        start = a.get("_idx", 0)
        end = apis[i + 1].get("_idx", len(lines)) if i + 1 < len(apis) else len(lines)
        bounds.append((start, end))

    for a, (start, end) in zip(apis, bounds):
        i = start
        while i < end:
            lv, t = lines[i]
            cells = _split_row(t)
            if cells and _is_param_header(cells):
                cmap = _map_columns(cells)
                if cmap.get("name") is None:
                    i += 1
                    continue
                pipe_mode = "|" in t          # Markdown / HTML 表格：行内带分隔符
                ncol = len(cells)
                scope = _scope_of(lines, i, a["method"])
                i += 1
                while i < end:
                    raw = lines[i][1]
                    row = _split_row(raw)
                    if not row:
                        i += 1
                        continue
                    # 表格分隔行（--- / :--:）跳过
                    if all(re.fullmatch(r"[-:：\s]+", c) for c in row):
                        i += 1
                        continue
                    # 越界即停：新表头 / 新接口行 / 脱离表格模式 / 字段名不合法
                    if _is_param_header(row) or _is_api_line(raw):
                        break
                    if pipe_mode and "|" not in raw:
                        break
                    if not pipe_mode and len(row) < max(3, ncol - 2):
                        break
                    fname = row[cmap["name"]] if cmap["name"] < len(row) else ""
                    if not _valid_field_name(fname):
                        break
                    _add_field(a, row, cmap, scope)
                    i += 1
            else:
                i += 1


def _valid_field_name(name: str) -> bool:
    """字段名合法性：字母/下划线/中文开头，且不含空格（避免把标题句当成参数行）"""
    return bool(re.match(r"^[A-Za-z_\u4e00-\u9fa5][A-Za-z0-9_\.\-\u4e00-\u9fa5]*$", name or ""))


def _split_row(t: str):
    """把一行拆成单元格：优先 Markdown/HTML 表格的 '|' 分隔，其次按空白分隔（PDF 抽取文本常见）"""
    s = t.strip()
    if "|" in s:
        s = re.sub(r"^\||\|$", "", s)
        cells = [c.strip() for c in s.split("|")]
        cells = [c for c in cells if c not in ("", "---", ":--", "--:", ":-:")]
        return cells if cells else None
    if not s:
        return None
    return s.split()


def _is_param_header(cells):
    joined = " ".join(cells).lower()
    if len(cells) < 2:
        return False
    has_name = any(k in joined for k in _ALIAS["name"])
    has_other = any(k in joined for k in _ALIAS["type"] + _ALIAS["required"] + _ALIAS["desc"])
    # 表头单元格通常很短
    return has_name and has_other and max(len(c) for c in cells) <= 12


def _map_columns(cells):
    cmap = {}
    lower = [c.lower() for c in cells]
    for key, aliases in _ALIAS.items():
        for idx, c in enumerate(lower):
            if any(a in c for a in aliases):
                cmap[key] = idx
                break
    return cmap


def _scope_of(lines, i, method):
    """判断参数归属：query / body / response"""
    for j in range(i - 1, max(-1, i - 6), -1):
        t = lines[j][1]
        if re.search(r"(响应|返回|出参|响应参数|返回参数)", t) and len(t) < 40:
            return "response"
        if re.search(r"(query|查询参数|url参数|请求行参数|路径参数)", t, re.I) and len(t) < 40:
            return "query"
        if re.search(r"(请求体|请求参数|body|报文体|json参数|入参)", t, re.I) and len(t) < 40:
            return "body"
    return "query" if method in ("GET", "DELETE", "HEAD") else "body"


def _add_field(api, row, cmap, scope):
    def cell(key):
        idx = cmap.get(key)
        if idx is None or idx >= len(row):
            return ""
        return row[idx].strip()

    name = cell("name")
    if not name or len(name) > 40:
        return
    if re.search(r"^(参数名|字段名|名称|参数)$", name):
        return
    typ = cell("type").lower()
    req = cell("required")
    desc = cell("desc")
    default = cell("default")
    if default:
        val = _cast(default, typ)
    else:
        val = _TYPE_SAMPLE.get(typ, name if typ in ("string", "str", "") else "")
        if typ == "string" or typ == "str" or not typ:
            val = default or _guess_value(name, desc)
    meta = {"type": typ or "string", "required": req in ("是", "Y", "y", "true", "必填", "必选", "True"),
            "desc": desc}
    if scope == "response":
        api["response_schema"][name] = meta
    elif scope == "query":
        api["query_params"][name] = val
    else:
        api["body"][name] = val


def _cast(v, typ):
    if typ in ("int", "integer", "long", "number"):
        try:
            return int(v)
        except Exception:
            try:
                return float(v)
            except Exception:
                return 1
    if typ in ("float", "double"):
        try:
            return float(v)
        except Exception:
            return 1.0
    if typ in ("boolean", "bool"):
        return str(v).lower() in ("true", "1", "是")
    return v


def _guess_value(name, desc):
    n = (name or "").lower()
    if any(k in n for k in ("page", "页码")):
        return 1
    if any(k in n for k in ("size", "limit", "count")):
        return 10
    if any(k in n for k in ("id",)):
        return 1
    if any(k in n for k in ("phone", "mobile")):
        return "13800000000"
    if any(k in n for k in ("email",)):
        return "test@example.com"
    if any(k in n for k in ("time", "date")):
        return "2025-01-01"
    return "test"


# ============================================================
# 结构化文档：OpenAPI / Postman（原有实现）
# ============================================================
def _parse_openapi(spec: dict):
    base = spec.get("basePath", "")
    apis = []
    for path, methods in (spec.get("paths") or {}).items():
        for method, op in (methods or {}).items():
            if method.lower() not in ("get", "post", "put", "delete", "patch"):
                continue
            if not isinstance(op, dict):
                continue
            name = op.get("summary") or op.get("operationId") or f"{method.upper()} {path}"
            module = (op.get("tags") or ["默认模块"])[0]
            query_params, headers = {}, {}
            for p in op.get("parameters", []) or []:
                if not isinstance(p, dict):
                    continue
                if p.get("in") == "query":
                    query_params[p.get("name", "")] = _sample(p.get("schema") or {}, p.get("example"))
                elif p.get("in") == "header":
                    headers[p.get("name", "")] = str(p.get("example") or "")
            body = {}
            rb = op.get("requestBody") or {}
            content = (rb.get("content") or {})
            json_ct = content.get("application/json") or {}
            if json_ct:
                body = _sample(json_ct.get("schema") or {}, None, True)
            resp_codes = {}
            for code, resp in (op.get("responses") or {}).items():
                if isinstance(resp, dict):
                    rc = (resp.get("content") or {}).get("application/json") or {}
                    resp_codes[str(code)] = rc.get("schema") or {}
            apis.append({
                "name": str(name)[:100],
                "method": method.upper(),
                "path": (base + path) if base else path,
                "module": str(module),
                "headers": headers,
                "query_params": query_params,
                "body": body,
                "response_schema": resp_codes,
            })
    return apis


def _parse_postman(col: dict):
    apis = []
    info = col.get("info") or {}
    root_name = info.get("name") or "默认模块"

    def walk(items, module):
        for it in items or []:
            if not isinstance(it, dict):
                continue
            if "item" in it:  # folder
                walk(it.get("item"), it.get("name") or module)
                continue
            req = it.get("request") or {}
            url = req.get("url") or {}
            if isinstance(url, dict):
                raw = url.get("raw", "")
                path = "/" + "/".join(url.get("path") or [])
                qp = {q.get("key", ""): (q.get("value") or "") for q in (url.get("query") or []) if isinstance(q, dict)}
            else:
                raw = str(url)
                path = raw.split("?")[0]
                qp = {}
            headers = {h.get("key", ""): (h.get("value") or "") for h in (req.get("header") or []) if isinstance(h, dict)}
            body = {}
            bd = req.get("body") or {}
            if bd.get("mode") == "raw":
                try:
                    body = json.loads(bd.get("raw") or "{}")
                except Exception:
                    body = {}
            if path.startswith("http"):
                try:
                    from urllib.parse import urlparse
                    path = urlparse(path).path or "/"
                except Exception:
                    path = "/"
            apis.append({
                "name": it.get("name") or path,
                "method": (req.get("method") or "GET").upper(),
                "path": path or "/",
                "module": module or root_name,
                "headers": headers,
                "query_params": qp,
                "body": body,
                "response_schema": {},
            })
    walk(col.get("item"), root_name)
    return apis


def _sample(schema: dict, example, as_body=False, depth=0):
    """根据 JSON Schema 生成示例值"""
    if example is not None:
        return example
    if not isinstance(schema, dict) or depth > 4:
        return "" if as_body else ""
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    t = schema.get("type")
    if t == "object" or "properties" in schema:
        out = {}
        for k, v in (schema.get("properties") or {}).items():
            out[k] = _sample(v, None, False, depth + 1)
        return out
    if t == "array":
        return [_sample(schema.get("items") or {}, None, False, depth + 1)]
    if t == "integer":
        return 1
    if t == "number":
        return 1.0
    if t == "boolean":
        return True
    fmt = schema.get("format", "")
    if fmt in ("date", "date-time"):
        return "2025-01-01"
    if fmt == "email":
        return "test@example.com"
    return "test"


def params_of_api(api_row):
    """从接口行提取可参数化字段（用于 AI 生成）：合并 query + body 顶层字段"""
    from utils import jloads
    query = jloads(api_row["query_params"], {})
    body = jloads(api_row["body"], {})
    fields = []
    for k, v in query.items():
        fields.append({"name": k, "in": "query", "value": v, "type": type(v).__name__})
    if isinstance(body, dict):
        for k, v in body.items():
            fields.append({"name": k, "in": "body", "value": v, "type": type(v).__name__})
    return fields
