# -*- coding: utf-8 -*-
"""RBAC 模块后端自测：迁移 / 登录 / 菜单 / 角色 / 用户 / 权限隔离"""
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from fastapi.testclient import TestClient
import db as d
import app as appmod

client = TestClient(appmod.app)

def jr(r):
    return r.status_code, r.json()

print("=== 1. 登录(admin) ===")
sc, body = jr(client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}))
assert sc == 200 and body["code"] == 0, body
print("OK", "role_name=", body["data"]["role_name"], "menus=", body["data"]["menus"])
admin_menus = body["data"]["menus"]
assert "users" in admin_menus
token = body["data"]["token"]
H = {"Authorization": token}

print("=== 2. 菜单目录 ===")
sc, body = jr(client.get("/api/menus", headers=H))
assert sc == 200 and len(body["data"]) == 10, body
print("OK 菜单数=", len(body["data"]))

print("=== 3. 角色列表(种子) ===")
sc, body = jr(client.get("/api/roles", headers=H))
assert sc == 200 and len(body["data"]) >= 3, body
print("OK 角色=", [(r["name"], r["code"]) for r in body["data"]])
tester = next(r for r in body["data"] if r["code"] == "tester")
viewer = next(r for r in body["data"] if r["code"] == "viewer")

print("=== 4. 创建角色 ===")
sc, body = jr(client.post("/api/roles", headers=H, json={
    "name": "自定义角色A", "code": "custom_a", "description": "测试",
    "menu_keys": ["dashboard", "projects", "cases"]}))
assert sc == 200 and body["code"] == 0, body
role_id = body["data"]["id"]
print("OK 新建角色 id=", role_id)

print("=== 5. 角色编码唯一校验 ===")
sc, body = jr(client.post("/api/roles", headers=H, json={"name": "重复", "code": "custom_a"}))
assert sc == 400, body
print("OK 重复编码被拒")

print("=== 6. 创建用户(绑定角色 + 额外菜单) ===")
sc, body = jr(client.post("/api/users", headers=H, json={
    "username": "tester1", "password": "tester123", "nickname": "测试员1",
    "role_id": tester["id"], "status": "active", "menu_keys": ["dashboard", "projects", "cases", "reports"]}))
assert sc == 200 and body["code"] == 0, body
uid = body["data"]["id"]
print("OK 新建用户 id=", uid)

print("=== 7. 用户密码强度校验 ===")
sc, body = jr(client.post("/api/users", headers=H, json={"username": "weak", "password": "123", "role_id": viewer["id"]}))
assert sc == 400, body
print("OK 弱密码被拒")

print("=== 8. 用新用户登录，校验菜单 ===")
sc, body = jr(client.post("/api/auth/login", json={"username": "tester1", "password": "tester123"}))
assert sc == 200 and body["code"] == 0, body
print("OK tester1 menus=", body["data"]["menus"])
assert set(body["data"]["menus"]) == {"dashboard", "projects", "cases", "reports"}, body["data"]["menus"]
utoken = body["data"]["token"]
UH = {"Authorization": utoken}

print("=== 9. 普通用户访问用户管理接口应 403 ===")
sc, body = jr(client.get("/api/users", headers=UH))
assert sc == 403, (sc, body)
print("OK 越权访问被拒")
sc, body = jr(client.get("/api/roles", headers=UH))
assert sc == 403, (sc, body)
print("OK 角色列表越权被拒")

print("=== 10. 编辑用户：修改菜单权限 ===")
sc, body = jr(client.put(f"/api/users/{uid}", headers=H, json={"menu_keys": ["dashboard", "projects"], "nickname": "改"}))
assert sc == 200 and body["code"] == 0, body
sc, body = jr(client.post("/api/auth/login", json={"username": "tester1", "password": "tester123"}))
assert set(body["data"]["menus"]) == {"dashboard", "projects"}, body["data"]["menus"]
print("OK 菜单更新生效")

print("=== 11. 不能删除最后一个管理员 ===")
sc, body = jr(client.delete(f"/api/users/{d.q1('SELECT id FROM users WHERE username=?', ('admin',))['id']}", headers=H))
assert sc == 400, (sc, body)
print("OK 删除自身/最后管理员被拒")

print("=== 12. 删除自定义角色(无用户绑定) ===")
sc, body = jr(client.delete(f"/api/roles/{role_id}", headers=H))
assert sc == 200 and body["code"] == 0, body
print("OK 自定义角色已删除")

print("\n全部后端用例通过 ✅")
