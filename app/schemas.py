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


class CallCreate(BaseModel):
    call_id: str
    mc_number: Optional[str] = None
    carrier_name: Optional[str] = None
    eligible: Optional[bool] = None
    load_id: Optional[str] = None
    outcome: Optional[str] = None
    sentiment: Optional[str] = None
    transcript: Optional[str] = None


class CallOut(BaseModel):
    id: int
    call_id: str
    mc_number: Optional[str] = None
    carrier_name: Optional[str] = None
    eligible: Optional[bool] = None
    load_id: Optional[str] = None
    agreed: bool
    final_rate: Optional[float] = None
    negotiation_rounds: int
    outcome: Optional[str] = None
    sentiment: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
