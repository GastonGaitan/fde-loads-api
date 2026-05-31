from sqlalchemy import Column, String, Float, Integer, DateTime, Text
from .db import Base


class Load(Base):
    __tablename__ = "loads"

    load_id = Column(String, primary_key=True)
    origin = Column(String, nullable=False, index=True)
    destination = Column(String, nullable=False, index=True)
    pickup_datetime = Column(DateTime, nullable=False)
    delivery_datetime = Column(DateTime, nullable=False)
    equipment_type = Column(String, nullable=False, index=True)
    loadboard_rate = Column(Float, nullable=False)
    notes = Column(Text, default="")
    weight = Column(Float, nullable=False)
    commodity_type = Column(String, nullable=False)
    num_of_pieces = Column(Integer, nullable=False)
    miles = Column(Float, nullable=False)
    dimensions = Column(String, default="")
