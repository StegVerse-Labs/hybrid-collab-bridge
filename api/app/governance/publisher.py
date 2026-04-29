"""Publisher Integration — Paper + Social Media Pipeline.

Triggers on finalized, governed outputs:
- Paper submissions (arXiv, journals, conferences)
- Social media posts (Twitter/X, LinkedIn, Mastodon)
- Blog posts (Medium, Dev.to, StegVerse blog)
- Newsletter entries

Governed by: Publisher repo at github.com/GCAT-BCAT-Engine/Publisher
"""
from __future__ import annotations
import os
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import httpx

from .entity import EntityIdentity


@dataclass
class PublishableOutput:
    """A governed output ready for publication."""
    content: str
    title: str
    authors: List[str]
    receipt_id: str
    bcat: Dict[str, Any]
    gcat: Dict[str, Any]
    tags: List[str]
    format: str  # paper | social | blog | newsletter


class PublisherClient:
    """Client for GCAT-BCAT-Engine/Publisher integration."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.endpoint = endpoint or os.getenv("PUBLISHER_ENDPOINT", "")
        self.api_key = api_key or os.getenv("PUBLISHER_API_KEY", "")
        self.enabled = bool(self.endpoint)

    async def submit_paper(
        self,
        output: PublishableOutput,
        venue: str,  # arxiv, journal_name, conference_name
        category: str = "cs.AI",
    ) -> Dict[str, Any]:
        """Submit governed output as academic paper."""
        if not self.enabled:
            return {"status": "disabled", "reason": "No PUBLISHER_ENDPOINT configured"}

        payload = {
            "type": "paper_submission",
            "title": output.title,
            "abstract": output.content[:500],
            "authors": output.authors,
            "venue": venue,
            "category": category,
            "receipt_id": output.receipt_id,
            "bcat": output.bcat,
            "gcat": output.gcat,
            "tags": output.tags,
            "timestamp": int(time.time()),
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    f"{self.endpoint}/v1/submit/paper",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                )
                r.raise_for_status()
                return r.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def post_social(
        self,
        output: PublishableOutput,
        platform: str,  # twitter, linkedin, mastodon
        thread: bool = False,
    ) -> Dict[str, Any]:
        """Post governed output to social media."""
        if not self.enabled:
            return {"status": "disabled"}

        # Truncate for social if needed
        content = output.content
        if len(content) > 280 and platform == "twitter":
            content = content[:277] + "..."

        payload = {
            "type": "social_post",
            "platform": platform,
            "content": content,
            "title": output.title,
            "receipt_id": output.receipt_id,
            "tags": output.tags,
            "thread": thread,
            "timestamp": int(time.time()),
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    f"{self.endpoint}/v1/submit/social",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                )
                r.raise_for_status()
                return r.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def publish_blog(
        self,
        output: PublishableOutput,
        platform: str = "stegverse",
    ) -> Dict[str, Any]:
        """Publish governed output as blog post."""
        if not self.enabled:
            return {"status": "disabled"}

        payload = {
            "type": "blog_post",
            "platform": platform,
            "title": output.title,
            "content": output.content,
            "authors": output.authors,
            "receipt_id": output.receipt_id,
            "tags": output.tags,
            "timestamp": int(time.time()),
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    f"{self.endpoint}/v1/submit/blog",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                )
                r.raise_for_status()
                return r.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def queue_newsletter(
        self,
        outputs: List[PublishableOutput],
        issue_title: str,
    ) -> Dict[str, Any]:
        """Queue multiple outputs for newsletter."""
        if not self.enabled:
            return {"status": "disabled"}

        payload = {
            "type": "newsletter",
            "issue_title": issue_title,
            "items": [
                {
                    "title": o.title,
                    "summary": o.content[:200],
                    "receipt_id": o.receipt_id,
                    "tags": o.tags,
                }
                for o in outputs
            ],
            "timestamp": int(time.time()),
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    f"{self.endpoint}/v1/submit/newsletter",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                )
                r.raise_for_status()
                return r.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
