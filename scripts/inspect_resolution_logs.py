from app.db.session import SessionLocal
from sqlalchemy import select
from telecom_support_database.models import ResolutionLog

with SessionLocal() as session:
    rows = session.execute(
        select(ResolutionLog)
        .order_by(ResolutionLog.created_at.desc())
        .limit(10)
    ).scalars().all()

    for row in rows:
        print(
            f"{row.created_at} | "
            f"{row.latency_ms:.2f} ms | "
            f"error={row.error_type} | "
            f"grounded={row.grounded}"
        )
