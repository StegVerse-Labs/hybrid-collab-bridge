from app.governance.artifact_integrity import evaluate_artifact_integrity


def test_complete_artifact_reaches_next_boundary_only():
    content = "PURPOSE\nText\n\nSAFETY RULES\nText\n\nSTATUS\nPrototype"
    result = evaluate_artifact_integrity(
        content,
        required_sections=["Purpose", "Safety Rules", "Status"],
    )

    assert result.decision == "ALLOW_NEXT_BOUNDARY"
    assert result.passed is True
    assert result.missing_sections == ()
    assert len(result.content_sha256) == 64
    assert "downstream admissibility remains pending" in result.reasoning


def test_missing_declared_section_requires_repair():
    result = evaluate_artifact_integrity(
        "PURPOSE\nText\n\nSTATUS\nPrototype",
        required_sections=["Purpose", "Safety Rules", "Status"],
    )

    assert result.decision == "NEEDS_REPAIR"
    assert result.passed is False
    assert result.missing_sections == ("Safety Rules",)


def test_empty_artifact_fails_closed():
    result = evaluate_artifact_integrity("   ", required_sections=["Purpose"])

    assert result.decision == "FAIL_CLOSED"
    assert result.empty is True
    assert result.missing_sections == ("Purpose",)


def test_duplicate_requirements_are_deduplicated_without_reordering():
    result = evaluate_artifact_integrity(
        "PURPOSE",
        required_sections=["Purpose", "Purpose", "  Purpose  "],
    )

    assert result.required_sections == ("Purpose",)
