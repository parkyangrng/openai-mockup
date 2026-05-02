"""
test.py — Smoke test for the mock API.

Run the server in one terminal:
    uvicorn main:app --port 8000

Run this in another:
    python test.py
"""

import sys
import urllib.request
import urllib.parse
import json

BASE = "http://localhost:8000"
passed = 0
failed = 0


def get(path, **params):
    url = f"{BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body


def check(label, cond, detail=""):
    global passed, failed
    if cond:
        print(f"  PASS  {label}")
        passed += 1
    else:
        print(f"  FAIL  {label} {('— ' + detail) if detail else ''}")
        failed += 1


def section(name):
    print(f"\n{name}")


# ============================================================
section("Meta")
status, body = get("/health")
check("/health returns 200", status == 200)
check("/health returns ok", body.get("status") == "ok")

status, body = get("/")
check("/ returns 200", status == 200)
check("/ exposes /docs link", "docs" in body)

# ============================================================
section("Account lookup — by account_number")
status, body = get("/v1/accounts", account_number="ACC-4722")
check("200 status", status == 200)
check("returns Jane Doe", body.get("customer_name") == "Jane Doe")
check("plan is Internet 200", body.get("current_plan", {}).get("speed_mbps") == 200)
check("balance is 134.18", body.get("balance_due", {}).get("amount") == 134.18)

# ============================================================
section("Account lookup — by phone (multiple formats)")
for phone in ["+15125550172", "5125550172", "(512) 555-0172", "512-555-0172"]:
    status, body = get("/v1/accounts", phone_number=phone)
    check(
        f"format '{phone}' resolves to Jane Doe",
        status == 200 and body.get("customer_name") == "Jane Doe",
    )

# ============================================================
section("Account lookup — by name")
status, body = get("/v1/accounts", name="Jane Doe")
check("exact name match", status == 200 and body.get("customer_name") == "Jane Doe")

status, body = get("/v1/accounts", name="jane")
check("partial lowercase match", status == 200 and body.get("customer_name") == "Jane Doe")

status, body = get("/v1/accounts", name="LOPEZ")
check("uppercase substring match", status == 200 and body.get("customer_name") == "Maria Lopez")

# ============================================================
section("Account lookup — not found")
status, body = get("/v1/accounts", account_number="ACC-DOESNOTEXIST")
check("404 on unknown account", status == 404)
check(
    "error code is account_not_found",
    body.get("detail", {}).get("error") == "account_not_found",
)

status, body = get("/v1/accounts", phone_number="+19999999999")
check("404 on unknown phone", status == 404)

status, body = get("/v1/accounts", name="Nonexistent Person")
check("404 on unknown name", status == 404)

# ============================================================
section("Account lookup — bad request")
status, body = get("/v1/accounts")
check("400 when no identifier provided", status == 400)

# ============================================================
section("Order lookup — by order_number")
status, body = get("/v1/orders", order_number="ORD-7700123")
check("200 status", status == 200)
check("count is 1", body.get("count") == 1)
check(
    "order_type is service_appointment",
    body["orders"][0]["order_type"] == "service_appointment",
)
check("status is scheduled", body["orders"][0]["status"] == "scheduled")

# ============================================================
section("Order lookup — by account_number (multiple orders)")
status, body = get("/v1/orders", account_number="ACC-4722")
check("200 status", status == 200)
check("count is 2", body.get("count") == 2)
order_numbers = sorted(o["order_number"] for o in body["orders"])
check(
    "both expected orders present",
    order_numbers == ["ORD-7700123", "ORD-7700124"],
)

# ============================================================
section("Order lookup — by phone (resolves through account)")
status, body = get("/v1/orders", phone_number="+15125550172")
check("200 status", status == 200)
check("count is 2 for Jane Doe", body.get("count") == 2)

status, body = get("/v1/orders", phone_number="5125550172")
check("normalized phone also works", status == 200 and body.get("count") == 2)

# ============================================================
section("Order lookup — not found")
status, body = get("/v1/orders", order_number="ORD-NOTREAL")
check("404 on unknown order", status == 404)

status, body = get("/v1/orders", account_number="ACC-NOORDERS")
check("404 on account with no orders", status == 404)

status, body = get("/v1/orders", phone_number="+19999999999")
check("404 on phone that doesn't match an account", status == 404)

# ============================================================
section("Order lookup — bad request")
status, body = get("/v1/orders")
check("400 when no identifier provided", status == 400)

# ============================================================
section("OpenAPI spec")
status, body = get("/openapi.json")
check("openapi.json reachable", status == 200)
check("has /v1/accounts path", "/v1/accounts" in body.get("paths", {}))
check("has /v1/orders path", "/v1/orders" in body.get("paths", {}))
check(
    "Account schema defined",
    "Account" in body.get("components", {}).get("schemas", {}),
)
check(
    "Order schema defined",
    "Order" in body.get("components", {}).get("schemas", {}),
)


# ============================================================
print(f"\n{passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
