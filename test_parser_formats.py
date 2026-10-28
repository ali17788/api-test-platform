# -*- coding: utf-8 -*-
"""生成 PDF / HTML 样例接口文档，并调用解析服务验证解析效果"""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
from services.parser import parse_document  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "samples")
os.makedirs(OUT, exist_ok=True)

SAMPLE_MD = """# 用户中心接口文档

## 用户管理

### 3.1 查询用户列表
GET /api/users

请求参数（Query）

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|---|---|---|---|---|
| page | int | 否 | 页码 | 1 |
| size | int | 否 | 每页条数 | 10 |

### 3.2 创建用户
POST /api/users

请求参数（Body）

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|---|---|---|---|---|
| username | string | 是 | 用户名 | admin |
| phone | string | 是 | 手机号 | 13800000000 |

### 3.3 删除用户
DELETE /api/users/{id}

## 鉴权模块

### 4.1 用户登录
POST /api/login

请求参数（Body）

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|---|---|---|---|---|
| username | string | 是 | 用户名 | admin |
| password | string | 是 | 密码 | 123456 |
"""

SAMPLE_HTML = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>订单服务接口文档</title></head>
<body>
<h1>订单服务 API</h1>
<h2>订单模块</h2>
<h3>创建订单</h3>
<p>POST /api/orders</p>
<table>
<tr><th>参数名</th><th>类型</th><th>必填</th><th>说明</th><th>默认值</th></tr>
<tr><td>product_id</td><td>int</td><td>是</td><td>商品ID</td><td>1</td></tr>
<tr><td>quantity</td><td>int</td><td>是</td><td>购买数量</td><td>2</td></tr>
</table>
<h3>查询订单列表</h3>
<p>GET /api/orders</p>
<table>
<tr><th>参数名</th><th>类型</th><th>必填</th><th>说明</th><th>默认值</th></tr>
<tr><td>page</td><td>int</td><td>否</td><td>页码</td><td>1</td></tr>
<tr><td>status</td><td>string</td><td>否</td><td>订单状态</td><td>paid</td></tr>
</table>
<h2>支付模块</h2>
<h3>发起支付</h3>
<p>POST /api/pay</p>
<table>
<tr><th>参数名</th><th>类型</th><th>必填</th><th>说明</th><th>默认值</th></tr>
<tr><td>order_id</td><td>int</td><td>是</td><td>订单ID</td><td>1</td></tr>
<tr><td>channel</td><td>string</td><td>是</td><td>支付渠道</td><td>wechat</td></tr>
</table>
</body></html>
"""

# 标签式 HTML（ShowDoc 风格：接口名称/请求方式/接口路径分行）
SAMPLE_HTML_LABEL = """<html><head><meta charset="utf-8"></head><body>
<h2>商品模块</h2>
<h3>商品详情</h3>
<p>接口名称：查询商品详情</p>
<p>接口路径：/api/goods/detail</p>
<p>请求方式：POST</p>
<table>
<tr><th>参数名</th><th>类型</th><th>必填</th><th>说明</th><th>默认值</th></tr>
<tr><td>goods_id</td><td>int</td><td>是</td><td>商品ID</td><td>1001</td></tr>
</table>
<h3>商品上下架</h3>
<p>接口名称：商品上下架</p>
<p>接口路径：/api/goods/status</p>
<p>请求方式：PUT</p>
<table>
<tr><th>参数名</th><th>类型</th><th>必填</th><th>说明</th><th>默认值</th></tr>
<tr><td>goods_id</td><td>int</td><td>是</td><td>商品ID</td><td>1001</td></tr>
<tr><td>on_sale</td><td>boolean</td><td>是</td><td>是否上架</td><td>true</td></tr>
</table>
</body></html>
"""


def make_pdf(path):
    """用 reportlab 生成一份中文 PDF 接口文档（模拟 Word 导出版式）"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=15 * mm)
    st = ParagraphStyle("cn", fontName="STSong-Light", fontSize=10.5, leading=16)
    st_h = ParagraphStyle("h", fontName="STSong-Light", fontSize=14, leading=22, spaceAfter=6)
    story = []
    for ln in SAMPLE_MD.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        if ln.startswith("# "):
            story.append(Paragraph(ln[2:], st_h))
        elif ln.startswith("## "):
            story.append(Paragraph(ln[3:], st_h))
        elif ln.startswith("### "):
            story.append(Paragraph(ln[4:], st_h))
        else:
            story.append(Paragraph(ln.replace("|", "  "), st))
        story.append(Spacer(1, 2))
    doc.build(story)
    return path


def main():
    # 1) HTML 表格型
    p = os.path.join(OUT, "接口文档_订单服务.html")
    with open(p, "w", encoding="utf-8") as f:
        f.write(SAMPLE_HTML)
    apis, err = parse_document("接口文档_订单服务.html", open(p, "rb").read())
    print("[HTML-表格型] err=", err, " count=", len(apis or []))
    for a in (apis or []):
        print("   ", a["method"], a["path"], "|", a["name"], "|", a["module"],
              "| query:", a["query_params"], "| body:", a["body"])

    # 2) HTML 标签型
    p2 = os.path.join(OUT, "接口文档_商品模块.html")
    with open(p2, "w", encoding="utf-8") as f:
        f.write(SAMPLE_HTML_LABEL)
    apis2, err2 = parse_document("接口文档_商品模块.html", open(p2, "rb").read())
    print("[HTML-标签型] err=", err2, " count=", len(apis2 or []))
    for a in (apis2 or []):
        print("   ", a["method"], a["path"], "|", a["name"], "|", a["module"], "| body:", a["body"])

    # 3) PDF
    p3 = make_pdf(os.path.join(OUT, "接口文档_用户中心.pdf"))
    apis3, err3 = parse_document("接口文档_用户中心.pdf", open(p3, "rb").read())
    print("[PDF] err=", err3, " count=", len(apis3 or []))
    for a in (apis3 or []):
        print("   ", a["method"], a["path"], "|", a["name"], "|", a["module"],
              "| query:", a["query_params"], "| body:", a["body"])

    # 4) Markdown
    p4 = os.path.join(OUT, "接口文档_用户中心.md")
    with open(p4, "w", encoding="utf-8") as f:
        f.write(SAMPLE_MD)
    apis4, err4 = parse_document("接口文档_用户中心.md", open(p4, "rb").read())
    print("[Markdown] err=", err4, " count=", len(apis4 or []))
    for a in (apis4 or []):
        print("   ", a["method"], a["path"], "|", a["name"], "|", a["module"],
              "| query:", a["query_params"], "| body:", a["body"])

    # 5) 不支持的类型
    apis5, err5 = parse_document("接口.xlsx", b"xxxx")
    print("[不支持类型] err=", err5)


if __name__ == "__main__":
    main()
