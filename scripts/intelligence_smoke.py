from app.services.intelligence import ComplaintIntelligenceService


def main() -> None:
    complaint = (
        "My broadband drops every evening around 8 and "
        "I've already restarted the router twice, "
        "I work from home and this is costing me."
    )

    service = ComplaintIntelligenceService()
    result = service.analyze(complaint)

    print("\nComplaint:")
    print(complaint)

    print("\nIntelligence:")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()