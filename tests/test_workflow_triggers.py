"""Workflows here run only as push / pull_request state transitions.

Ecosystem actions are manifest-bound state transitions; a manually dispatched
or clock-scheduled run is NON-CONFORMING (WORKFLOW_MANUAL_DISPATCH_PRESENT /
ACTION_IS_STATE_TRANSITION_DEPENDENT). This rule is DERIVED_FROM_INVARIANT_TEXT
(StegVerse-Labs/.github data/task-registry-global-invariants.json), not a
verbatim prohibition. YAML is read as text so no dependency is needed.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"

# Surfaces owned by another lane, handed off, not edited here. Empty: Grok Lane B's
# organization-ledger-transition.yml (commit 14c028c) is retired on main.
ALLOWLIST: set[str] = set()

FORBIDDEN = ("workflow_dispatch", "schedule")
KEY = re.compile(r"^\s*(?:-\s*)?['\"]?(%s)['\"]?\s*:" % "|".join(FORBIDDEN))
FLOW = re.compile(r"^\s*['\"]?on['\"]?\s*:\s*(.+)$")


def forbidden_triggers(text: str) -> list[str]:
    found = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0]
        match = KEY.match(line)
        if match:
            found.append(f"{number}:{match.group(1)}")
            continue
        flow = FLOW.match(line)
        if flow:
            for name in FORBIDDEN:
                if re.search(r"\b%s\b" % name, flow.group(1)):
                    found.append(f"{number}:{name}")
    return found


class WorkflowTriggerTest(unittest.TestCase):
    def workflows(self):
        return sorted(p for p in WORKFLOWS.rglob("*") if p.suffix in (".yml", ".yaml"))

    def test_no_manual_or_scheduled_triggers(self):
        self.assertTrue(self.workflows())
        for path in self.workflows():
            if path.name in ALLOWLIST:
                continue
            with self.subTest(workflow=path.name):
                self.assertEqual(forbidden_triggers(path.read_text()), [])

    def test_allowlist_names_existing_files(self):
        names = {p.name for p in self.workflows()}
        self.assertLessEqual(ALLOWLIST, names)

    def test_detector(self):
        self.assertEqual(forbidden_triggers("on:\n  workflow_dispatch:\n"), ["2:workflow_dispatch"])
        self.assertEqual(forbidden_triggers("on:\n  schedule:\n    - cron: '0 0 * * *'\n"), ["2:schedule"])
        self.assertEqual(forbidden_triggers("on: [push, workflow_dispatch]\n"), ["1:workflow_dispatch"])
        self.assertEqual(forbidden_triggers("# a workflow_dispatch run\non:\n  push:\n"), [])


if __name__ == "__main__":
    unittest.main()
