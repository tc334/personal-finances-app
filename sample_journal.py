from datetime import date

journal = [
    {
        "description": "Owners put money into business",
        "timestamp": date(year=2025, month=1, day=1),
        "credits": [
            {
                "amount": 100000.00,
                "account": "Tegan & Adriane",
            },
        ],
        "debits": [
            {
                "amount": 100000.00,
                "account": "WF Checking",
            },
        ],
    },
    {
        "description": "Business buys a vehicle",
        "timestamp": date(year=2025, month=1, day=2),
        "credits": [
            {
                "amount": 50000.00,
                "account": "WF Checking",
            },
        ],
        "debits": [
            {
                "amount": 50000.00,
                "account": "Snowy",
            },
        ],
    },
    {
        "description": "Vehicle depreciates",
        "timestamp": date(year=2025, month=1, day=3),
        "credits": [
            {
                "amount": 5000.00,
                "account": "Snowy",
            },
        ],
        "debits": [
            {
                "amount": 5000.00,
                "account": "Snowy (E)",
            },
        ],
    },
    {
        "vendor": "Jiffy Lube",
        "description": "Change oil in Snowy",
        "timestamp": date(year=2025, month=1, day=5),
        "credits": [
            {
                "amount": 100.00,
                "account": "WF Checking",
            }
        ],
        "debits": [
            {
                "amount": 100.00,
                "account": "Snowy (E)",
            }
        ],
    },
    {
        "vendor": "Target",
        "description": "Toothpaste and car parts",
        "timestamp": date(year=2025, month=1, day=4),
        "credits": [
            {
                "amount": 15.0,
                "account": "WF Checking",
            },
        ],
        "debits": [
            {
                "amount": 10.0,
                "account": "Snowy (E)",
            },
            {
                "amount": 5.0,
                "account": "Health Care",
            },
        ],
    },
]
