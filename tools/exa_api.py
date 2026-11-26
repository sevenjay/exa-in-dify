from typing import Any

import requests


def max_age_hours(value: int | float | str | None) -> int | None:
    if value is None:
        return None
    hours = int(value)
    if hours != float(value) or not -1 <= hours <= 720:
        raise ValueError("Max age must be a whole number from -1 to 720 hours.")
    return hours


def post(api_key: str, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(
        f"https://api.exa.ai/{endpoint}",
        json=payload,
        headers={
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "x-exa-integration": "dify-community-integration",
        },
        timeout=(5, 50),
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        try:
            detail = response.json().get("error")
        except (ValueError, AttributeError):
            detail = None
        message = f"Exa /{endpoint} returned HTTP {response.status_code}"
        if detail:
            message += f": {detail}"
        raise ValueError(message) from error
    return response.json()
