from datetime import date

journal = [
    {
        "description": "Owners put money into business",
        "timestamp": date(year=2025, month=1, day=1),
        "amount": 100000.00,
        "credit": "Tegan & Adriane",
        "debit": "WF Checking",
    },
    {
        "description": "Business buys a vehicle",
        "timestamp": date(year=2025, month=1, day=2),
        "amount": 50000.00,
        "credit": "WF Checking",
        "debit": "Snowy",
    },
    {
        "description": "Vehicle depreciates",
        "timestamp": date(year=2025, month=1, day=3),
        "amount": 5000.00,
        "credit": "Snowy",
        "debit": "Snowy (E)",
    },
    {
        "description": "Change oil in Snowy",
        "timestamp": date(year=2025, month=1, day=4),
        "amount": 100.00,
        "credit": "WF Checking",
        "debit": "Snowy (E)",
    },
]
