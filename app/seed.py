from datetime import datetime, timedelta, timezone

from .db import Base, SessionLocal, engine
from .models import Load

Base.metadata.create_all(bind=engine)

now = datetime.now(timezone.utc).replace(tzinfo=None)

SAMPLE_LOADS = [
    Load(
        load_id="L-1001",
        origin="Dallas, TX",
        destination="Atlanta, GA",
        pickup_datetime=now + timedelta(days=1),
        delivery_datetime=now + timedelta(days=2, hours=12),
        equipment_type="Dry Van",
        loadboard_rate=2400.00,
        notes="No-touch freight, drop and hook available",
        weight=42000,
        commodity_type="General merchandise",
        num_of_pieces=24,
        miles=781,
        dimensions="53ft trailer",
    ),
    Load(
        load_id="L-1002",
        origin="Phoenix, AZ",
        destination="Los Angeles, CA",
        pickup_datetime=now + timedelta(days=1, hours=6),
        delivery_datetime=now + timedelta(days=1, hours=18),
        equipment_type="Reefer",
        loadboard_rate=1850.00,
        notes="Temp 36F, time-sensitive produce",
        weight=38000,
        commodity_type="Fresh produce",
        num_of_pieces=18,
        miles=372,
        dimensions="53ft reefer",
    ),
    Load(
        load_id="L-1003",
        origin="Chicago, IL",
        destination="Houston, TX",
        pickup_datetime=now + timedelta(days=2),
        delivery_datetime=now + timedelta(days=3, hours=8),
        equipment_type="Flatbed",
        loadboard_rate=3100.00,
        notes="Steel coils, tarps required",
        weight=46000,
        commodity_type="Steel",
        num_of_pieces=8,
        miles=1080,
        dimensions="48ft flatbed",
    ),
    Load(
        load_id="L-1004",
        origin="Dallas, TX",
        destination="Miami, FL",
        pickup_datetime=now + timedelta(days=1),
        delivery_datetime=now + timedelta(days=3),
        equipment_type="Dry Van",
        loadboard_rate=3200.00,
        notes="Live load, FCFS appointment",
        weight=41000,
        commodity_type="Electronics",
        num_of_pieces=32,
        miles=1310,
        dimensions="53ft trailer",
    ),
    Load(
        load_id="L-1005",
        origin="Atlanta, GA",
        destination="Dallas, TX",
        pickup_datetime=now + timedelta(days=2),
        delivery_datetime=now + timedelta(days=3, hours=14),
        equipment_type="Dry Van",
        loadboard_rate=2350.00,
        notes="Drop trailer",
        weight=39000,
        commodity_type="Consumer goods",
        num_of_pieces=20,
        miles=781,
        dimensions="53ft trailer",
    ),
    Load(
        load_id="L-1006",
        origin="Denver, CO",
        destination="Salt Lake City, UT",
        pickup_datetime=now + timedelta(hours=18),
        delivery_datetime=now + timedelta(days=1, hours=10),
        equipment_type="Power Only",
        loadboard_rate=1200.00,
        notes="Carrier provides truck, trailer staged at shipper",
        weight=44000,
        commodity_type="Mixed freight",
        num_of_pieces=15,
        miles=525,
        dimensions="53ft trailer (provided)",
    ),
    Load(
        load_id="L-1007",
        origin="Los Angeles, CA",
        destination="Seattle, WA",
        pickup_datetime=now + timedelta(days=1),
        delivery_datetime=now + timedelta(days=2, hours=20),
        equipment_type="Reefer",
        loadboard_rate=2950.00,
        notes="Temp 34F, frozen seafood",
        weight=40000,
        commodity_type="Frozen seafood",
        num_of_pieces=22,
        miles=1135,
        dimensions="53ft reefer",
    ),
    Load(
        load_id="L-1008",
        origin="Houston, TX",
        destination="New Orleans, LA",
        pickup_datetime=now + timedelta(hours=10),
        delivery_datetime=now + timedelta(days=1, hours=4),
        equipment_type="Flatbed",
        loadboard_rate=1450.00,
        notes="Construction materials, tarps optional",
        weight=43500,
        commodity_type="Construction materials",
        num_of_pieces=12,
        miles=350,
        dimensions="48ft flatbed",
    ),
    Load(
        load_id="L-1009",
        origin="Atlanta, GA",
        destination="Charlotte, NC",
        pickup_datetime=now + timedelta(hours=12),
        delivery_datetime=now + timedelta(days=1),
        equipment_type="Dry Van",
        loadboard_rate=950.00,
        notes="Quick turn, drop and hook",
        weight=28000,
        commodity_type="Paper products",
        num_of_pieces=14,
        miles=245,
        dimensions="53ft trailer",
    ),
    Load(
        load_id="L-1010",
        origin="Phoenix, AZ",
        destination="Dallas, TX",
        pickup_datetime=now + timedelta(days=1, hours=8),
        delivery_datetime=now + timedelta(days=2, hours=16),
        equipment_type="Dry Van",
        loadboard_rate=2150.00,
        notes="Standard freight",
        weight=37000,
        commodity_type="Auto parts",
        num_of_pieces=26,
        miles=887,
        dimensions="53ft trailer",
    ),
]


def main():
    with SessionLocal() as db:
        existing = db.query(Load).count()
        if existing > 0:
            print(f"DB already has {existing} loads. Skipping seed.")
            return
        for load in SAMPLE_LOADS:
            db.add(load)
        db.commit()
        print(f"Seeded {len(SAMPLE_LOADS)} loads.")


if __name__ == "__main__":
    main()
