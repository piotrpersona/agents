"""Tests for the intent masking script."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import mask_intent

SCRIPT = Path(__file__).parent / "mask_intent.py"


class TestUUID4Validation(unittest.TestCase):
    def test_accepts_and_rejects(self) -> None:
        cases: list[tuple[str, str, bool]] = [
            ("canonical v4", "f47ac10b-58cc-4372-a567-0e02b2c3d479", True),
            ("uppercase v4", "F47AC10B-58CC-4372-A567-0E02B2C3D479", True),
            ("padded v4", "  f47ac10b-58cc-4372-a567-0e02b2c3d479\n", True),
            ("raw intent text", "Process refund for John Doe SSN 123-45-6789", False),
            ("leaky slug", "query_user_account_details", False),
            ("v1 uuid", "f47ac10b-58cc-1372-a567-0e02b2c3d479", False),
            ("bad variant nibble", "f47ac10b-58cc-4372-7567-0e02b2c3d479", False),
            ("nil uuid", "00000000-0000-0000-0000-000000000000", False),
            (
                "uuid plus trailing text",
                "f47ac10b-58cc-4372-a567-0e02b2c3d479 for acct 9",
                False,
            ),
            ("empty", "", False),
        ]
        for name, value, expected in cases:
            with self.subTest(name):
                self.assertEqual(mask_intent.is_valid_uuid4(value), expected)


class TestLedger(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        os.environ["INTENT_MASKING_DIR"] = self.tmp.name
        self.addCleanup(os.environ.pop, "INTENT_MASKING_DIR", None)

    def test_mask_mints_uuid4_and_resolves_back(self) -> None:
        intent_id = mask_intent.mask(
            "mcp__caveman__caveman_compress", "summarize branch diff"
        )
        self.assertTrue(mask_intent.is_valid_uuid4(intent_id))
        record = mask_intent.resolve(intent_id)
        assert record is not None
        self.assertEqual(record["intent"], "summarize branch diff")
        self.assertEqual(record["tool"], "mcp__caveman__caveman_compress")

    def test_mask_without_intent_text_still_mints_token(self) -> None:
        intent_id = mask_intent.mask("mcp__arxiv__search_papers", None)
        record = mask_intent.resolve(intent_id)
        assert record is not None
        self.assertIsNone(record["intent"])

    def test_operation_label_reuses_one_token(self) -> None:
        os.environ["CLAUDE_CODE_SESSION_ID"] = "sess-a"
        self.addCleanup(os.environ.pop, "CLAUDE_CODE_SESSION_ID", None)
        first = mask_intent.mask(
            "mcp__a__one", "audit the ledger", operation="audit-ledger"
        )
        second = mask_intent.mask("mcp__b__two", None, operation="audit-ledger")
        self.assertEqual(first, second)
        self.assertEqual(len(mask_intent.read_records()), 1)

    def test_different_operations_get_different_tokens(self) -> None:
        first = mask_intent.mask("tool", None, operation="one")
        second = mask_intent.mask("tool", None, operation="two")
        self.assertNotEqual(first, second)

    def test_operation_token_does_not_cross_sessions(self) -> None:
        os.environ["CLAUDE_CODE_SESSION_ID"] = "sess-a"
        self.addCleanup(os.environ.pop, "CLAUDE_CODE_SESSION_ID", None)
        first = mask_intent.mask("tool", None, operation="shared-label")
        os.environ["CLAUDE_CODE_SESSION_ID"] = "sess-b"
        self.assertNotEqual(
            mask_intent.mask("tool", None, operation="shared-label"), first
        )

    def test_masking_without_operation_never_reuses(self) -> None:
        first = mask_intent.mask("tool", "same text")
        second = mask_intent.mask("tool", "same text")
        self.assertNotEqual(first, second)

    def test_record_carries_the_claude_code_session(self) -> None:
        os.environ["CLAUDE_CODE_SESSION_ID"] = "sess-123"
        self.addCleanup(os.environ.pop, "CLAUDE_CODE_SESSION_ID", None)
        record = mask_intent.resolve(mask_intent.mask("tool", None))
        assert record is not None
        self.assertEqual(record["session"], "sess-123")

    def test_tokens_are_unique_per_call(self) -> None:
        tokens = {mask_intent.mask("tool", "same intent") for _ in range(5)}
        self.assertEqual(len(tokens), 5)

    def test_ledger_is_owner_only(self) -> None:
        mask_intent.mask("tool", "secret")
        path = mask_intent.ledger_path()
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)

    def test_resolve_rejects_raw_text_and_unknown_tokens(self) -> None:
        mask_intent.mask("tool", "known")
        self.assertIsNone(mask_intent.resolve("Process refund for John Doe"))
        self.assertIsNone(mask_intent.resolve("f47ac10b-58cc-4372-a567-0e02b2c3d479"))

    def test_resolve_without_ledger(self) -> None:
        self.assertIsNone(mask_intent.resolve("f47ac10b-58cc-4372-a567-0e02b2c3d479"))


class TestTrail(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        os.environ["INTENT_MASKING_DIR"] = self.tmp.name
        self.addCleanup(os.environ.pop, "INTENT_MASKING_DIR", None)
        os.environ["CLAUDE_CODE_SESSION_ID"] = "sess-now"
        self.addCleanup(os.environ.pop, "CLAUDE_CODE_SESSION_ID", None)

    def test_trail_is_scoped_to_this_session_unless_asked(self) -> None:
        mask_intent.mask("tool", "now", operation="now-op")
        os.environ["CLAUDE_CODE_SESSION_ID"] = "sess-old"
        mask_intent.mask("tool", "earlier", operation="old-op")
        os.environ["CLAUDE_CODE_SESSION_ID"] = "sess-now"

        self.assertEqual([r["intent"] for r in mask_intent.trail()], ["now"])
        self.assertEqual(
            sorted(r["intent"] for r in mask_intent.trail(every_session=True)),
            ["earlier", "now"],
        )

    def test_trail_filters_by_operation_and_limit(self) -> None:
        mask_intent.mask("tool", "one", operation="op-a")
        mask_intent.mask("tool", "two", operation="op-b")
        self.assertEqual(
            [r["intent"] for r in mask_intent.trail(operation="op-b")], ["two"]
        )
        self.assertEqual([r["intent"] for r in mask_intent.trail(limit=1)], ["two"])

    def test_trail_renders_one_line_per_record(self) -> None:
        self.assertEqual(mask_intent.format_trail([]), "no masked intents recorded")
        intent_id = mask_intent.mask("mcp__x__y", "read the ledger", operation="op-a")
        rendered = mask_intent.format_trail(mask_intent.trail())
        self.assertEqual(len(rendered.splitlines()), 1)
        for field in (intent_id, "op-a", "mcp__x__y", "read the ledger"):
            self.assertIn(field, rendered)


class TestCommandLine(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = {**os.environ, "INTENT_MASKING_DIR": self.tmp.name}

    def run_cli(
        self, *args: str, stdin: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            input=stdin,
            env=self.env,
            check=False,
        )

    def test_mask_check_resolve_round_trip(self) -> None:
        minted = self.run_cli(
            "mask",
            "--tool",
            "mcp__serena__find_symbol",
            "--intent",
            "-",
            stdin="locate the transaction repository\n",
        )
        self.assertEqual(minted.returncode, 0, minted.stderr)
        intent_id = minted.stdout.strip()

        checked = self.run_cli("check", intent_id)
        self.assertEqual(checked.returncode, 0, checked.stderr)

        resolved = self.run_cli("resolve", intent_id)
        self.assertEqual(resolved.returncode, 0, resolved.stderr)
        record = json.loads(resolved.stdout)
        self.assertEqual(record["intent"], "locate the transaction repository")
        self.assertEqual(record["tool"], "mcp__serena__find_symbol")

    def test_check_fails_on_raw_intent(self) -> None:
        result = self.run_cli("check", "Process refund for John Doe SSN 123-45-6789")
        self.assertEqual(result.returncode, 1)
        self.assertIn("never be sent", result.stderr)

    def test_operation_reuse_through_the_cli(self) -> None:
        self.env["CLAUDE_CODE_SESSION_ID"] = "sess-cli"
        first = self.run_cli(
            "mask", "--tool", "mcp__a__one", "--operation", "deploy-check"
        )
        second = self.run_cli(
            "mask", "--tool", "mcp__a__two", "--operation", "deploy-check"
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout.strip(), second.stdout.strip())

        listed = self.run_cli("trail", "--operation", "deploy-check")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(len(listed.stdout.strip().splitlines()), 1)
        self.assertIn(first.stdout.strip(), listed.stdout)

    def test_trail_without_records(self) -> None:
        result = self.run_cli("trail")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no masked intents recorded", result.stdout)

    def test_resolve_unknown_token_fails(self) -> None:
        result = self.run_cli("resolve", "f47ac10b-58cc-4372-a567-0e02b2c3d479")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no ledger entry", result.stderr)


if __name__ == "__main__":
    unittest.main()
