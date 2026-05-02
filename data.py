"""
data.py — In-memory mock database for accounts and orders.

Three scenarios across three customers, plus a default fallback for any
unknown lookup so demos never crash with 'no data'.
"""

from typing import Optional


# ============================================================
# Accounts
# ============================================================
ACCOUNTS = [
    {
        "account_number": "ACC-4722",
        "customer_name": "Jane Doe",
        "phone_number": "+15125550172",
        "email": "jane.doe@example.com",
        "service_address": {
            "street": "4521 Oak St",
            "city": "Austin",
            "state": "TX",
            "zip": "78704",
        },
        "current_plan": {
            "name": "Spectrum Internet 200",
            "speed_mbps": 200,
            "monthly_cost": 89.99,
        },
        "balance_due": {"amount": 134.18, "due_date": "2026-05-15"},
        "last_payment": {
            "amount": 89.99,
            "date": "2026-04-15",
            "method": "autopay_visa_4444",
        },
        "autopay_enabled": True,
        "account_status": "active",
        "tenure_months": 38,
    },
    {
        "account_number": "ACC-9981",
        "customer_name": "Robert Chen",
        "phone_number": "+13035551122",
        "email": "rchen@example.com",
        "service_address": {
            "street": "1820 Larimer St",
            "city": "Denver",
            "state": "CO",
            "zip": "80202",
        },
        "current_plan": {
            "name": "Spectrum Internet 500",
            "speed_mbps": 500,
            "monthly_cost": 109.99,
        },
        "balance_due": {"amount": 109.99, "due_date": "2026-05-10"},
        "last_payment": {
            "amount": 109.99,
            "date": "2026-04-10",
            "method": "autopay_mastercard_8821",
        },
        "autopay_enabled": True,
        "account_status": "active",
        "tenure_months": 14,
    },
    {
        "account_number": "ACC-1234",
        "customer_name": "Maria Lopez",
        "phone_number": "+18135559944",
        "email": "mlopez@example.com",
        "service_address": {
            "street": "3100 Bayshore Blvd",
            "city": "Tampa",
            "state": "FL",
            "zip": "33629",
        },
        "current_plan": {
            "name": "Spectrum Internet 300",
            "speed_mbps": 300,
            "monthly_cost": 99.99,
        },
        "balance_due": {"amount": 99.99, "due_date": "2026-05-08"},
        "last_payment": {
            "amount": 99.99,
            "date": "2026-04-08",
            "method": "autopay_visa_2233",
        },
        "autopay_enabled": True,
        "account_status": "active",
        "tenure_months": 67,
    },
]


