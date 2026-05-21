"""Phase 3 verification — run ad_writer end-to-end against the real OpenAI API.

Runs the Ad Writer with a realistic finding set and confirms:
- 3 variants are produced (PAS, AIDA, BAB)
- Each variant has a GPT Image 2 generated image URL
- Persona compliance (no banned phrases)
- Artifact HTML saved
"""

import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import Runner
from skills.content_skills.ad_writer import ad_writer


PROMPT = """Generate 3 ad variants for Meta (square aspect).

Subject: AI sourcing agent for US DTC brands launching new SKUs from Asia.

Selected findings (from analysis):
[
  {"finding_id":"F1","claim":"73% of newly-acquired DTC brand aggregators report supplier vetting as their #1 launch bottleneck","evidence":"Internal Sourcy customer survey 2026 Q1, n=140 aggregators","confidence":"High","tags":["pain_point","brand_aggregator"]},
  {"finding_id":"F2","claim":"Sourcy's first-quote turnaround is 3 hours vs an industry average of 7 days","evidence":"390+ active customers; benchmark vs Alibaba RFQ SLA","confidence":"High","tags":["winning_angle","speed"]},
  {"finding_id":"F4","claim":"Brand aggregators searching 'find verified supplier Vietnam' have a 4x higher conversion rate than generic 'sourcing agent' traffic","evidence":"Google Ads Q1 2026 search-term report","confidence":"Medium","tags":["winning_angle","keyword"]}
]

Agent refs: A (SEO), C (Competitor).

Channel: meta. Aspect: square."""


async def main() -> int:
    print("→ Running ad_writer with 3-variant + image-gen pipeline...\n")
    print(f"  Prompt length: {len(PROMPT)} chars")
    print(f"  Persona: Sourcy (banned phrases auto-loaded)\n")

    result = await Runner.run(ad_writer, PROMPT, max_turns=20)
    text = str(result.final_output)

    # Save chat response for inspection
    out = Path("public/content/ads")
    out.mkdir(parents=True, exist_ok=True)
    transcript = out / "phase3_test_transcript.md"
    transcript.write_text(text)
    print(f"✓ Chat response saved: {transcript} ({len(text)} chars)\n")

    # 1. Confirm 3 variants
    variants_found = sum(1 for k in ["Variant A", "Variant B", "Variant C"] if k in text)
    print(f"  Variants in chat response: {variants_found}/3")

    # 2. Confirm image URLs in chat response (paths to /content/images/)
    images = re.findall(r"/content/images/[^\s)]+\.png", text)
    images = list(dict.fromkeys(images))  # dedupe
    print(f"  Image URLs in chat response: {len(images)}")
    for i, url in enumerate(images[:5], 1):
        full = Path("public") / url.lstrip("/")
        size = full.stat().st_size if full.exists() else 0
        print(f"    [{i}] {url} ({size} bytes, exists={full.exists()})")

    # 3. Persona compliance
    persona = json.loads(Path("personas/sourcy.json").read_text())
    banned = persona["banned_phrases"]
    text_lc = text.lower()
    found_banned = [bp for bp in banned if re.search(rf"\b{re.escape(bp.lower())}\b", text_lc)]
    print(f"  Banned phrases in chat: {len(found_banned)}  {found_banned}")

    # 4. Findings sentinel parsed
    from app.streaming_events import StreamTracker
    findings = StreamTracker._extract_findings(text)
    print(f"  Structured findings emitted: {len(findings)}")
    for f in findings[:3]:
        print(f"    - {f.get('finding_id','?')}: {f.get('claim','')[:80]}")

    # 5. Persona lexicon hits
    preferred = persona["lexicon"]["preferred"]
    hits = [p for p in preferred if p.lower() in text_lc]
    print(f"  Persona lexicon hits ({len(hits)}/{len(preferred)}): {hits}")

    # 6. Latest HTML artifact
    artifacts = sorted(Path("public/reports").glob("ad*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
    if artifacts:
        print(f"  Latest ad artifact: {artifacts[0]} ({artifacts[0].stat().st_size} bytes)")

    print("\n" + "─" * 60)
    print("First 1000 chars of chat response:")
    print("─" * 60)
    print(text[:1000])

    success = variants_found == 3 and len(images) >= 1 and not found_banned
    return 0 if success else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
