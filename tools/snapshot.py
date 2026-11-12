#!/usr/bin/env python3
"""생활 장부 요약 스냅샷 → CSV (대화 옆 요약 페이지용). 앱의 calc/planCalc 규칙을 그대로 따름.
사용: python3 tools/snapshot.py <출력폴더> [YYYY-MM]
"""
import csv, json, os, subprocess, sys, calendar, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
KST = dt.timezone(dt.timedelta(hours=9))

def L(col, *a):
    return [dict(id=r["id"], **r["data"]) for r in json.loads(subprocess.check_output(["python3", os.path.join(HERE, "db.py"), "list", col, *a]))]

def own(e): return max(0, (e.get("amount") or 0) - (e.get("reimb") or 0))
def method(e): return e.get("method") or "신한"

def main(out, month=None):
    now = dt.datetime.now(KST)
    m = month or now.strftime("%Y-%m")
    y, mo = map(int, m.split("-")); dim = calendar.monthrange(y, mo)[1]
    day_now = now.day if m == now.strftime("%Y-%m") else dim
    pm = (dt.date(y, mo, 1) - dt.timedelta(days=1)).strftime("%Y-%m")

    S = {k: v for k, v in [(r["id"], r) for r in L("settings")]}.get("main", {})
    budget = S.get("varBudget") or 0
    incen_lim = S.get("incenMonthly") if S.get("incenMonthly") not in (None, "") else 1000000
    ex = L("expenses", m); plans = L("plans", m); inv = L("invest"); todos = L("todos")

    var_t = sum(own(e) for e in ex)
    incen_used = sum(e["amount"] for e in ex if method(e) == "인센")
    unp = [e for e in ex if e.get("unplanned") and not e.get("plan")]

    # 일정 반영 계획선 (앱 planCalc와 동일)
    plan_t = sum(p.get("budget") or 0 for p in plans); base = max(budget - plan_t, 0)
    def dayin(d):
        if not d: return 1
        if d[:7] < m: return 1
        if d[:7] > m: return dim
        return int(d[8:10]) or 1
    daily = [0.0] + [base / dim] * dim; act = [0.0] * (dim + 1)
    for p in plans:
        s = dayin(p.get("date")); e = max(s, dayin(p.get("endDate") or p.get("date")))
        for d in range(s, e + 1): daily[d] += (p.get("budget") or 0) / (e - s + 1)
    for e in ex:
        if not e.get("selfcare"): act[dayin(e.get("date"))] += own(e)
    pc, ac = [0.0], [0.0]
    for d in range(1, dim + 1): pc.append(pc[-1] + daily[d]); ac.append(ac[-1] + act[d])

    by_plan = {}
    for e in ex:
        if e.get("plan"): by_plan[e["plan"]] = by_plan.get(e["plan"], 0) + own(e)

    # 신한 통장(연결 계좌): 기준 잔액 − 기준 시각 이후 신한 결제
    sh = next((x for x in inv if x.get("link")), None); sh_bal = None
    if sh:
        recent = ex + L("expenses", pm)
        sh_bal = (sh.get("baseAmount") or 0) - sum(e["amount"] for e in recent if method(e) == sh["link"] and (e.get("createdAt") or 0) > (sh.get("baseAt") or 0))
    toss = next((x for x in inv if x.get("account") == "토스뱅크"), None)

    os.makedirs(out, exist_ok=True)
    def W(name, rows, cols):
        with open(os.path.join(out, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)

    W("summary.csv", [dict(
        month=m, asOf=now.strftime("%Y-%m-%d %H:%M"), day=day_now, days=dim,
        budget=budget, spent=var_t, left=budget - var_t,
        planToDate=round(pc[day_now]), actualToDate=round(ac[day_now]), diff=round(ac[day_now] - pc[day_now]),
        incenLimit=incen_lim, incenUsed=incen_used, incenLeft=incen_lim - incen_used,
        shinhan=sh_bal if sh_bal is not None else "", toss=(toss or {}).get("value", ""),
        unplannedCount=len(unp), unplannedTotal=sum(own(e) for e in unp),
    )], ["month", "asOf", "day", "days", "budget", "spent", "left", "planToDate", "actualToDate", "diff",
         "incenLimit", "incenUsed", "incenLeft", "shinhan", "toss", "unplannedCount", "unplannedTotal"])

    W("daily.csv", [dict(day=d, plan=round(pc[d]), actual=round(ac[d]) if d <= day_now else "") for d in range(1, dim + 1)],
      ["day", "plan", "actual"])

    cats = {}
    for e in ex: cats[e.get("category") or "기타"] = cats.get(e.get("category") or "기타", 0) + own(e)
    W("categories.csv", [dict(category=k, amount=v) for k, v in sorted(cats.items(), key=lambda kv: -kv[1]) if v > 0],
      ["category", "amount"])

    W("plans.csv", [dict(id=p["id"], name=p["name"], start=p.get("date", ""), end=p.get("endDate") or p.get("date", ""),
                         budget=p.get("budget") or 0, spent=by_plan.get(p["id"], 0)) for p in sorted(plans, key=lambda p: p.get("date", ""))],
      ["id", "name", "start", "end", "budget", "spent"])

    rec = sorted([e for e in ex if own(e) > 0], key=lambda e: (e.get("date", ""), e.get("createdAt") or 0), reverse=True)[:10]
    W("recent.csv", [dict(id=e["id"], date=e.get("date", ""), memo=e.get("memo", ""), category=e.get("category", ""),
                          method=method(e), amount=own(e), unplanned="Y" if e.get("unplanned") else "") for e in rec],
      ["id", "date", "memo", "category", "method", "amount", "unplanned"])

    op = sorted([t for t in todos if not t.get("done")], key=lambda t: t.get("due") or "9999")[:8]
    W("todos.csv", [dict(id=t["id"], due=t.get("due", ""), title=t.get("title", ""), prio=t.get("prio", "")) for t in op],
      ["id", "due", "title", "prio"])
    print("ok", m, out)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
