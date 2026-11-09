#!/usr/bin/env python3
"""생활 장부 Supabase 도우미 (자동 작업·대화용). 비밀 키는 네트워크 프록시가 apikey 헤더에 넣어줌.
사용:
  python3 db.py list <collection> [month]          → [{id, version, data}] JSON
  python3 db.py get <collection> <id>
  python3 db.py create <collection> <id> '<json>'  → 이미 있으면 "exists" 출력(덮어쓰지 않음)
  python3 db.py set <collection> <id> '<json>'     → 덮어쓰기(없으면 생성)
  python3 db.py update <collection> <id> '<json>' [version] → 필드 병합. version 주면 그 버전일 때만(아니면 "conflict")
  python3 db.py delete <collection> <id>
"""
import json, sys, urllib.request, urllib.parse
B = "https://cwyvuiwfrkelnmpmynzk.supabase.co/rest/v1/docs"
OWNER = "f4198aa1-1e1b-4bf2-afb8-6ec0fa077e6b"
H = {"apikey": "proxy-injected", "Content-Type": "application/json"}

def req(method, qs="", body=None, prefer=None):
    h = dict(H)
    if prefer: h["Prefer"] = prefer
    r = urllib.request.Request(B + qs, method=method, headers=h,
                               data=None if body is None else json.dumps(body, ensure_ascii=False).encode())
    with urllib.request.urlopen(r, timeout=20) as res:
        t = res.read().decode()
        return json.loads(t) if t else None

q = lambda **kw: "?" + urllib.parse.urlencode(kw, safe=",.*()>-")

def main(a):
    cmd, col = a[0], a[1]
    if cmd == "list":
        kw = {"collection": f"eq.{col}", "select": "id,version,data", "order": "id"}
        if len(a) > 2: kw["data->>month"] = f"eq.{a[2]}"
        return req("GET", q(**kw))
    _id = a[2]
    key = {"collection": f"eq.{col}", "id": f"eq.{_id}"}
    if cmd == "get":
        r = req("GET", q(**key, select="id,version,data")); return r[0] if r else None
    if cmd == "delete":
        return req("DELETE", q(**key), prefer="return=representation")
    data = json.loads(a[3])
    row = [{"owner": OWNER, "collection": col, "id": _id, "data": data}]
    if cmd == "create":
        r = req("POST", "?on_conflict=owner,collection,id", row, "resolution=ignore-duplicates,return=representation")
        return "created" if r else "exists"
    if cmd == "set":
        req("POST", "?on_conflict=owner,collection,id", row, "resolution=merge-duplicates,return=minimal"); return "ok"
    if cmd == "update":
        cur = main(["get", col, _id])
        if not cur: return "not_found"
        if len(a) > 4 and str(cur["version"]) != str(a[4]): return "conflict"
        merged = {**cur["data"], **data}
        r = req("PATCH", q(**key, version=f"eq.{cur['version']}"), {"data": merged}, "return=representation")
        return {"version": r[0]["version"]} if r else "conflict"
    raise SystemExit("unknown command")

if __name__ == "__main__":
    try:
        print(json.dumps(main(sys.argv[1:]), ensure_ascii=False))
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:300]); sys.exit(1)
