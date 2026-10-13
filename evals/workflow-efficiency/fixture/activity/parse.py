import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class Event:
    category: str
    amount: Decimal
    timestamp: str | None = None


def load_events(path: str | Path) -> list[Event]:
    with open(path, newline='', encoding='utf-8') as stream:
        return [Event(row['category'], Decimal(row['amount']), row.get('timestamp'))
                for row in csv.DictReader(stream)]
