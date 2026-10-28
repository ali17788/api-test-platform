# -*- coding: utf-8 -*-
"""演示用的本地 Mock 接口服务（用于验证执行引擎），端口 8099"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs


class MockHandler(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):  # 静音日志
        pass

    def _handle(self, method):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        try:
            body = json.loads(raw) if raw else {}
        except Exception:
            body = {}

        if path == "/api/login":
            if not body.get("username") or not body.get("password"):
                return self._json(400, {"code": 400, "msg": "参数缺失"})
            if len(str(body.get("password") or "")) > 100:
                return self._json(400, {"code": 400, "msg": "密码长度超限"})
            return self._json(200, {"code": 0, "token": "mock-token-abc", "msg": "登录成功"})

        if path == "/api/users":
            try:
                page = int(qs.get("page", ["1"])[0])
                size = int(qs.get("size", ["10"])[0])
            except Exception:
                return self._json(400, {"code": 400, "msg": "分页参数类型错误"})
            if page < 1 or size < 1 or size > 100:
                return self._json(400, {"code": 400, "msg": "分页参数非法"})
            if page > 5:
                return self._json(200, {"code": 0, "data": [], "total": 42})
            data = [{"id": i, "name": f"user{i}"} for i in range((page - 1) * size, (page - 1) * size + min(size, 3))]
            return self._json(200, {"code": 0, "data": data, "total": 42})

        if path.startswith("/api/users/"):
            uid = path.rsplit("/", 1)[-1]
            if not uid.isdigit():
                return self._json(400, {"code": 400, "msg": "用户ID非法"})
            return self._json(200, {"code": 0, "data": {"id": int(uid), "name": f"user{uid}"}})

        if path == "/api/secure/profile":
            if not self.headers.get("Authorization"):
                return self._json(401, {"code": 401, "msg": "未授权"})
            return self._json(200, {"code": 0, "data": {"name": "admin"}})

        return self._json(404, {"code": 404, "msg": "接口不存在"})

    def do_GET(self): self._handle("GET")
    def do_POST(self): self._handle("POST")
    def do_PUT(self): self._handle("PUT")
    def do_DELETE(self): self._handle("DELETE")


if __name__ == "__main__":
    print("Mock API 服务已启动：http://127.0.0.1:8099")
    HTTPServer(("127.0.0.1", 8099), MockHandler).serve_forever()
