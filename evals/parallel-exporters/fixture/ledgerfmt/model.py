"""Shared, protected wire schema and validation; reuse these helpers."""
from dataclasses import dataclass
from decimal import Decimal
import re

@dataclass(frozen=True)
class Record:
    account: str
    amount: Decimal
    tags: tuple[str, ...] = ()


def record_from_wire(account, amount, tags):
    if not isinstance(account, str) or not account:
        raise ValueError('account must be a nonempty string')
    if not isinstance(amount, str) or not re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?', amount):
        raise ValueError('amount must be a plain decimal string')
    if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
        raise ValueError('tags must be a list of strings')
    return Record(account, Decimal(amount), tuple(tags))


def record_to_wire(record):
    if not isinstance(record, Record) or not isinstance(record.amount, Decimal) or not record.amount.is_finite():
        raise ValueError('record must contain a finite Decimal amount')
    if not isinstance(record.tags, tuple):
        raise ValueError('record tags must be a tuple')
    amount = format(record.amount, 'f')
    valid = record_from_wire(record.account, amount, list(record.tags))
    return {'account': valid.account, 'amount': amount, 'tags': list(valid.tags)}
