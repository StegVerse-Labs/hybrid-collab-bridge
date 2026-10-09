"""Stdlib unittest coverage for the vendorable HCB capability contract (#38)."""
import ast
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hcb_contract import capability as cap  # noqa: E402
from hcb_contract import (  # noqa: E402
    ALLOW,
    DENY,
    FAIL_CLOSED,
    SCHEMA_ID,
    ProtocolAdapter,
    normalize_capability_descriptor,
)

SIX_FIELDS = (
    "failure_code",
    "failed_predicate",
    "required_evidence_or_repair",
    "retry_entrypoint",
    "owning_existing_goal",
    "next_attempt",
)
SCHEMA_PATH = ROOT / "schemas" / "capability_descriptor.v1.schema.json"
MANIFEST_PATH = ROOT / "hcb_contract" / "VENDOR_MANIFEST.json"

DESCRIPTOR = {
    "capability_id": "image-generate",
    "work_class": "image",
    "input_media": ["text"],
    "output_media": ["image"],
    "provider": "example-image-provider",
    "entitlement_state": "NOT_ENTITLED",
    "routing_disposition": "UPGRADE_REQUIRED",
    "required_tier": "pro",
    "execution_constraints": {"ephemeral_surface": True},
}


def _all_keys(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from _all_keys(v)
    elif isinstance(value, list):
        for v in value:
            yield from _all_keys(v)


class SixFieldAssertions:
    def assert_non_allow(self, result, disposition, failure_code):
        data = result.to_dict()
        self.assertEqual(data["disposition"], disposition)
        self.assertEqual(data["failure_code"], failure_code)
        for key in SIX_FIELDS:
            self.assertIsInstance(data[key], str, key)
            self.assertTrue(data[key], key)
        self.assertEqual(data["owning_existing_goal"], "HCB-VERSIONED-CONTRACT-038")
        self.assertEqual(data["authority_effect"], "NONE")
        self.assertIsNone(data["output"])
        return data


class CapabilityDescriptorContractTests(SixFieldAssertions, unittest.TestCase):
    def test_round_trip_is_deterministic(self):
        first = normalize_capability_descriptor(DESCRIPTOR)
        self.assertEqual(first.disposition, ALLOW)
        self.assertEqual(first.output["schema"], SCHEMA_ID)
        second = normalize_capability_descriptor(json.loads(json.dumps(first.output)))
        self.assertEqual(second.output, first.output)
        self.assertEqual(second.evidence["descriptor_sha256"], first.evidence["descriptor_sha256"])
        reordered = dict(reversed(list(DESCRIPTOR.items())))
        self.assertEqual(normalize_capability_descriptor(reordered).to_dict(), first.to_dict())

    def test_defaults_match_existing_model_defaults(self):
        out = normalize_capability_descriptor(
            {"capability_id": "text-generate", "work_class": "text", "provider": "mock"}
        ).output
        self.assertEqual(out["entitlement_state"], "UNKNOWN")
        self.assertEqual(out["routing_disposition"], "ENTITLEMENT_UNKNOWN")
        self.assertEqual(out["evidence_return"], "RETAINED_OBSERVATION_REQUIRED")
        self.assertEqual(out["authority_effect"], "NONE")
        self.assertEqual(sorted(out), sorted(cap.DESCRIPTOR_FIELDS))

    def test_schema_version_mismatch_denied(self):
        result = normalize_capability_descriptor(dict(DESCRIPTOR, schema="stegverse.hybrid-collab.capability-descriptor/v2"))
        self.assert_non_allow(result, DENY, "CAPABILITY_SCHEMA_VERSION_MISMATCH")

    def test_unsupported_media_denied(self):
        result = normalize_capability_descriptor(dict(DESCRIPTOR, input_media=["hologram"]))
        self.assert_non_allow(result, DENY, "UNSUPPORTED_MEDIA_TYPE")

    def test_authority_claim_denied(self):
        result = normalize_capability_descriptor(dict(DESCRIPTOR, authority_effect="ALLOW"))
        self.assert_non_allow(result, DENY, "AUTHORITY_CLAIM_NOT_PERMITTED")

    def test_credentials_in_descriptor_denied(self):
        result = normalize_capability_descriptor(dict(DESCRIPTOR, api_key="sk-live-123"))
        data = self.assert_non_allow(result, DENY, "CREDENTIAL_MATERIAL_IN_DESCRIPTOR")
        self.assertNotIn("sk-live-123", json.dumps(data))
        nested = dict(DESCRIPTOR, execution_constraints={"auth": {"bearer": "x"}})
        self.assert_non_allow(normalize_capability_descriptor(nested), DENY, "CREDENTIAL_MATERIAL_IN_DESCRIPTOR")

    def test_contract_enums_match_schema_file(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        props = schema["properties"]
        self.assertEqual(schema["$id"], SCHEMA_ID)
        self.assertEqual(props["schema"]["const"], SCHEMA_ID)
        self.assertEqual(props["authority_effect"]["const"], "NONE")
        self.assertIn("schema", schema["required"])
        self.assertEqual(sorted(props), sorted(cap.DESCRIPTOR_FIELDS))
        self.assertEqual(tuple(props["work_class"]["enum"]), cap.WORK_CLASSES)
        self.assertEqual(tuple(schema["$defs"]["media_type"]["enum"]), cap.MEDIA_TYPES)
        self.assertEqual(tuple(props["entitlement_state"]["enum"]), cap.ENTITLEMENT_STATES)
        self.assertEqual(tuple(props["routing_disposition"]["enum"]), cap.ROUTING_DISPOSITIONS)

    def test_pydantic_model_fields_match_schema(self):
        """api/app/models.py CapabilityDescriptor stays the single canonical shape (parsed, not imported)."""
        tree = ast.parse((ROOT / "api" / "app" / "models.py").read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "CapabilityDescriptor")
        fields = [n.target.id for n in cls.body if isinstance(n, ast.AnnAssign)]
        model_fields = ["schema" if f == "schema_id" else f for f in fields]
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(sorted(model_fields), sorted(schema["properties"]))
        default_call = next(n for n in cls.body if isinstance(n, ast.AnnAssign) and n.target.id == "schema_id").value
        alias = next(k.value.value for k in default_call.keywords if k.arg == "alias")
        self.assertEqual(alias, "schema")


class ProtocolAdapterTests(SixFieldAssertions, unittest.TestCase):
    def setUp(self):
        self.adapter = ProtocolAdapter()

    def test_recognized_hcb_task_translates_deterministically(self):
        envelope = {
            "protocol": "hcb.task",
            "protocol_version": "v1",
            "media_type": "text",
            "payload": {"task_type": "text-generate", "prompt": "hello", "options": {"temperature": 0.2}},
        }
        first = self.adapter.translate(envelope)
        self.assertEqual(first.disposition, ALLOW)
        self.assertEqual(first.output["prompt"], "hello")
        self.assertEqual(first.output["authority_effect"], "NONE")
        self.assertTrue(first.input_sha256.startswith("sha256:"))
        self.assertEqual(first.evidence["mapping_version"], "v1")
        self.assertTrue(first.evidence["mapping_sha256"].startswith("sha256:"))
        self.assertIn("transformation", first.evidence)
        self.assertEqual(self.adapter.translate(json.loads(json.dumps(envelope))).to_dict(), first.to_dict())

    def test_recognized_ollama_generate_strips_credentials(self):
        envelope = {
            "protocol": "ollama.generate",
            "protocol_version": "v1",
            "media_type": "text",
            "payload": {
                "model": "llama3.1",
                "prompt": "hi",
                "stream": False,
                "options": {"num_predict": 1200, "max_tokens": 5, "api_key": "sk-secret"},
                "authorization": "Bearer sk-secret",
            },
        }
        result = self.adapter.translate(envelope)
        self.assertEqual(result.disposition, ALLOW)
        self.assertEqual(result.output["model"], "llama3.1")
        self.assertEqual(result.output["options"], {"max_tokens": 5, "num_predict": 1200, "stream": False})
        self.assertEqual(result.evidence["transformation"]["redacted_field_count"], 1)
        dumped = json.dumps(result.to_dict())
        self.assertNotIn("sk-secret", dumped)
        self.assertFalse([k for k in _all_keys(result.to_dict()) if cap.is_secret_like_key(k)])

    def test_unknown_protocol_fails_closed_with_candidate_evidence(self):
        envelope = {
            "protocol": "novel.chat",
            "protocol_version": "v9",
            "media_type": "text",
            "payload": {"messages": [{"role": "user", "content": "x"}], "api_key": "sk-secret"},
        }
        result = self.adapter.translate(envelope)
        data = self.assert_non_allow(result, FAIL_CLOSED, "UNKNOWN_PROTOCOL")
        candidate = data["evidence"]["candidate_mapping"]
        self.assertFalse(candidate["selectable"])
        self.assertEqual(candidate["authority_effect"], "NONE")
        self.assertEqual(candidate["proposed_prompt_field"], "messages")
        self.assertNotIn("api_key", candidate["observed_fields"])
        self.assertIn("SDK", data["retry_entrypoint"])
        self.assertNotIn("sk-secret", json.dumps(data))
        self.assertTrue(data["input_sha256"].startswith("sha256:"))

    def test_unsupported_media_denied(self):
        envelope = {
            "protocol": "hcb.task",
            "protocol_version": "v1",
            "media_type": "video",
            "payload": {"task_type": "text-generate", "prompt": "hello"},
        }
        self.assert_non_allow(self.adapter.translate(envelope), DENY, "UNSUPPORTED_MEDIA_TYPE")

    def test_version_mismatch_denied(self):
        envelope = {
            "protocol": "ollama.generate",
            "protocol_version": "v2",
            "media_type": "text",
            "payload": {"prompt": "hello"},
        }
        self.assert_non_allow(self.adapter.translate(envelope), DENY, "PROTOCOL_VERSION_MISMATCH")

    def test_malformed_envelope_fails_closed(self):
        self.assert_non_allow(self.adapter.translate({"protocol": "hcb.task"}), FAIL_CLOSED, "MALFORMED_PROTOCOL_ENVELOPE")

    def test_every_output_is_non_authorizing_and_secret_free(self):
        envelopes = [
            {"protocol": "hcb.task", "protocol_version": "v1", "payload": {"task_type": "text-generate", "prompt": "a", "options": {"token": "t"}}},
            {"protocol": "hcb.task", "protocol_version": "v1", "payload": {"task_type": "image", "prompt": "a"}},
            {"protocol": "x", "protocol_version": "v1", "payload": {"password": "p", "text": "a"}},
        ]
        results = [self.adapter.translate(e).to_dict() for e in envelopes]
        results.append(normalize_capability_descriptor(DESCRIPTOR).to_dict())
        for data in results:
            self.assertEqual(data["authority_effect"], "NONE")
            if data["output"]:
                self.assertEqual(data["output"]["authority_effect"], "NONE")
            self.assertFalse([k for k in _all_keys(data) if cap.is_secret_like_key(k)], data)


class VendorManifestTests(unittest.TestCase):
    def test_manifest_digests_match_files(self):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["authority_effect"], "NONE")
        self.assertEqual(manifest["dependencies"], [])
        self.assertIn("schemas/capability_descriptor.v1.schema.json", manifest["files"])
        self.assertIn("hcb_contract/capability.py", manifest["files"])
        for rel, digest in manifest["files"].items():
            actual = "sha256:" + hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
            self.assertEqual(actual, digest, rel)

    def test_contract_imports_stdlib_only(self):
        allowed = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
        for path in (ROOT / "hcb_contract").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [node.module.split(".")[0]]
                else:
                    continue
                for name in names:
                    if allowed:
                        self.assertIn(name, allowed, f"{path.name} imports {name}")


if __name__ == "__main__":
    unittest.main()
