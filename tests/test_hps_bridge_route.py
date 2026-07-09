from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_hps_bridge_route import decide  # noqa: E402

EXAMPLES = ROOT / "examples"


def load_example(name: str) -> dict:
    with (EXAMPLES / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


class HpsBridgeRouteTests(unittest.TestCase):
    def test_sdk_origin_allows_next_boundary(self) -> None:
        result = decide(load_example("sdk_origin_hps_bridge_route.json"))
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.decision, "ALLOW_NEXT_BOUNDARY")

    def test_llm_origin_allows_next_boundary(self) -> None:
        result = decide(load_example("llm_origin_hps_bridge_route.json"))
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.decision, "ALLOW_NEXT_BOUNDARY")

    def test_expired_route_denies(self) -> None:
        result = decide(load_example("expired_hps_bridge_route.json"))
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.decision, "DENY")


if __name__ == "__main__":
    unittest.main()
