from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class LoadOut(BaseModel):
    load_id: str
    origin: str
    destination: str
    pickup_datetime: datetime
    delivery_datetime: datetime
    equipment_type: str
    loadboard_rate: float
    notes: str
    weight: float
    commodity_type: str
    num_of_pieces: int
    miles: float
    dimensions: str

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    count: int
    loads: list[LoadOut]


class NegotiateRequest(BaseModel):
    call_id: str
    load_id: str
    carrier_offer: float


class NegotiateResponse(BaseModel):
    round: int
    decision: str  # accept | counter | reject
    listed_rate: float
    max_rate: float
    carrier_offer: float
    counter_rate: Optional[float] = None
    agreed_rate: Optional[float] = None
    final: bool = False
    message: str
