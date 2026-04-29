"""StegCGE Full Compiler — Master Governance Compiler.

For StegGhost org or dedicated StegVerse AI Authority org.
Compiles governance across all orgs, provides:
- Cross-org policy compilation
- Master StegDB backup
- Oversight and optimization
- Repair direction for failed orgs

Repo: github.com/StegGhost/StegCGE
"""
from __future__ import annotations
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .entity import EntityIdentity
from .cge_client import CGELightClient


@dataclass
class OrgStatus:
    """Status of a governed org."""
    org_id: str
    cge_tier: str  # light | full | compiler
    health: str  # healthy | degraded | failed
    last_receipt: Optional[str]
    policy_drift: bool
    needs_repair: bool


class StegCGECompiler:
    """Full compiler CGE for master governance.

    Monitors all org CGEs, compiles cross-org policy,
    directs repairs when orgs fail.

    Usage:
        compiler = StegCGECompiler()

        # Register org
        compiler.register_org("StegVerse-Labs", "light")

        # Compile cross-org policy
        policy = await compiler.compile_policy()

        # Check org health
        status = await compiler.check_org_health("StegVerse-Labs")

        # Direct repair if needed
        if status.needs_repair:
            await compiler.direct_repair("StegVerse-Labs", status)
    """

    def __init__(self):
        self.orgs: Dict[str, OrgStatus] = {}
        self.master_ledger: List[Dict[str, Any]] = []
        self.compiled_policy: Dict[str, Any] = {}

    def register_org(self, org_id: str, cge_tier: str) -> None:
        """Register an org for monitoring."""
        self.orgs[org_id] = OrgStatus(
            org_id=org_id,
            cge_tier=cge_tier,
            health="healthy",
            last_receipt=None,
            policy_drift=False,
            needs_repair=False,
        )

    async def compile_policy(self) -> Dict[str, Any]:
        """Compile cross-org policy from all registered orgs."""

        # Gather constitutions from all orgs
        constitutions = []
        for org_id, status in self.orgs.items():
            # In production, fetch from org's repo_constitution.txt
            constitution = self._fetch_org_constitution(org_id)
            if constitution:
                constitutions.append({
                    "org_id": org_id,
                    "cge_tier": status.cge_tier,
                    "constitution": constitution,
                })

        # Compile unified policy
        compiled = {
            "version": "1.0.0",
            "compiled_at": int(time.time()),
            "orgs": len(constitutions),
            "unified_thresholds": self._compute_unified_thresholds(constitutions),
            "unified_quorum": self._compute_unified_quorum(constitutions),
            "authority_hierarchy": self._build_authority_hierarchy(constitutions),
        }

        self.compiled_policy = compiled

        # Record in master ledger
        self.master_ledger.append({
            "type": "policy_compilation",
            "timestamp": compiled["compiled_at"],
            "orgs": compiled["orgs"],
        })

        return compiled

    def _fetch_org_constitution(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Fetch constitution from org. Placeholder for HTTP fetch."""
        # In production: fetch from org's repo_constitution.txt
        # For now, return minimal default
        return {
            "authority_classes": ["human_operator", "ai_entity", "automated_process"],
            "threshold_profiles": {"standard": {"observability_min": 0.6}},
        }

    def _compute_unified_thresholds(self, constitutions: List[Dict]) -> Dict[str, float]:
        """Compute most restrictive thresholds across all orgs."""
        unified = {}

        for c in constitutions:
            profiles = c.get("constitution", {}).get("threshold_profiles", {})
            for profile_name, thresholds in profiles.items():
                if profile_name not in unified:
                    unified[profile_name] = {}
                for key, value in thresholds.items():
                    if key.endswith("_min"):
                        # Take max of mins (most restrictive)
                        unified[profile_name][key] = max(
                            unified[profile_name].get(key, 0),
                            value,
                        )
                    elif key == "risk_max":
                        # Take min of maxs (most restrictive)
                        unified[profile_name][key] = min(
                            unified[profile_name].get(key, 1.0),
                            value,
                        )

        return unified

    def _compute_unified_quorum(self, constitutions: List[Dict]) -> Dict[str, Any]:
        """Compute unified quorum rules."""
        # All orgs must agree on: human+AI pair for policy changes
        return {
            "policy_change": {
                "required": ["human_operator", "ai_entity"],
                "min_count": 2,
                "pairing_rule": "paired",
            },
            "emergency_halt": {
                "required": ["human_operator", "ai_entity", "policy_engine"],
                "min_count": 2,
                "pairing_rule": "any_two_of_three",
            },
        }

    def _build_authority_hierarchy(self, constitutions: List[Dict]) -> List[str]:
        """Build authority hierarchy across orgs."""
        # Master compiler is top authority
        hierarchy = ["stegcge_compiler"]

        # Add org authorities
        for c in constitutions:
            org_id = c["org_id"]
            hierarchy.append(f"{org_id}_authority")

        return hierarchy

    async def check_org_health(self, org_id: str) -> OrgStatus:
        """Check health of a specific org."""
        status = self.orgs.get(org_id)
        if not status:
            return OrgStatus(
                org_id=org_id,
                cge_tier="unknown",
                health="unknown",
                last_receipt=None,
                policy_drift=False,
                needs_repair=True,
            )

        # In production: ping org's /health endpoint
        # Check receipt chain continuity
        # Check policy drift against compiled policy

        return status

    async def direct_repair(
        self,
        org_id: str,
        status: OrgStatus,
    ) -> Dict[str, Any]:
        """Direct repair for a failed org."""

        repair_plan = {
            "org_id": org_id,
            "status": status.health,
            "actions": [],
            "timestamp": int(time.time()),
        }

        if status.health == "failed":
            repair_plan["actions"].extend([
                "1. Verify CGE Light bootstrap integrity",
                "2. Check ledger continuity and receipt chain",
                "3. Re-apply compiled policy from master",
                "4. Verify entity registry consistency",
                "5. Re-establish StegDB ingestion",
            ])
        elif status.health == "degraded":
            repair_plan["actions"].extend([
                "1. Check provider adapter health",
                "2. Verify TV/TVC credential freshness",
                "3. Review admission threshold compliance",
            ])

        # Record repair directive in master ledger
        self.master_ledger.append({
            "type": "repair_directive",
            "org_id": org_id,
            "timestamp": repair_plan["timestamp"],
            "actions": len(repair_plan["actions"]),
        })

        return repair_plan

    async def backup_org_ledger(self, org_id: str) -> Dict[str, Any]:
        """Backup org ledger to master StegDB."""

        # In production: fetch org ledger, push to master StegDB
        return {
            "org_id": org_id,
            "backup_status": "scheduled",
            "timestamp": int(time.time()),
        }

    def get_master_status(self) -> Dict[str, Any]:
        """Get overall compiler status."""
        return {
            "version": "1.0.0",
            "registered_orgs": len(self.orgs),
            "healthy": sum(1 for o in self.orgs.values() if o.health == "healthy"),
            "degraded": sum(1 for o in self.orgs.values() if o.health == "degraded"),
            "failed": sum(1 for o in self.orgs.values() if o.health == "failed"),
            "compiled_policy_version": self.compiled_policy.get("version", "none"),
            "master_ledger_entries": len(self.master_ledger),
        }
