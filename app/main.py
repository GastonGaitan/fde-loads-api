import json
import os
import urllib.request
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Call, Load, NegotiationRound
from .schemas import (
    CallCreate,
    CallOut,
    CarrierVerifyResponse,
    NegotiateRequest,
    NegotiateResponse,
    SearchResponse,
)

API_KEY = os.getenv("API_KEY", "dev-secret-change-me")

# Broker is willing to pay up to listed_rate * (1 + margin).
NEGOTIATION_MAX_MARGIN = float(os.getenv("NEGOTIATION_MAX_MARGIN", "0.15"))
# Max number of counter-offers the agent may make before walking away.
NEGOTIATION_MAX_ROUNDS = int(os.getenv("NEGOTIATION_MAX_ROUNDS", "3"))

# FMCSA carrier lookup (server-side wrapper).
FMCSA_API_KEY = os.getenv("FMCSA_API_KEY", "")
FMCSA_DOCKET_URL = os.getenv(
    "FMCSA_DOCKET_URL",
    "https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number",
)

app = FastAPI(title="Acme Loads API", version="0.1.0")

Base.metadata.create_all(bind=engine)


def require_api_key(x_api_key: str = Header(default=None, alias="X-API-Key")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid or missing X-API-Key header")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get(
    "/loads/search",
    response_model=SearchResponse,
    dependencies=[Depends(require_api_key)],
)
def search_loads(
    origin: str = Query(..., description="City, State of pickup (e.g. 'Dallas, TX'). Use 'any' to skip filter."),
    destination: str = Query(..., description="City, State of dropoff. Use 'any' to skip filter."),
    equipment_type: str = Query(..., description="Dry Van, Reefer, Flatbed, Power Only, or Other."),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Load)

    if origin.strip().lower() != "any":
        origin_city = origin.split(",")[0].strip().lower()
        query = query.filter(func.lower(Load.origin).contains(origin_city))

    if destination.strip().lower() != "any":
        dest_city = destination.split(",")[0].strip().lower()
        query = query.filter(func.lower(Load.destination).contains(dest_city))

    query = query.filter(func.lower(Load.equipment_type) == equipment_type.strip().lower())

    loads = query.limit(limit).all()
    return SearchResponse(count=len(loads), loads=loads)


@app.get(
    "/carriers/verify",
    response_model=CarrierVerifyResponse,
    dependencies=[Depends(require_api_key)],
)
def verify_carrier(mc: str = Query(..., description="Carrier MC / docket number")):
    """Server-side wrapper over the FMCSA QCMobile API. Returns a flat, typed
    result so the voice agent gets clean fields (eligible, carrier_name, ...)
    instead of parsing raw FMCSA JSON in the workflow. Always returns 200; any
    failure is reported in the `error` field with eligible=False."""
    digits = "".join(c for c in mc if c.isdigit())
    result = CarrierVerifyResponse(mc_number=digits, eligible=False)
    if not digits:
        result.error = "invalid MC number"
        return result

    url = f"{FMCSA_DOCKET_URL}/{digits}?webKey={FMCSA_API_KEY}"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (compatible; AcmeLogistics/1.0)",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            payload = json.loads(r.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        result.error = f"FMCSA lookup failed: {exc}"
        return result

    content = payload.get("content")
    if isinstance(content, list):
        content = content[0] if content else None
    carrier = (content or {}).get("carrier") if content else None
    if not carrier:
        result.error = "carrier not found"
        return result

    allowed = str(carrier.get("allowedToOperate") or "N")
    status = str(carrier.get("statusCode") or "I")
    result.carrier_name = str(carrier.get("legalName") or "Unknown")
    result.dot_number = str(carrier.get("dotNumber") or "")
    result.allowed_to_operate = allowed
    result.status_code = status
    result.eligible = allowed == "Y" and status == "A"
    return result


def _round_to(value: float, step: int = 25) -> float:
    return float(round(value / step) * step)


