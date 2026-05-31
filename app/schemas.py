from datetime import datetime
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
