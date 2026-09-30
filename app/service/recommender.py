import json
import logging

from io import BytesIO
from typing import Any
from urllib.parse import quote_plus

from PIL import Image

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.schemas.planners import (
    HomeRequest,
    PartyRequest,
    JewelryRequest,
    RecommendationResponse,
    RecommendationItem,
)
from app.services.catalog import (
    CATALOG,
    search_catalog,
)


log = logging.getLogger(__name__)

settings = get_settings()

_gemini_client = None


def get_gemini_client():
    """
    Lazily initialize the Gemini client.
    """

    global _gemini_client

    if (
        _gemini_client is None
        and settings.gemini_api_key
    ):
        _gemini_client = genai.Client(
            api_key=settings.gemini_api_key
        )

    return _gemini_client


def catalog_as_json() -> str:
    """
    Convert the local catalog into prompt-safe JSON.
    """

    clean_catalog = []

    for item in CATALOG:
        clean_catalog.append(
            {
                key: value
                for key, value in item.items()
                if key != "url"
            }
        )

    return json.dumps(
        clean_catalog,
        indent=2,
    )


def call_gemini(
    prompt: str,
    image_bytes: bytes | None = None,
) -> RecommendationResponse | None:

    if settings.ai_mode.lower() == "mock":
        return None

    client = get_gemini_client()

    if not client:
        return None

    try:

        contents: list[Any] = [prompt]

        if image_bytes:

            image = Image.open(
                BytesIO(image_bytes)
            ).convert("RGB")

            contents.append(image)

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RecommendationResponse,
                temperature=0.3,
                max_output_tokens=3500,
            ),
        )

        parsed = getattr(
            response,
            "parsed",
            None,
        )

        if isinstance(
            parsed,
            RecommendationResponse,
        ):
            parsed.ai_used = True
            return parsed

        response_text = getattr(
            response,
            "text",
            None,
        )

        if not response_text:
            return None

        result = (
            RecommendationResponse
            .model_validate_json(
                response_text
            )
        )

        result.ai_used = True

        return result

    except Exception as exc:

        log.exception(
            "Gemini request failed. "
            "Using fallback engine: %s",
            exc,
        )

        return None


def make_item(
    name: str,
    category: str,
    platform: str,
    price: float,
    reason: str,
) -> RecommendationItem:

    search_query = quote_plus(
        f"{platform} {name}"
    )

    return RecommendationItem(
        name=name,
        category=category,
        platform=platform,
        price=round(
            float(price),
            2,
        ),
        reason=reason,
        url=(
            "https://www.google.com/search?q="
            + search_query
        ),
    )


def home_fallback(
    req: HomeRequest,
) -> RecommendationResponse:

    allocations = {
        "furniture": round(
            req.budget * 0.35,
            2,
        ),
        "lighting": round(
            req.budget * 0.15,
            2,
        ),
        "decor": round(
            req.budget * 0.20,
            2,
        ),
        "dining": round(
            req.budget * 0.30,
            2,
        ),
    }

    tags = [
        req.style,
        *req.rooms,
        *req.priorities,
    ]

    candidates = search_catalog(
        categories=[
            "furniture",
            "lighting",
            "decor",
            "dining",
            "fan",
        ],
        budget=req.budget,
        tags=tags,
    )

    recommendations = []

    for item in candidates[:6]:

        recommendations.append(
            make_item(
                name=item["name"],
                category=item["category"],
                platform=item["platform"],
                price=item["price"],
                reason=(
                    f"Matches your {req.style} "
                    "style and stays within "
                    "the overall budget."
                ),
            )
        )

    if not recommendations:

        recommendations.append(
            make_item(
                name="Budget-friendly room essentials",
                category="bundle",
                platform="Amazon",
                price=min(
                    req.budget,
                    5000,
                ),
                reason=(
                    "Fallback option for a "
                    "constrained budget."
                ),
            )
        )

    return RecommendationResponse(
        planner="home",
        budget=req.budget,
        allocated_total=req.budget,
        summary=(
            f"A {req.style} home plan for "
            f"{', '.join(req.rooms)} with a "
            "balanced allocation across core "
            "categories."
        ),
        allocations=allocations,
        recommendations=recommendations,
        tips=[
            "Buy high-use furniture first.",
            "Reserve 5–10% for delivery and installation.",
            "Compare dimensions before ordering.",
        ],
        ai_used=False,
    )


