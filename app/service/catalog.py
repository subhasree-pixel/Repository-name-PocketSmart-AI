from urllib.parse import quote_plus


CATALOG = [
    {
        "name": "Minimal Pendant Light",
        "category": "lighting",
        "platform": "IKEA",
        "price": 2499,
        "tags": [
            "modern",
            "living",
            "bedroom",
        ],
    },
    {
        "name": "3-Blade Ceiling Fan",
        "category": "fan",
        "platform": "Amazon",
        "price": 3299,
        "tags": [
            "modern",
            "bedroom",
            "living",
        ],
    },
    {
        "name": "Compact 4-Seater Dining Table",
        "category": "dining",
        "platform": "IKEA",
        "price": 11990,
        "tags": [
            "modern",
            "dining",
            "compact",
        ],
    },
    {
        "name": "Ergonomic Accent Chair",
        "category": "furniture",
        "platform": "Amazon",
        "price": 7499,
        "tags": [
            "modern",
            "living",
            "elegant",
        ],
    },
    {
        "name": "Textured Wall Art Set",
        "category": "decor",
        "platform": "Flipkart",
        "price": 1899,
        "tags": [
            "modern",
            "boho",
            "living",
        ],
    },
    {
        "name": "Warm LED Strip Kit",
        "category": "lighting",
        "platform": "Amazon",
        "price": 1299,
        "tags": [
            "modern",
            "bedroom",
        ],
    },
    {
        "name": "Party Catering Combo",
        "category": "catering",
        "platform": "Swiggy",
        "price": 499,
        "per_guest": True,
        "tags": [
            "birthday",
            "corporate",
            "mixed",
        ],
    },
    {
        "name": "Premium Catering Buffet",
        "category": "catering",
        "platform": "Zomato",
        "price": 699,
        "per_guest": True,
        "tags": [
            "wedding",
            "corporate",
            "mixed",
        ],
    },
    {
        "name": "Event Decoration Starter",
        "category": "decoration",
        "platform": "Amazon",
        "price": 5999,
        "tags": [
            "birthday",
            "home",
        ],
    },
    {
        "name": "Banquet Venue Package",
        "category": "venue",
        "platform": "OYO",
        "price": 18000,
        "tags": [
            "birthday",
            "corporate",
            "wedding",
        ],
    },
    {
        "name": "Elegant Kundan Drop Earrings",
        "category": "earrings",
        "platform": "Amazon",
        "price": 2499,
        "tags": [
            "wedding",
            "elegant",
            "red",
            "gold",
        ],
    },
    {
        "name": "Pearl Necklace Set",
        "category": "necklace",
        "platform": "Flipkart",
        "price": 3299,
        "tags": [
            "wedding",
            "elegant",
            "blue",
            "pastel",
        ],
    },
    {
        "name": "Minimal Gold-Plated Bracelet",
        "category": "bracelet",
        "platform": "Amazon",
        "price": 1799,
        "tags": [
            "party",
            "minimal",
            "any",
        ],
    },
    {
        "name": "Statement Choker Set",
        "category": "necklace",
        "platform": "Flipkart",
        "price": 4599,
        "tags": [
            "wedding",
            "festive",
            "red",
            "green",
        ],
    },
]


def search_catalog(
    categories: list[str],
    budget: float,
    tags: list[str],
    limit: int = 8,
):
    """
    Search the local mock catalog.

    This is deliberately deterministic so the
    application can run without external APIs.
    """

    scored = []

    normalized_tags = [
        tag.lower()
        for tag in tags
        if tag
    ]

    for item in CATALOG:

        if item["category"] not in categories:
            continue

        if item.get("per_guest"):
            continue

        if item["price"] > budget:
            continue

        item_tags = [
            tag.lower()
            for tag in item["tags"]
        ]

        score = sum(
            1
            for tag in normalized_tags
            if tag in item_tags
        )

        scored.append(
            (
                score,
                item,
            )
        )

    scored.sort(
        key=lambda value: (
            -value[0],
            value[1]["price"],
        )
    )

    results = []

    for _, item in scored[:limit]:

        copy = dict(item)

        search_query = quote_plus(
            f"{item['platform']} {item['name']}"
        )

        copy["url"] = (
            "https://www.google.com/search?q="
            + search_query
        )

        results.append(copy)

    return results