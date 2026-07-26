from pathlib import Path

import pytest

from tools.validate_hil_independent_response import validate_packet


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "hil_independent_response.schema.json"
PACKET = ROOT / "evidence" / "hil-independent-responses" / "HIL-RESP-GPT56-20260726-001.json"

INVALID_FIXTURES = [
    ROOT / "examples" / "hil-independent-response.invalid-canonical-altered.json",
    ROOT / "examples" / "hil-independent-response.invalid-disagreement-suppressed.json",
    ROOT / "examples" / "hil-independent-response.invalid-publication-authority.json",
    ROOT / "examples" / "hil-independent-response.invalid-master-record.json",
    ROOT / "examples" / "hil-independent-response.invalid-hash.json",
]


def test_canonical_independent_response_packet_validates() -> None:
    assert validate_packet(PACKET, SCHEMA) == []


@pytest.mark.parametrize("fixture", INVALID_FIXTURES, ids=lambda path: path.stem)
def test_invalid_independent_response_packets_fail_closed(fixture: Path) -> None:
    assert validate_packet(fixture, SCHEMA)