def party_fallback(
    req: PartyRequest,
) -> RecommendationResponse:

    allocations = {
        "catering": round(
            req.budget * 0.45,
            2,
        ),
        "venue": round(
            req.budget * 0.25,
            2,
        ),
        "decoration": round(
            req.budget * 0.15,
            2,
        ),
        "entertainment": round(
            req.budget * 0.15,
            2,
        ),
    }

    catering_price = min(
        req.budget * 0.45,
        req.guests * 499,
    )

    recommendations = [
        make_item(
            name="Party Catering Combo",
            category="catering",
            platform="Swiggy",
            price=catering_price,
            reason=(
                f"Scaled for {req.guests} guests."
            ),
        ),
        make_item(
            name="Event Decoration Starter",
            category="decoration",
            platform="Amazon",
            price=min(
                req.budget * 0.15,
                5999,
            ),
            reason=(
                "Provides a practical "
                "decoration baseline."
            ),
        ),
        make_item(
            name="Banquet Venue Package",
            category="venue",
            platform="OYO",
            price=min(
                req.budget * 0.25,
                18000,
            ),
            reason=(
                "Reference venue budget for "
                "the selected event type."
            ),
        ),
    ]

    return RecommendationResponse(
        planner="party",
        budget=req.budget,
        allocated_total=req.budget,
        summary=(
            f"A {req.event_type} plan for "
            f"{req.guests} guests in {req.city}."
        ),
        allocations=allocations,
        recommendations=recommendations,
        tips=[
            "Confirm per-person catering charges and taxes.",
            "Keep a contingency reserve for last-minute guests.",
            "Ask venues what decoration and service charges are included.",
        ],
        ai_used=False,
    )


def jewelry_fallback(
    req: JewelryRequest,
) -> RecommendationResponse:

    tags = [
        req.occasion,
        req.style,
        req.outfit_color,
        req.metal_preference,
    ]

    candidates = search_catalog(
        categories=[
            "earrings",
            "necklace",
            "bracelet",
        ],
        budget=req.budget,
        tags=tags,
    )

    recommendations = []

    for item in candidates[:6]:

        recommendations.append(
            make_item(
                name=item["name"],
                category=item["category"],
                platform=item["platform"],
                price=item["price"],
                reason=(
                    f"Selected for {req.occasion} "
                    f"and {req.style} preferences."
                ),
            )
        )

    if not recommendations:

        recommendations.append(
            make_item(
                name="Minimal Gold-Plated Bracelet",
                category="bracelet",
                platform="Amazon",
                price=min(
                    req.budget,
                    1799,
                ),
                reason=(
                    "Simple fallback option "
                    "that works across occasions."
                ),
            )
        )

    return RecommendationResponse(
        planner="jewelry",
        budget=req.budget,
        allocated_total=req.budget,
        summary=(
            f"Jewelry suggestions for a "
            f"{req.occasion} occasion with "
            f"a {req.style} aesthetic."
        ),
        allocations={
            "jewelry": req.budget
        },
        recommendations=recommendations,
        tips=[
            "Match the metal tone with the outfit hardware when possible.",
            "For statement pieces, keep the remaining jewelry simpler.",
            "Check seller ratings, material details, and return policy.",
        ],
        ai_used=False,
    )


def generate_home(
    req: HomeRequest,
) -> RecommendationResponse:

    prompt = f"""
You are PocketSmart AI's home interior
budget planner.

Use ONLY the supplied catalog as product
candidates.

Do not invent products, platforms,
prices, or URLs.

Keep every recommendation within the
user's budget.

Keep the recommendation total within
the user's budget.

USER:
{req.model_dump_json()}

CATALOG:
{catalog_as_json()}

Create:

1. A practical budget allocation.
2. Four to six recommendations.
3. Short reasons for every recommendation.
4. Practical planning tips.

Return valid structured JSON matching
the requested response schema.
"""

    result = call_gemini(prompt)

    if result:
        return result

    return home_fallback(req)


def generate_party(
    req: PartyRequest,
) -> RecommendationResponse:

    prompt = f"""
You are PocketSmart AI's event budget planner.

Use ONLY the supplied catalog as
product/service candidates.

For per-guest catering products,
calculate the total using the guest count.

Do not invent vendors, products,
prices, or URLs.

Keep the planned spend within
the user's budget.

USER:
{req.model_dump_json()}

CATALOG:
{catalog_as_json()}

Create:

1. Catering allocation.
2. Venue allocation.
3. Decoration allocation.
4. Entertainment allocation.
5. Three to six recommendations.
6. Practical event planning tips.

Return valid structured JSON.
"""

    result = call_gemini(prompt)

    if result:
        return result

    return party_fallback(req)


def generate_jewelry(
    req: JewelryRequest,
    image_bytes: bytes | None = None,
) -> RecommendationResponse:

    if image_bytes:

        image_instruction = """
An outfit image has been supplied.

Inspect visible outfit colors,
style cues and overall aesthetic.

Use those visual observations
to refine jewelry recommendations.
"""

    else:

        image_instruction = """
No outfit image was supplied.

Use the text-based outfit and
style preferences.
"""

    prompt = f"""
You are PocketSmart AI's jewelry
stylist and budget planner.

{image_instruction}

Use ONLY the supplied catalog.

Do not invent products, platforms,
prices, or URLs.

Keep all recommendations within
the user's budget.

USER:
{req.model_dump_json()}

CATALOG:
{catalog_as_json()}

Return:

1. Four to six recommendations.
2. Style-matching reasons.
3. Budget allocation.
4. Practical jewelry tips.

Return valid structured JSON.
"""

    result = call_gemini(
        prompt,
        image_bytes=image_bytes,
    )

    if result:
        return result

    return jewelry_fallback(req)