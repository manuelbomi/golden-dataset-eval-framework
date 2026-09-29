#!/usr/bin/env python
"""Seed a handful of demo documents (short, generic sales/support snippets --
no real customer or company data) via the running API, so a fresh
`docker compose up` has something in the annotation queue immediately.

Usage: python scripts/seed_demo.py [--base-url http://localhost:8000]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

DEMO_SNIPPETS = [
    "Honestly, the price feels a bit steep for what we're getting.",
    "This looks great -- when could we get started?",
    "I can guarantee you'll never see a problem like that again.",
    "What's included in the standard support tier?",
    "Let's schedule a follow-up call for next Tuesday at 2pm.",
    "I need to check with my manager before we move forward.",
    "Your competitor is offering a similar package for less.",
    "We'll send over the signed contract by Friday.",
    "Can you walk me through how the onboarding process works?",
    "So this basically never fails, no matter what?",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    with httpx.Client(base_url=args.base_url, timeout=10.0) as client:
        for text in DEMO_SNIPPETS:
            resp = client.post("/documents", json={"text": text})
            resp.raise_for_status()
        print(f"Seeded {len(DEMO_SNIPPETS)} demo documents against {args.base_url}")


if __name__ == "__main__":
    main()
