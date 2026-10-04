#!/usr/bin/env python3
"""Mint, validate and resolve masked intent tokens for MCP tool calls.

The token is what travels to the MCP server. The intent text it stands for
stays in a local, mode-0600 ledger that only this machine can read.

A token minted under --operation is reused for every later call naming that
same operation in the same session, so a stateful server still sees one
correlated operation instead of a stream of unrelated UUIDs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UUID4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def is_valid_uuid4(value: str) -> bool:
    return bool(UUID4_PATTERN.match(value.strip()))


def ledger_path() -> Path:
    override = os.environ.get("INTENT_MASKING_DIR")
    if override:
        return Path(override).expanduser() / "ledger.jsonl"
    claude_dir = os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude"
    return Path(claude_dir).expanduser() / "intent-masking" / "ledger.jsonl"


def current_session() -> str | None:
    return os.environ.get("CLAUDE_CODE_SESSION_ID")


def read_records() -> list[dict[str, Any]]:
    path = ledger_path()
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def append_record(record: dict[str, Any]) -> None:
    path = ledger_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def operation_token(operation: str) -> str | None:
    session = current_session()
    for record in reversed(read_records()):
        if record.get("operation") == operation and record.get("session") == session:
            return str(record["intent_id"])
    return None


def mask(tool: str, intent: str | None, operation: str | None = None) -> str:
    if operation:
        existing = operation_token(operation)
        if existing:
            return existing
    intent_id = str(uuid.uuid4())
    append_record(
        {
            "intent_id": intent_id,
            "tool": tool,
            "operation": operation,
            "session": current_session(),
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "intent": intent,
        }
    )
    return intent_id


def resolve(intent_id: str) -> dict[str, Any] | None:
    if not is_valid_uuid4(intent_id):
        return None
    wanted = intent_id.strip().lower()
    for record in reversed(read_records()):
        if str(record.get("intent_id", "")).lower() == wanted:
            return record
    return None


def trail(
    operation: str | None = None,
    every_session: bool = False,
    limit: int = 20,
) -> list[dict[str, Any]]:
    session = current_session()
    matches = [
        record
        for record in read_records()
        if (every_session or record.get("session") == session)
        and (operation is None or record.get("operation") == operation)
    ]
    return matches[-limit:]


def format_trail(records: list[dict[str, Any]]) -> str:
    if not records:
        return "no masked intents recorded"
    return "\n".join(
        " | ".join(
            [
                str(record.get("created_at", "?")),
                str(record.get("intent_id", "?")),
                str(record.get("operation") or "-"),
                str(record.get("tool", "?")),
                str(record.get("intent") or "-"),
            ]
        )
        for record in records
    )


def read_intent(value: str | None) -> str | None:
    if value == "-":
        return sys.stdin.read().strip() or None
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mask_intent", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    mask_cmd = sub.add_parser(
        "mask", help="mint a token to send instead of intent text"
    )
    mask_cmd.add_argument("--tool", required=True, help="MCP tool the token is for")
    mask_cmd.add_argument(
        "--intent",
        help="intent text to keep in the local ledger; '-' reads it from stdin",
    )
    mask_cmd.add_argument(
        "--operation",
        help="label for the operation; later calls under this label reuse its token",
    )

    check_cmd = sub.add_parser("check", help="verify a value is a UUIDv4, not raw text")
    check_cmd.add_argument("value")

    resolve_cmd = sub.add_parser("resolve", help="look up what a token stands for")
    resolve_cmd.add_argument("intent_id")

    trail_cmd = sub.add_parser("trail", help="list what this session masked")
    trail_cmd.add_argument("--operation", help="only this operation label")
    trail_cmd.add_argument(
        "--all",
        action="store_true",
        dest="every_session",
        help="every session, not just this one",
    )
    trail_cmd.add_argument(
        "--limit", type=int, default=20, help="newest N records (default 20)"
    )

    args = parser.parse_args(argv)

    match args.command:
        case "mask":
            print(mask(args.tool, read_intent(args.intent), args.operation))
            return 0
        case "check":
            if is_valid_uuid4(args.value):
                print("valid uuid4")
                return 0
            print(
                f"not a uuid4: {args.value!r} must never be sent as an intent argument",
                file=sys.stderr,
            )
            return 1
        case "resolve":
            record = resolve(args.intent_id)
            if record is None:
                print(f"no ledger entry for {args.intent_id!r}", file=sys.stderr)
                return 1
            print(json.dumps(record, ensure_ascii=False, indent=2))
            return 0
        case "trail":
            print(format_trail(trail(args.operation, args.every_session, args.limit)))
            return 0
        case _:
            parser.error(f"unknown command: {args.command}")
            return 2


if __name__ == "__main__":
    sys.exit(main())