# ============================================================
# Orders
# ============================================================
# Orders reference accounts by account_number so phone-number lookup
# works transitively (look up the account, then return its orders).
ORDERS = [
    {
        "order_number": "ORD-7700123",
        "account_number": "ACC-4722",
        "order_type": "service_appointment",
        "status": "scheduled",
        "created_date": "2026-04-25",
        "scheduled_date": "2026-05-02T14:00:00Z",
        "scheduled_window_end": "2026-05-02T17:00:00Z",
        "description": "Technician visit — investigate intermittent disconnects",
        "items": [
            {
                "sku": "SVC-FIELD-DIAG",
                "description": "On-site signal diagnostic",
                "quantity": 1,
                "amount": 0.00,
            }
        ],
        "total_amount": 0.00,
        "technician": None,
        "notes": "Customer reports 6 evening disconnects in past 24h",
    },
    {
        "order_number": "ORD-7700124",
        "account_number": "ACC-4722",
        "order_type": "plan_upgrade",
        "status": "pending_confirmation",
        "created_date": "2026-04-28",
        "scheduled_date": None,
        "scheduled_window_end": None,
        "description": "Upgrade from Internet 200 to Internet 500",
        "items": [
            {
                "sku": "PLAN-INET-500",
                "description": "Spectrum Internet 500 (monthly)",
                "quantity": 1,
                "amount": 109.99,
            }
        ],
        "total_amount": 109.99,
        "technician": None,
        "notes": "Auto-applies after customer confirmation",
    },
    {
        "order_number": "ORD-8800987",
        "account_number": "ACC-9981",
        "order_type": "equipment_replacement",
        "status": "shipped",
        "created_date": "2026-04-20",
        "scheduled_date": "2026-04-29T00:00:00Z",
        "scheduled_window_end": None,
        "description": "Replacement modem — DOCSIS 3.1 (self-install)",
        "items": [
            {
                "sku": "EQ-MODEM-DOCSIS31",
                "description": "Self-install DOCSIS 3.1 modem",
                "quantity": 1,
                "amount": 0.00,
            }
        ],
        "total_amount": 0.00,
        "technician": None,
        "notes": "Tracking: 1Z9999W90398765432",
    },
    {
        "order_number": "ORD-9900456",
        "account_number": "ACC-1234",
        "order_type": "service_appointment",
        "status": "completed",
        "created_date": "2026-04-15",
        "scheduled_date": "2026-04-22T13:00:00Z",
        "scheduled_window_end": "2026-04-22T15:00:00Z",
        "description": "Modem replacement — equipment failure resolved",
        "items": [
            {
                "sku": "SVC-FIELD-SWAP",
                "description": "On-site equipment swap",
                "quantity": 1,
                "amount": 0.00,
            },
            {
                "sku": "EQ-MODEM-DOCSIS31",
                "description": "DOCSIS 3.1 modem (replacement)",
                "quantity": 1,
                "amount": 0.00,
            },
        ],
        "total_amount": 0.00,
        "technician": "Tech ID 4471 — Daniel R.",
        "notes": "Old modem returned; signal verified at 38 dB SNR",
    },
]


# ============================================================
# Lookup helpers
# ============================================================
def _normalize_phone(value: str) -> str:
    """Strip everything but digits and a leading +. Allows lookups like
    '512-555-0172', '(512) 555-0172', '+15125550172' to all match."""
    if not value:
        return ""
    cleaned = "".join(c for c in value if c.isdigit() or c == "+")
    # If the user gave a 10-digit US number without country code, prefix +1
    if cleaned and not cleaned.startswith("+") and len(cleaned) == 10:
        cleaned = "+1" + cleaned
    return cleaned


def _normalize_name(value: str) -> str:
    return (value or "").strip().lower()


def find_account(
    account_number: Optional[str] = None,
    phone_number: Optional[str] = None,
    name: Optional[str] = None,
) -> Optional[dict]:
    """Look up exactly one account by any of the three identifiers.

    Match precedence: account_number > phone_number > name.
    Name match is case-insensitive substring; the others are normalized
    to canonical form before exact comparison.
    """
    if account_number:
        target = account_number.strip().upper()
        for acct in ACCOUNTS:
            if acct["account_number"].upper() == target:
                return acct
        return None

    if phone_number:
        target = _normalize_phone(phone_number)
        for acct in ACCOUNTS:
            if _normalize_phone(acct["phone_number"]) == target:
                return acct
        return None

    if name:
        target = _normalize_name(name)
        # Substring match — first hit wins
        for acct in ACCOUNTS:
            if target in _normalize_name(acct["customer_name"]):
                return acct
        return None

    return None


def find_orders(
    order_number: Optional[str] = None,
    account_number: Optional[str] = None,
    phone_number: Optional[str] = None,
) -> list[dict]:
    """Return matching orders. order_number returns at most 1; the others
    can return many."""
    if order_number:
        target = order_number.strip().upper()
        for order in ORDERS:
            if order["order_number"].upper() == target:
                return [order]
        return []

    if account_number:
        target = account_number.strip().upper()
        return [o for o in ORDERS if o["account_number"].upper() == target]

    if phone_number:
        # Resolve phone → account_number, then return that account's orders
        acct = find_account(phone_number=phone_number)
        if not acct:
            return []
        return [o for o in ORDERS if o["account_number"] == acct["account_number"]]

    return []
