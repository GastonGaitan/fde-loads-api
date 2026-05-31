from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean
from .db import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


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


class NegotiationRound(Base):
    __tablename__ = "negotiation_rounds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String, nullable=False, index=True)
    load_id = Column(String, nullable=False, index=True)
    round_number = Column(Integer, nullable=False)
    carrier_offer = Column(Float, nullable=False)
    decision = Column(String, nullable=False)  # accept | counter | reject
    counter_rate = Column(Float, nullable=True)
    agreed_rate = Column(Float, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String, nullable=False, index=True)
    mc_number = Column(String, nullable=True)
    carrier_name = Column(String, nullable=True)
    eligible = Column(Boolean, nullable=True)
    load_id = Column(String, nullable=True)
    agreed = Column(Boolean, nullable=False, default=False)
    final_rate = Column(Float, nullable=True)
    negotiation_rounds = Column(Integer, nullable=False, default=0)
    outcome = Column(String, nullable=True)  # classified post-call
    sentiment = Column(String, nullable=True)  # classified post-call
    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
