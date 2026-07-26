from pathlib import Path

from tools.validate_hil_independent_response import validate_packet


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "hil_independent_response.schema.json"
PACKET = ROOT / "evidence" / "hil-independent-responses" / "HIL-RESP-GPT56-20260726-001.json"


def test_canonical_independent_response_packet_validates() -> None:
    assert validate_packet(PACKET, SCHEMA) == []
