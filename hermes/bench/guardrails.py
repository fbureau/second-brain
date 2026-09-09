#!/usr/bin/env python3
"""Reliability scorecard for the Hermes edition.

Runs the adversarial suite and reports what share of "a small model got it wrong" cases the
deterministic layer catches. The number is the honest version of the project's central claim:
that a 12B model can run a second brain because the tools hold the contract.

    python3 hermes/bench/guardrails.py            # scorecard
    python3 hermes/bench/guardrails.py --verbose  # plus each case's outcome

Exit code is non-zero if any guardrail fails, so it can gate a release.
"""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "hermes" / "tests"))

GROUPS = {
    "frontmatter contract": ("invented_enum", "unknown_note_type", "missing_required", "without_a_preamble",
                             "ai_first_and_base_tag"),
    "append-only history": ("over_an_existing_note", "never_rewrites", "destructive_edit", "deleting_a_note"),
    "path safety": ("escaping_the_vault", "missing_note_says_so", "missing_note_does_not_create"),
    "people identity": ("typo_is_never", "ambiguous_first_name"),
    "retrieval honesty": ("refuses_to_answer", "never_answers_with_the_system"),
    "preview & recovery": ("preview_mode_writes_nothing", "unknown_anchor", "never_raises", "source_tool_is_hidden"),
    "contract drift": ("schema_has_a_handler", "matches_the_written_contract"),
}


def _group_of(test_id: str) -> str:
    name = test_id.rsplit(".", 1)[-1]
    for group, needles in GROUPS.items():
        if any(n in name for n in needles):
            return group
    return "other"


class Scorer(unittest.TextTestResult):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.outcomes: list[tuple[str, str, float]] = []
        self._t0 = 0.0

    def startTest(self, test):
        self._t0 = time.perf_counter()
        super().startTest(test)

    def addSuccess(self, test):
        self.outcomes.append((test.id(), "held", time.perf_counter() - self._t0))
        super().addSuccess(test)

    def addFailure(self, test, err):
        self.outcomes.append((test.id(), "LEAKED", time.perf_counter() - self._t0))
        super().addFailure(test, err)

    def addError(self, test, err):
        self.outcomes.append((test.id(), "ERROR", time.perf_counter() - self._t0))
        super().addError(test, err)


def main() -> int:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    import test_guardrails  # noqa: E402  (path set above)

    suite = unittest.defaultTestLoader.loadTestsFromModule(test_guardrails)
    runner = unittest.TextTestRunner(stream=open("/dev/null", "w"), resultclass=Scorer)
    result = runner.run(suite)

    by_group: dict[str, list[tuple[str, str, float]]] = {}
    for tid, outcome, secs in result.outcomes:
        by_group.setdefault(_group_of(tid), []).append((tid, outcome, secs))

    held = sum(1 for _, o, _ in result.outcomes if o == "held")
    total = len(result.outcomes)
    width = max(len(g) for g in by_group)
    print(f"\nSecond Brain — Hermes edition · guardrail scorecard")
    print(f"{'=' * (width + 26)}")
    for group in sorted(by_group):
        cases = by_group[group]
        ok = sum(1 for _, o, _ in cases if o == "held")
        bar = "█" * ok + "·" * (len(cases) - ok)
        print(f"{group:<{width}}  {ok:>2}/{len(cases):<2} {bar}")
        if verbose:
            for tid, outcome, secs in cases:
                mark = "  ✓" if outcome == "held" else "  ✗"
                print(f"{mark} {tid.rsplit('.', 1)[-1]:<58} {outcome:<7} {secs * 1000:5.0f} ms")
    print(f"{'=' * (width + 26)}")
    print(f"{'held':<{width}}  {held:>2}/{total:<2} "
          f"({held / total * 100:.0f}% of malformed calls refused by the code, not the prompt)")
    if held < total:
        print("\nA leaked case is a hole a small model will find. Fix the tool, not the skill text.")
    print(f"total wall time: {sum(s for _, _, s in result.outcomes):.1f}s\n")
    return 0 if held == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
