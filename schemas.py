"""
schemas.py — Pydantic models that define request/response shapes.

FastAPI uses these to:
1. Validate incoming requests
2. Serialize outgoing responses
3. Auto-generate the OpenAPI spec at /openapi.json and Swagger UI at /docs
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


# ============================================================
# Common
# ============================================================
class ServiceAddress(BaseModel):
    street: str
    city: str
    state: str
    zip: str


class Plan(BaseModel):
    name: str
    speed_mbps: int
    monthly_cost: float


class BalanceDue(BaseModel):
    amount: float
    due_date: str


class LastPayment(BaseModel):
    amount: float
    date: str
    method: str


class ErrorResponse(BaseModel):
    error: str = Field(..., examples=["account_not_found"])
    message: str = Field(..., examples=["No account matched the provided identifiers."])


# ============================================================
# Account
# ============================================================
class Account(BaseModel):
    account_number: str = Field(..., examples=["ACC-4722"])
    customer_name: str = Field(..., examples=["Jane Doe"])
    phone_number: str = Field(..., examples=["+15125550172"])
    email: str
    service_address: ServiceAddress
    current_plan: Plan
    balance_due: BalanceDue
    last_payment: LastPayment
    autopay_enabled: bool
    account_status: Literal["active", "past_due", "suspended"]
    tenure_months: int


# ============================================================
# Order
# ============================================================
class OrderItem(BaseModel):
    sku: str
    description: str
    quantity: int
    amount: float


class Order(BaseModel):
    order_number: str = Field(..., examples=["ORD-7700123"])
    account_number: str
    order_type: Literal[
        "service_appointment",
        "equipment_replacement",
        "plan_upgrade",
        "plan_downgrade",
        "new_service",
        "disconnect",
    ]
    status: Literal[
        "pending_confirmation",
        "scheduled",
        "shipped",
        "in_progress",
        "completed",
        "cancelled",
    ]
    created_date: str
    scheduled_date: Optional[str] = None
    scheduled_window_end: Optional[str] = None
    description: str
    items: list[OrderItem]
    total_amount: float
    technician: Optional[str] = None
    notes: Optional[str] = None


class OrderListResponse(BaseModel):
    """When looking up by phone/account, multiple orders may match."""
    count: int
    orders: list[Order]
