from decimal import Decimal
from .parse import Event


def summarize(events: list[Event]) -> dict:
    totals: dict[str, Decimal] = {}
    for event in events:
        totals[event.category] = totals.get(event.category, Decimal('0')) + event.amount
    return {'count': len(events),
            'totals': {key: str(totals[key]) for key in sorted(totals)}}