@app.post(
    "/negotiate",
    response_model=NegotiateResponse,
    dependencies=[Depends(require_api_key)],
)
def negotiate(req: NegotiateRequest, db: Session = Depends(get_db)):
    """Stateful rate negotiation. The backend owns the ceiling and the round count
    so the voice agent only has to speak the decision (never invent numbers)."""
    load = db.get(Load, req.load_id)
    if load is None:
        raise HTTPException(status_code=404, detail=f"load {req.load_id!r} not found")

    listed = float(load.loadboard_rate)
    max_rate = round(listed * (1 + NEGOTIATION_MAX_MARGIN), 2)
    offer = float(req.carrier_offer)

    prior_rounds = (
        db.query(NegotiationRound)
        .filter(
            NegotiationRound.call_id == req.call_id,
            NegotiationRound.load_id == req.load_id,
        )
        .count()
    )
    rnd = prior_rounds + 1

    counter_rate = None
    agreed_rate = None

    if offer <= max_rate:
        decision = "accept"
        agreed_rate = offer
        final = True
        message = f"Carrier offer {offer} within budget (max {max_rate}); accepted."
    elif rnd > NEGOTIATION_MAX_ROUNDS:
        decision = "reject"
        final = True
        message = f"Offer {offer} above max {max_rate} after {NEGOTIATION_MAX_ROUNDS} rounds; no deal."
    elif rnd >= NEGOTIATION_MAX_ROUNDS:
        decision = "counter"
        counter_rate = max_rate
        final = True
        message = f"Round {rnd}: best-and-final counter at max {max_rate}."
    else:
        # Counter walks monotonically from listed toward max as rounds advance,
        # always staying at or below the ceiling.
        decision = "counter"
        frac = rnd / NEGOTIATION_MAX_ROUNDS
        counter_rate = float(min(max_rate, _round_to(listed + frac * (max_rate - listed))))
        final = False
        message = f"Round {rnd}: counter at {counter_rate} (offer {offer}, max {max_rate})."

    db.add(
        NegotiationRound(
            call_id=req.call_id,
            load_id=req.load_id,
            round_number=rnd,
            carrier_offer=offer,
            decision=decision,
            counter_rate=counter_rate,
            agreed_rate=agreed_rate,
        )
    )
    db.commit()

    return NegotiateResponse(
        round=rnd,
        decision=decision,
        listed_rate=listed,
        max_rate=max_rate,
        carrier_offer=offer,
        counter_rate=counter_rate,
        agreed_rate=agreed_rate,
        final=final,
        message=message,
    )


@app.post(
    "/calls",
    response_model=CallOut,
    dependencies=[Depends(require_api_key)],
)
def log_call(req: CallCreate, db: Session = Depends(get_db)):
    """Persist a post-call record. Rate and round data are joined from the
    authoritative negotiation_rounds table by call_id, so the agent never has
    to report (and possibly hallucinate) the final numbers."""
    rounds = (
        db.query(NegotiationRound)
        .filter(NegotiationRound.call_id == req.call_id)
        .order_by(NegotiationRound.round_number)
        .all()
    )
    agreed = False
    final_rate = None
    load_id = req.load_id
    for r in rounds:
        if r.load_id:
            load_id = r.load_id
        if r.decision == "accept":
            agreed = True
            final_rate = r.agreed_rate

    transcript = req.transcript
    if transcript is not None and not isinstance(transcript, str):
        transcript = json.dumps(transcript, ensure_ascii=False)

    call = Call(
        call_id=req.call_id,
        mc_number=req.mc_number,
        carrier_name=req.carrier_name,
        eligible=req.eligible,
        load_id=load_id,
        agreed=agreed,
        final_rate=final_rate,
        negotiation_rounds=len(rounds),
        outcome=req.outcome,
        sentiment=req.sentiment,
        transcript=transcript,
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


@app.get(
    "/calls",
    response_model=list[CallOut],
    dependencies=[Depends(require_api_key)],
)
def list_calls(
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return db.query(Call).order_by(Call.created_at.desc()).limit(limit).all()


@app.get("/metrics", dependencies=[Depends(require_api_key)])
def metrics(db: Session = Depends(get_db)):
    """Aggregated KPIs for the dashboard (Objective 2)."""
    total = db.query(Call).count()
    deals = db.query(Call).filter(Call.agreed.is_(True)).count()

    outcomes = dict(
        db.query(Call.outcome, func.count(Call.id)).group_by(Call.outcome).all()
    )
    sentiments = dict(
        db.query(Call.sentiment, func.count(Call.id)).group_by(Call.sentiment).all()
    )

    avg_rounds = (
        db.query(func.avg(Call.negotiation_rounds))
        .filter(Call.agreed.is_(True))
        .scalar()
    )
    avg_rate = (
        db.query(func.avg(Call.final_rate)).filter(Call.agreed.is_(True)).scalar()
    )

    return {
        "total_calls": total,
        "deals_booked": deals,
        "conversion_rate": round(deals / total, 4) if total else 0.0,
        "outcomes": {(k or "unknown"): v for k, v in outcomes.items()},
        "sentiments": {(k or "unknown"): v for k, v in sentiments.items()},
        "avg_negotiation_rounds_for_deals": (
            round(float(avg_rounds), 2) if avg_rounds is not None else None
        ),
        "avg_final_rate_for_deals": (
            round(float(avg_rate), 2) if avg_rate is not None else None
        ),
    }
