import json

import httpx

URL = "http://127.0.0.1:8000/api/v1/resolve"

payload = {
    "complaint": (
        "My broadband drops every evening around 8 "
        "and I have already restarted the router twice. "
        "I work from home and this is costing me."
    )
}


def main() -> None:
    print("Sending request...")

    try:
        response = httpx.post(
            URL,
            json=payload,
            timeout=180.0,
        )

        print(f"HTTP status: {response.status_code}")

        if response.is_error:
            print("ERROR RESPONSE:")
            print(response.text)
            return

        data = response.json()

        print("\n=== RESOLUTION RESULT ===")
        print("Summary:")
        print(data["resolution"]["summary"])

        print("\nConfidence:")
        print(data["resolution"]["confidence"])

        print("\nGrounded:")
        print(data["grounding"]["is_grounded"])

        print("\nAuthoritative evidence:")
        print(
            data["grounding"][
                "authoritative_evidence_count"
            ]
        )

        print("\nRecommended steps:")
        for index, step in enumerate(
            data["resolution"]["recommended_steps"],
            start=1,
        ):
            print(f"{index}. {step}")

        print("\nFull response:")
        print(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            )
        )

    except Exception as exc:
        print("\nREQUEST FAILED")
        print(type(exc).__name__)
        print(str(exc))


if __name__ == "__main__":
    main()