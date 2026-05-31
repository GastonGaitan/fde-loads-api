import os
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Load
from .schemas import SearchResponse

API_KEY = os.getenv("API_KEY", "dev-secret-change-me")

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
