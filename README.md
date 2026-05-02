# Charter API Mock — Python / FastAPI

Mock ISP API for AIR demos. Two endpoints (account lookup, order lookup) with multi-identifier search, deployable to Render in one click.

**Why FastAPI**: it auto-generates the OpenAPI 3.1 spec from your Python code — no separate YAML to maintain. Visit `/docs` after starting the server to get an interactive Swagger UI for free.

## What's in this repo

| File | Purpose |
|---|---|
| `main.py` | FastAPI application — endpoints, routing, OpenAPI metadata |
| `schemas.py` | Pydantic models — define request/response shapes, drive the OpenAPI spec |
| `data.py` | In-memory mock database + lookup helpers (phone normalization, name matching) |
| `test.py` | 30+ smoke tests covering every endpoint and error case |
| `requirements.txt` | FastAPI, Uvicorn, Pydantic |
| `render.yaml` | Render Blueprint for one-click deploy |

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/v1/accounts?account_number=...` | Look up account by account number |
| GET | `/v1/accounts?phone_number=...` | Look up account by phone (any format) |
| GET | `/v1/accounts?name=...` | Look up account by customer name (case-insensitive substring) |
| GET | `/v1/orders?order_number=...` | Look up specific order |
| GET | `/v1/orders?account_number=...` | List all orders for an account |
| GET | `/v1/orders?phone_number=...` | List all orders for the account that owns this phone |
| GET | `/health` | Health check (used by Render) |
| GET | `/docs` | Auto-generated Swagger UI |
| GET | `/openapi.json` | Auto-generated OpenAPI 3.1 spec |

All lookups return **200** with the resource on match, or **404** with `{"detail": {"error": "...", "message": "..."}}` on no match. Missing all identifiers returns **400**.

## Step 1 — Run locally (3 minutes)

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Visit:
- **http://localhost:8000/docs** — interactive Swagger UI
- **http://localhost:8000/openapi.json** — raw OpenAPI spec

Try a few calls:

```bash
# Account by account number
curl 'http://localhost:8000/v1/accounts?account_number=ACC-4722' | python -m json.tool

# Same account by phone (any format works)
curl 'http://localhost:8000/v1/accounts?phone_number=512-555-0172' | python -m json.tool

# By name
curl 'http://localhost:8000/v1/accounts?name=jane' | python -m json.tool

# Specific order
curl 'http://localhost:8000/v1/orders?order_number=ORD-7700123' | python -m json.tool

# All orders for the account behind this phone number
curl 'http://localhost:8000/v1/orders?phone_number=+15125550172' | python -m json.tool

# Not found
curl -i 'http://localhost:8000/v1/accounts?account_number=NOPE'
```

### Run the test suite

In another terminal while the server is running:

```bash
python test.py
```

Expect `30+ passed, 0 failed`. Tests cover happy paths, all phone-number formats, partial name matching, every 404 case, the 400 validation error, and the OpenAPI spec itself.

## Step 2 — Deploy to Render (5 minutes)

### One-click via Blueprint

1. Push to GitHub
2. Render Dashboard → **New** → **Blueprint** → connect repo
3. Render reads `render.yaml`, runs `pip install -r requirements.txt`, starts `uvicorn`
4. ~2 minutes later you get `https://charter-api-mock.onrender.com`

### Verify

```bash
curl https://charter-api-mock.onrender.com/health
curl 'https://charter-api-mock.onrender.com/v1/accounts?account_number=ACC-4722'
```

Then open `https://charter-api-mock.onrender.com/docs` in a browser to show the prospect the live, interactive API.

### ⚠️ Free tier cold starts

Render's free plan spins down after 15 minutes of inactivity (~30s cold start on next request). For live demos, **upgrade to Starter ($7/mo)** or warm the service with a few `/health` hits before showing it.

## Step 3 — Wire AIR Pro Studio to it

In AIR Pro Studio → Integrations → Add REST Integration:

| Field | Value |
|---|---|
| Name | `Charter Customer API` |
| Base URL | `https://charter-api-mock.onrender.com` |
| Auth | None (mock; production would have API key or OAuth) |
| Timeout | 5000ms |

### Operations

**lookup_account_by_phone**
- Method: `GET`
- Path: `/v1/accounts`
- Query: `phone_number={caller_phone}` (from agent context)
- Use case: AIR's first action when a call lands — identify who's calling

**lookup_account_by_name**
- Method: `GET`
- Path: `/v1/accounts`
- Query: `name={customer_says_name}`
- Use case: caller doesn't have account number handy and called from a different phone

**lookup_account_by_number**
- Method: `GET`
- Path: `/v1/accounts`
- Query: `account_number={customer_provides}`
- Use case: caller reads account number off their bill

**lookup_orders_for_caller**
- Method: `GET`
- Path: `/v1/orders`
- Query: `phone_number={caller_phone}`
- Use case: "is my technician scheduled?", "did my modem ship?"

**lookup_specific_order**
- Method: `GET`
- Path: `/v1/orders`
- Query: `order_number={customer_provides}`
- Use case: caller has an order number (from email/SMS) and wants status

## The data inside

Three customers are wired up to support different demo scenarios:

| Account | Customer | Phone | Plan | Demo scenario |
|---|---|---|---|---|
| `ACC-4722` | Jane Doe | `+15125550172` | Internet 200 | Headline: pending tech appointment + plan upgrade pending |
| `ACC-9981` | Robert Chen | `+13035551122` | Internet 500 | Modem replacement shipped (self-install) |
| `ACC-1234` | Maria Lopez | `+18135559944` | Internet 300 | Recently completed equipment swap |

Phone-number normalization is case-tested in the suite — `(512) 555-0172`, `512-555-0172`, `5125550172`, and `+15125550172` all match the same account.

## What this gives the AIR demo

A real REST API the agent can hit during a live call to:

1. **Identify the caller** automatically from their phone number (no "what's your account number?" friction)
2. **Pull account context** before the agent says anything — so the greeting can be personalized
3. **Look up open orders** when the caller asks "is my tech still coming?"
4. **Demonstrate graceful degradation** — when the lookup misses, the agent should fall back to asking for identifiers (which AIR's guardrails handle)

## Troubleshooting

**`uvicorn: command not found`** — run `pip install -r requirements.txt` first.

**Render build fails on Python version** — `render.yaml` pins Python 3.11.9. If your Render account doesn't have that version, change the `PYTHON_VERSION` env var to `3.12.0` or whatever's available.

**CORS errors from AIR test console** — Already handled with `allow_origins=["*"]` in `main.py`. Tighten before any production-ish use.

**State doesn't persist on redeploy** — In-memory only. For a persistent version, swap `data.py` for SQLite or attach Render's Postgres add-on.

## License

No real customer data. Free to fork, modify, and use for demos.
