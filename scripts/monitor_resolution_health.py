import argparse
from datetime import datetime, timedelta, timezone
from statistics import mean, median

from app.db.session import SessionLocal
from sqlalchemy import select
from telecom_support_database.models import ResolutionLog


def percentile(
    values: list[float],
    percentile_value: float,
) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)

    index = (len(ordered) - 1) * percentile_value
    lower = int(index)
    upper = min(lower + 1, len(ordered))

    if lower == upper:
        return ordered[lower]

    fraction = index - lower

    return (
        ordered[lower]
        + (ordered[upper] - ordered[lower]) * fraction
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitor resolution system health."
    )

    parser.add_argument(
        "--hours",
        type=float,
        default=None,
        help=(
            "Only include resolution logs from the "
            "last N hours."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with SessionLocal() as session:
        statement = select(ResolutionLog).order_by(
            ResolutionLog.created_at
        )

        if args.hours is not None:
            if args.hours <= 0:
                raise ValueError(
                    "--hours must be greater than zero."
                )

            cutoff = datetime.now(timezone.utc) - timedelta(
                hours=args.hours
            )

            statement = statement.where(
                ResolutionLog.created_at >= cutoff
            )

        logs = session.execute(statement).scalars().all()

    total = len(logs)

    print("=" * 70)
    print("RESOLUTION SYSTEM HEALTH")
    print("=" * 70)

    if args.hours is not None:
        print(
            f"Time window:                 "
            f"last {args.hours:g} hour(s)"
        )
        print()

    if total == 0:
        print("No resolution logs found.")
        print("=" * 70)
        return

    successful = [
        log
        for log in logs
        if log.error_type is None
    ]

    failed = [
        log
        for log in logs
        if log.error_type is not None
    ]

    grounded = [
        log
        for log in successful
        if log.grounded
    ]

    latencies = [
        float(log.latency_ms)
        for log in logs
        if log.latency_ms is not None
    ]

    confidences = [
        float(log.resolution_confidence)
        for log in successful
        if log.resolution_confidence is not None
    ]

    retrieval_counts = [
        int(log.retrieval_count)
        for log in successful
        if log.retrieval_count is not None
    ]

    evidence_counts = [
        int(log.authoritative_evidence_count)
        for log in successful
        if log.authoritative_evidence_count is not None
    ]

    print(f"Total requests:              {total}")
    print(f"Successful requests:         {len(successful)}")
    print(f"Failed requests:             {len(failed)}")

    print()

    print(
        f"Success rate:                "
        f"{len(successful) / total:.2%}"
    )

    print(
        f"Failure rate:                "
        f"{len(failed) / total:.2%}"
    )

    print(
        f"Grounding rate:              "
        f"{len(grounded) / len(successful):.2%}"
        if successful
        else "Grounding rate:              N/A"
    )

    print()

    if latencies:
        print("LATENCY")
        print("-" * 70)

        print(
            f"Average latency:             "
            f"{mean(latencies):.2f} ms"
        )

        print(
            f"Median latency (P50):        "
            f"{median(latencies):.2f} ms"
        )

        print(
            f"P95 latency:                 "
            f"{percentile(latencies, 0.95):.2f} ms"
        )

    print()

    if confidences:
        print("RESOLUTION QUALITY")
        print("-" * 70)

        print(
            f"Average confidence:          "
            f"{mean(confidences):.3f}"
        )

    if retrieval_counts:
        print(
            f"Average retrieved evidence:  "
            f"{mean(retrieval_counts):.2f}"
        )

    if evidence_counts:
        print(
            f"Average authoritative evidence:"
            f" {mean(evidence_counts):.2f}"
        )

    print()

    print("ERRORS")
    print("-" * 70)

    if not failed:
        print("No failed requests.")
    else:
        error_counts: dict[str, int] = {}

        for log in failed:
            error_type = log.error_type or "UNKNOWN"

            error_counts[error_type] = (
                error_counts.get(error_type, 0) + 1
            )

        for error_type, count in sorted(
            error_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            print(f"{error_type}: {count}")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()