# -*- coding: utf-8 -*-
"""首页仪表盘：统计卡片 / 趋势 / 状态分布 / 最近任务"""
from fastapi import APIRouter, Request
from datetime import datetime, timedelta
import db as d
from utils import ok, get_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(request: Request):
    get_user(request)
    projects = d.q1("SELECT COUNT(*) c FROM projects")["c"]
    apis = d.q1("SELECT COUNT(*) c FROM apis")["c"]
    cases = d.q1("SELECT COUNT(*) c FROM cases")["c"]
    users = d.q1("SELECT COUNT(*) c FROM users")["c"]
    roles = d.q1("SELECT COUNT(*) c FROM roles")["c"]

    # 近7天通过率
    rows = d.q("""SELECT date(created_at) d, SUM(executed) ex, SUM(passed) p
                  FROM tasks WHERE date(created_at) >= date('now','-7 days','localtime')
                  GROUP BY date(created_at)""")
    trend_map = {r["d"]: (r["ex"] or 0, r["p"] or 0) for r in rows}
    trend = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        ex, p = trend_map.get(day, (0, 0))
        trend.append({"date": day[-5:], "executed": ex, "passed": p,
                      "rate": round(p / ex * 100, 1) if ex else 0})
    total_ex = sum(r["ex"] or 0 for r in rows)
    total_p = sum(r["p"] or 0 for r in rows)
    week_rate = round(total_p / total_ex * 100, 1) if total_ex else 0

    status_rows = d.q("""SELECT status, COUNT(*) c FROM case_results
                         GROUP BY status""")
    status_map = {r["status"]: r["c"] for r in status_rows}
    pie = {
        "passed": status_map.get("passed", 0),
        "failed": status_map.get("failed", 0),
        "skipped": status_map.get("skipped", 0),
        "pending": max(cases - sum(status_map.values()), 0),
    }
    recent = [d.row_to_dict(r) for r in d.q("SELECT * FROM tasks ORDER BY id DESC LIMIT 10")]
    for r in recent:
        r["pass_rate"] = round(r["passed"] / r["executed"] * 100, 1) if r["executed"] else 0
    return ok({"projects": projects, "apis": apis, "cases": cases, "users": users, "roles": roles,
               "week_rate": week_rate, "trend": trend, "pie": pie, "recent": recent})
