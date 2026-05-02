"""
main.py — FastAPI application entry point.

Endpoints:
    GET /v1/accounts          Look up by account_number, phone_number, or name
    GET /v1/orders            Look up by order_number, account_number, or phone_number
    GET /health               Liveness probe
    GET /                     Service info
    GET /docs                 Auto-generated Swagger UI
    GET /openapi.json         Auto-generated OpenAPI 3.1 spec

Run locally:
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

Docs once running:
    http://localhost:8000/docs
"""

from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from data import find_account, find_orders
from schemas import Account, Order, OrderListResponse, ErrorResponse


app = FastAPI(
    title="Charter Demo API",
    description=(
        "Mock ISP API for AIR demos. Provides account and order lookup "
        "by multiple identifiers. All data is fictional — no real PII."
    ),
    version="1.0.0",
    contact={"name": "AIR Demo Team"},
    servers=[
        {"url": "https://charter-api-mock.onrender.com", "description": "Render deployment"},
        {"url": "http://localhost:8000", "description": "Local dev"},
    ],
)


# ============================================================
# Middleware
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # permissive for demo; tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Health & root
# ============================================================
@app.get("/", tags=["meta"], summary="Service info")
def root():
    return {
        "service": "charter-api-mock",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "endpoints": ["/v1/accounts", "/v1/orders"],
    }


@app.get("/health", tags=["meta"], summary="Health check")
def health():
    return {"status": "ok"}


# ============================================================
# Account lookup
# ============================================================
@app.get(
    "/v1/accounts",
    tags=["accounts"],
    response_model=Account,
    responses={404: {"model": ErrorResponse, "description": "Account not found"}},
    summary="Look up an account",
    description=(
        "Look up a single account by exactly one of the three identifiers. "
        "Match precedence is `account_number` > `phone_number` > `name`. "
        "Phone numbers are normalized — `(512) 555-0172`, `512-555-0172`, "
        "and `+15125550172` all match. Name matching is case-insensitive substring."
    ),
)
def get_account(
    account_number: Optional[str] = Query(
        None,
        description="Exact account number, e.g. `ACC-4722`",
        examples=["ACC-4722"],
    ),
    phone_number: Optional[str] = Query(
        None,
        description="Phone number; flexible formatting accepted",
        examples=["+15125550172"],
    ),
    name: Optional[str] = Query(
        None,
        description="Customer name (case-insensitive substring)",
        examples=["Jane Doe"],
    ),
):
    if not (account_number or phone_number or name):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "missing_identifier",
                "message": "Provide at least one of: account_number, phone_number, name.",
            },
        )

    acct = find_account(
        account_number=account_number,
        phone_number=phone_number,
        name=name,
    )
    if not acct:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "account_not_found",
                "message": "No account matched the provided identifiers.",
            },
        )
    return acct


# ============================================================
# Order lookup
# ============================================================
@app.get(
    "/v1/orders",
    tags=["orders"],
    response_model=OrderListResponse,
    responses={404: {"model": ErrorResponse, "description": "No orders found"}},
    summary="Look up orders",
    description=(
        "Look up orders by exactly one of: `order_number` (returns at most 1), "
        "`account_number` (returns all orders for the account), or "
        "`phone_number` (resolves to account, then returns its orders). "
        "Returns `404` when no orders match."
    ),
)
def get_orders(
    order_number: Optional[str] = Query(
        None,
        description="Exact order number, e.g. `ORD-7700123`",
        examples=["ORD-7700123"],
    ),
    account_number: Optional[str] = Query(
        None,
        description="Account number to list all orders for",
        examples=["ACC-4722"],
    ),
    phone_number: Optional[str] = Query(
        None,
        description="Phone number; resolves to account first",
        examples=["+15125550172"],
    ),
):
    if not (order_number or account_number or phone_number):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "missing_identifier",
                "message": "Provide at least one of: order_number, account_number, phone_number.",
            },
        )

    orders = find_orders(
        order_number=order_number,
        account_number=account_number,
        phone_number=phone_number,
    )
    if not orders:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "orders_not_found",
                "message": "No orders matched the provided identifiers.",
            },
        )

    return {"count": len(orders), "orders": orders}
