Implement two independent ledger import/export formats for an existing conversion CLI. This is a complete two-lane task with six owned files. Shared schema, CLI and protected acceptance checks are supplied; do not change them.

Shared API and schema:
- Each formatter implements load(stream) -> list[Record] and dump(records, stream) -> None for text streams. dump accepts any finite iterable of Record, including a one-shot generator, preserves input order and never mutates records or closes streams.
- Reuse protected ledgerfmt.model.record_from_wire and record_to_wire for all schema validation and Decimal encoding. account is a nonempty string; amount on the wire is a plain decimal string (no exponent, float, NaN or infinity); tags is a list of strings. Duplicate and empty tags are preserved. Decimal scale must survive round trips; record_to_wire already expands exponents for export.
- A malformed format or schema raises ValueError with useful context identifying the bad line/row. Do not allow KeyError, TypeError, JSONDecodeError details without context, or NotImplementedError to escape as data-error behavior. Stream I/O errors may propagate.
- dump must validate and serialize ALL records before writing anything to the destination. If any row is invalid, raise ValueError and leave stream content unchanged. This requirement covers data errors, not rollback after I/O errors. No flush/close requirement.
- load returns no partial result on any error. Support Unicode, embedded commas/quotes/newlines in account and tags through standard escaping/quoting. No BOM, comments, duplicate-JSON-key detection, streaming memory limits or new CLI flags are required.

Lane jsonl, owned ledgerfmt/formats/jsonl.py, tests/test_jsonl.py, docs/jsonl.md:
- One JSON object per nonblank input line, with exactly keys account, amount, tags. Ignore blank/whitespace-only lines. Reject scalars, arrays, missing/extra fields and malformed JSON. Empty input returns [].
- Emit sorted JSON object keys, ensure_ascii=False and one newline per record; empty output is ''. Standard JSON separators are fine. Use escaped newlines inside JSON strings, not additional physical lines.
- Add focused tests beyond the supplied examples, including a generator, invalid late rows, missing/extra keys and Unicode. Document API, format, sample and jsonl-to-csv CLI use.

Lane csv, owned ledgerfmt/formats/csv.py, tests/test_csv.py, docs/csv.md:
- Require exact first-row header account,amount,tags in that order; reject missing, duplicate, reordered or extra header columns. Every following CSV record must contain exactly three fields. Empty input is a header error; header-only input returns []. Blank records are errors.
- amount field uses shared schema. tags field is a JSON list of strings encoded inside a standard quoted CSV cell. Parse using csv with strict=True and standard JSON. Reject malformed quoting, bad tag JSON and wrong field count with ValueError and row context. Accept LF or CRLF and standard quoted multiline fields.
- The supplied numeric-limit regression uses tags containing a 5,000-digit integer. Standard JSON decoding may raise plain ValueError rather than JSONDecodeError; report row 2 for this data error, just as for invalid tag schema.
- Emit the header even for no records, use csv.writer with lineterminator='\n', minimal quoting, JSON ensure_ascii=False for tags. Preserve Decimal scale.
- Add focused tests beyond supplied examples, including empty/header errors, generator, multiline fields, invalid late rows, tags and row width. Document API, format, sample and csv-to-jsonl CLI use.

Integration is already wired in protected ledgerfmt/cli.py. `python3 -m ledgerfmt.cli jsonl csv` or reverse reads stdin, writes stdout and returns 2 with stderr/no stdout for invalid input. No lane needs another lane's implementation to pass its own acceptance file. Both implementations must work when merged without editing shared files.

Read model.py, the relevant acceptance/test_<lane>_contract.py and your inputs together. All files outside the six owned paths, including supplied tests and acceptance files, are protected. Do not implement shared validation again or broaden the contract. Final checks for the complete task:
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s acceptance -v
python3 -m compileall -q ledgerfmt tests acceptance

CPU only, no network/GPU, dependencies, model calls, delegation or commits. Finish after the requested implementation, tests and documentation pass. Report changed files, check results and unresolved requirements concisely.
