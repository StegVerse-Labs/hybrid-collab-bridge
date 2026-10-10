# Master Records Role (canonical, downstream only)

Source of truth: `StegVerse-org/.github/docs/ORGANIZATION_ROLE_RUNTIME_REALITY_DEPLOYMENT.md`.
Tracking: `StegVerse-Labs/hybrid-collab-bridge#38` (goal `HCB-VERSIONED-CONTRACT-038`), `StegVerse-org/LLM-adapter#368`.

Master Records is the **recorder of released organization batch receipts**. It is
downstream evidence preservation only.

```text
Master Records != authority
Master Records != gate
Master Records != custody
Master Records != runtime reality
nothing awaits Master Records
```

For this repository that means:

- no bridge decision, activation, admission, delegation, transport, or release
  step is blocked on, ordered behind, or conditioned on a Master Records record;
- Master Records is never a destination for candidates, delegation results,
  acknowledgements, or lifecycle state; it may record a batch receipt only after
  that batch has already been released by its own authority;
- Master Records does not issue or return final receipts and holds no custody;
- the hybrid-collab-bridge itself is optional and non-authoritative, and every
  non-`ALLOW` decision it emits carries the six fields.

The occurrence inventory and classification for this repository is
`data/master-records-role-audit.json`, enforced by
`api/tests/test_master_records_role_audit.py`.
