"""Phase 1 verification — run blog_writer and check persona compliance in output.

Calls the agent directly (no server) with a short prompt, saves output,
greps for banned phrases (should be zero), and confirms persona lexicon
shows up.
"""
import asyncio
import json
import re
import sys
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import Runner
from skills.content_skills.blog_writer import blog_writer

PROMPT = """Write a 500-word blog post for sourcy.ai targeting the keyword
'find suppliers in Vietnam'. Audience: a US-based DTC brand owner doing
$2-10M revenue who has been burned by Alibaba once already (problem-aware).
Pick ONE marketing principle from the library and follow its structure
exactly. State the chosen principle at the top of the metadata.
Keep it tight and on-brand. No fluff intro."""


async def main() -> int:
    print("→ Running blog_writer with persona-loaded prompt...\n")
    result = await Runner.run(blog_writer, PROMPT, max_turns=15)
    raw_output = str(result.final_output)

    # The agent saves the actual blog to /public/content/blogs/ — find the latest one.
    out_dir = Path("public/content/blogs")
    files = sorted(out_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print("⚠ No blog file was saved.")
        print("Agent chat output:", raw_output[:800])
        return 1
    latest = files[0]
    body = latest.read_text()
    print(f"✓ Blog saved: {latest}")
    print(f"  Length: {len(body)} chars\n")

    # Check banned phrases
    persona = json.loads(Path("personas/sourcy.json").read_text())
    banned = persona["banned_phrases"]
    found_banned = []
    body_lc = body.lower()
    for bp in banned:
        if re.search(rf"\b{re.escape(bp.lower())}\b", body_lc):
            found_banned.append(bp)

    # Check preferred lexicon
    preferred = persona["lexicon"]["preferred"]
    hit_preferred = [p for p in preferred if p.lower() in body_lc]

    # Check proof points
    proof_stats = [pp["stat"].split()[0] for pp in persona["proof_points"]]
    hit_proof = [s for s in proof_stats if s in body]

    print("─" * 60)
    print("Persona Compliance Check")
    print("─" * 60)
    print(f"Banned phrases found: {len(found_banned)}  {found_banned}")
    print(f"Preferred lexicon hits ({len(hit_preferred)}/{len(preferred)}): {hit_preferred}")
    print(f"Proof points used ({len(hit_proof)}/{len(proof_stats)}): {hit_proof}")
    print("─" * 60)

    # Surface the first 800 chars so user sees voice
    print("\n--- First 800 chars of blog ---\n")
    print(body[:800])
    print("\n--- Chat response from agent ---\n")
    print(raw_output[:400])

    return 0 if not found_banned else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
