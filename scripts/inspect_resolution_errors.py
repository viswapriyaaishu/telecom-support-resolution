from app.db.session import SessionLocal
from sqlalchemy import select
from telecom_support_database.models import ResolutionLog

with SessionLocal() as session:
    rows = session.execute(
        select(ResolutionLog)
        .where(ResolutionLog.error_type.is_not(None))
        .order_by(ResolutionLog.created_at.desc())
        .limit(5)
    ).scalars().all()

    for row in rows:
        print("=" * 70)
        print(f"Time: {row.created_at}")
        print(f"Error type: {row.error_type}")
        print(f"Error message: {row.error_message}")
