from .parse import load_events
from .report import summarize


def build_report(path):
    return summarize(load_events(path))
