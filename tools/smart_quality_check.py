"""Offline safety regression against synthetic CoD2-like examples.

This does NOT measure real translation accuracy, GPU/CPU gameplay cost or model
quality. It verifies that the semantic guard rejects known meaning damage and
accepts non-damaging reference examples when a stub MT response is supplied.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from smart_engine import SmartTranslationEngine, TranslationRequest  # noqa: E402


def main() -> int:
    cases = json.loads(
        (ROOT / "tests" / "fixtures" / "smart_semantic_cases.json")
        .read_text(encoding="utf-8")
    )
    passed = 0
    unsafe_accepted = 0
    valid_rejected = 0
    rejected_by_reason: dict[str, int] = {}
    for case in cases:
        response = case["mt_stub"]
        result = SmartTranslationEngine().translate(
            TranslationRequest(
                text=case["source"],
                target_lang=case["target"],
                source_lang="auto",
                use_slang=False,
            ),
            provider=lambda *_: response,
        )
        expected_safe = case["should_accept"]
        if result.safe == expected_safe:
            passed += 1
        elif expected_safe:
            valid_rejected += 1
        else:
            unsafe_accepted += 1
        if not result.safe:
            for reason in result.uncertainty_reasons:
                rejected_by_reason[reason] = rejected_by_reason.get(reason, 0) + 1
        if result.safe != expected_safe:
            print("FAIL", case["id"], "expected", expected_safe, "got", result)
    print(f"Synthetic semantic guard: {passed}/{len(cases)} passed")
    print(f"unsafe_accepted={unsafe_accepted}; valid_rejected={valid_rejected}")
    print("rejected_by_reason=", dict(sorted(rejected_by_reason.items())))
    print("Important: This is an invariant regression, NOT a real gameplay MT benchmark.")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
