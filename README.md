# Acme Logistics — Inbound Carrier Sales

FDE Technical Challenge solution. An inbound voice agent (built on the
HappyRobot platform) takes calls from carriers, verifies them, pitches a
matching load, negotiates the rate, and books the deal — backed by a small
FastAPI service and a self-built metrics dashboard.

## Architecture

```
                  ┌────────────────── HappyRobot workflow (voice agent) ──────────────────┐
  Carrier ──call──▶ verify MC (FMCSA) ─▶ search load ─▶ pitch ─▶ negotiate ─▶ mock transfer │
                  │                                          │            post-call:         │
                  └──────────────────────────────────────────┼── extract → classify → log ──┘
                                                              │ HTTPS (Caddy)
                                                              ▼
                          ┌─────────────── FastAPI (this repo) ───────────────┐
                          │ /loads/search  /negotiate  /calls  /metrics        │
                          └───────────────────────┬───────────────────────────┘
                                                   ▼
                                              PostgreSQL
                                                   ▲
                          Streamlit dashboard ─────┘  (reads /metrics + /calls)
```

- **API owns the business logic.** The negotiation ceiling and round count live
  in the backend (`/negotiate`), so the voice agent only relays numbers and never
  invents a rate. Final rate and round count are joined into `/calls` by
  `call_id`, keeping the API the single source of truth.
- **Dashboard is decoupled.** Streamlit reads the API over HTTP; it stores no
  secret and is gated by the API key (see Security).

## Components

| Service     | Port (host) | Purpose                                      |
|-------------|-------------|----------------------------------------------|
| `api`       | 8010        | FastAPI (loads, negotiation, call logging, metrics) |
| `db`        | —           | PostgreSQL (loads, negotiation_rounds, calls) |
| `seed`      | —           | One-shot loader of sample loads              |
| `dashboard` | 8501        | Streamlit metrics dashboard                  |
| `caddy`     | 80 / 443    | Reverse proxy + automatic HTTPS              |

## API endpoints

All endpoints (except `/health`) require the `X-API-Key` header.

| Method | Path             | Description                                              |
|--------|------------------|---------------------------------------------------------|
| GET    | `/health`        | Liveness check (no auth)                                 |
| GET    | `/loads/search`  | `origin`, `destination`, `equipment_type` → matching loads |
| POST   | `/negotiate`     | `{call_id, load_id, carrier_offer}` → accept / counter / reject (backend-controlled ceiling & rounds) |
| POST   | `/calls`         | Log a call; joins final rate + rounds from negotiation by `call_id` |
| GET    | `/calls`         | List recent calls                                       |
| GET    | `/metrics`       | Aggregated KPIs (conversion, outcomes, sentiment, avg rate/rounds) |

## Configuration

Copy `.env.example` to `.env` and set values:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `dev-secret-change-me` | Auth key for all endpoints (also the dashboard login) |
| `NEGOTIATION_MAX_MARGIN` | `0.15` | Broker pays up to `loadboard_rate * (1 + margin)` |
| `NEGOTIATION_MAX_ROUNDS` | `3` | Max counter-offers before walking away |
| `API_DOMAIN` / `DASH_DOMAIN` | `*.nip.io` | Public hostnames for HTTPS |
| `ACME_EMAIL` | — | Email for Let's Encrypt |

## Run locally

```bash
cp .env.example .env        # edit API_KEY at minimum
docker compose up -d --build
```

- API:        http://localhost:8010  (docs at `/docs`)
- Dashboard:  http://localhost:8501

The `db` schema is created automatically on startup and `seed` loads sample
loads on first run.

## Deploy / reproduce

The stack is fully containerized; reproducing it anywhere is one command.

```bash
git clone https://github.com/GastonGaitan/fde-loads-api.git
cd fde-loads-api
cp .env.example .env
#  - set a strong API_KEY
#  - set API_DOMAIN / DASH_DOMAIN to <sub>.<your-ip-with-dashes>.nip.io
#  - set ACME_EMAIL
docker compose up -d --build
```

### HTTPS

There are two ways to get HTTPS, depending on the host:

**A. Dedicated host (ports 80/443 free) — bundled Caddy.**
Start the optional `caddy` service, which obtains real Let's Encrypt
certificates automatically for `API_DOMAIN` and `DASH_DOMAIN`:

```bash
docker compose --profile edge up -d --build
```

Using **nip.io** (`<ip-with-dashes>.nip.io`) gives a valid hostname for a bare
IP without buying a domain. Requires ports **80** and **443** open on the host.

**B. Shared host (already runs a reverse proxy on 80/443).**
Leave the `caddy` service off (it is gated behind the `edge` profile, so a plain
`docker compose up -d` skips it) and add two server blocks to the existing
proxy, terminating TLS and forwarding to the published container ports:

```
api.<ip-with-dashes>.nip.io   →  http://127.0.0.1:8010
dash.<ip-with-dashes>.nip.io  →  http://127.0.0.1:8501
```

In both cases, once HTTPS is verified, point the HappyRobot `LOADS_API_URL`
variable at `https://api.<...>.nip.io`.

## Security

- **API-key auth** on every functional endpoint (`X-API-Key`).
- **HTTPS** terminated by Caddy (Let's Encrypt).
- **Dashboard login**: the user pastes the API key, which is validated against
  the API and reused for requests — the dashboard container holds no secret.

## HappyRobot workflow

Inbound voice agent (web-call trigger, no phone number purchased). Flow:
verify MC via FMCSA → collect & confirm preferences → search & pitch → negotiate
(≤ 3 rounds) → mock transfer on a deal → post-call extract + classify (outcome &
sentiment) → `POST /calls`.

## Project layout

```
app/            FastAPI service (models, schemas, endpoints, seed)
dashboard/      Streamlit dashboard (own image)
Caddyfile       Reverse proxy + HTTPS config
docker-compose.yml
```
