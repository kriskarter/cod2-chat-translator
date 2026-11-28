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

from smart_engine import SmartTranslationEngine, TranslationRequest, semantic_violations  # noqa: E402


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
        # Original full-response fixtures still exercise the guard directly.
        violations = semantic_violations(case["source"], response, case["target"])
        if (not violations) != case["should_accept"]:
            print("FAIL raw semantic guard", case["id"], violations)
            continue
        # The transport now receives just the prose beside an address.
        # Model its reply to that input independently from the old full-message fixture.
        def provider(text, *_):
            if "provider_input" in case:
                assert text == case["provider_input"], (case["id"], text)
            return case.get("provider_reply", response)
        result = SmartTranslationEngine().translate(
            TranslationRequest(
                text=case["source"],
                target_lang=case["target"],
                source_lang="auto",
                use_slang=False,
            ),
            provider=provider,
        )
        expected_safe = case["should_accept"] or "protected_output" in case
        if "protected_output" in case and result.text != case["protected_output"]:
            print("FAIL protected output", case["id"], result.text)
            continue
        if result.safe and semantic_violations(case["source"], result.text, case["target"]):
            print("FAIL reassembled message", case["id"], result.text)
            continue
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
