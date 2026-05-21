"""Multi-prompt test sweep across all generation skills.

Runs blog_writer, landing_page_writer, ad_writer, case_study_writer in sequence
with realistic prompts, captures outputs, and checks persona compliance for each.
"""

import asyncio
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import Runner

# Load persona once for compliance checks
PERSONA = json.loads(Path("personas/sourcy.json").read_text())
BANNED = PERSONA["banned_phrases"]
PREFERRED = PERSONA["lexicon"]["preferred"]
PROOF_NUMBERS = [pp["stat"].split()[0] for pp in PERSONA["proof_points"]]


def check_compliance(label: str, body: str) -> dict:
    body_lc = body.lower()
    banned_hits = [bp for bp in BANNED if re.search(rf"\b{re.escape(bp.lower())}\b", body_lc)]
    pref_hits = [p for p in PREFERRED if p.lower() in body_lc]
    proof_hits = [s for s in PROOF_NUMBERS if s in body]
    return {
        "label": label,
        "len": len(body),
        "banned": banned_hits,
        "preferred_hits": pref_hits,
        "proof_hits": proof_hits,
    }


def print_compliance(c: dict, threshold_pref: int = 1, threshold_proof: int = 1):
    ok_banned = not c["banned"]
    ok_pref = len(c["preferred_hits"]) >= threshold_pref
    ok_proof = len(c["proof_hits"]) >= threshold_proof
    mark = lambda ok: "✓" if ok else "✗"
    print(f"  Output length: {c['len']:,} chars")
    print(f"  {mark(ok_banned)} Banned phrases: {len(c['banned'])} hits — {c['banned'] or '(none)'}")
    print(f"  {mark(ok_pref)} Preferred lexicon: {len(c['preferred_hits'])}/{len(PREFERRED)} — {c['preferred_hits']}")
    print(f"  {mark(ok_proof)} Proof points: {len(c['proof_hits'])}/{len(PROOF_NUMBERS)} — {c['proof_hits']}")
    return ok_banned and ok_pref


def latest_file(directory: str, pattern: str) -> Path | None:
    p = Path(directory)
    if not p.exists():
        return None
    files = sorted(p.glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True)
    return files[0] if files else None


async def test_blog():
    from skills.content_skills.blog_writer import blog_writer
    print("\n" + "═" * 64)
    print("  TEST 1 · BLOG WRITER")
    print("═" * 64)
    prompt = """Write a 500-word blog post for sourcy.ai targeting
'private label products from Indonesia'. Audience: a US DTC brand owner
($5–15M revenue) considering diversifying off China. Pick one marketing
principle from the library and state which one you chose. Tight, on-brand."""
    print(f"  Prompt: 'Private label products from Indonesia' (DTC brand owner)")
    t0 = time.time()
    result = await Runner.run(blog_writer, prompt, max_turns=15)
    elapsed = time.time() - t0
    print(f"  ⏱  {elapsed:.1f}s")
    saved = latest_file("public/content/blogs", "*.md")
    if saved:
        body = saved.read_text()
        print(f"  📄 Saved: {saved.name}")
        c = check_compliance("blog", body)
        return print_compliance(c)
    print("  ⚠ No file saved")
    return False


async def test_landing_page():
    from skills.content_skills.landing_page_writer import landing_page_writer
    print("\n" + "═" * 64)
    print("  TEST 2 · LANDING PAGE WRITER")
    print("═" * 64)
    prompt = """Write a landing page for sourcy.ai/private-label, targeting
brand aggregators with $5M+ revenue across multiple DTC brands.
Use the Hormozi value-stack principle. State the chosen principle and
which LP blocks (from the design system's landing_page_blocks list)
you used in metadata."""
    print(f"  Prompt: '/private-label' LP for brand aggregators (Hormozi)")
    t0 = time.time()
    result = await Runner.run(landing_page_writer, prompt, max_turns=15)
    elapsed = time.time() - t0
    print(f"  ⏱  {elapsed:.1f}s")
    saved = latest_file("public/content/landing-pages", "*.md")
    if saved:
        body = saved.read_text()
        print(f"  📄 Saved: {saved.name}")
        c = check_compliance("landing_page", body)
        ok = print_compliance(c)
        principle_named = bool(re.search(r"hormozi|value.?stack", body, re.I))
        print(f"  {'✓' if principle_named else '✗'} Hormozi principle explicitly named")
        return ok and principle_named
    print("  ⚠ No file saved")
    return False


async def test_ad():
    from skills.content_skills.ad_writer import ad_writer
    print("\n" + "═" * 64)
    print("  TEST 3 · AD WRITER (3 variants + 3 images)")
    print("═" * 64)
    prompt = """Generate 3 ad variants for Meta (square).

Subject: AI sourcing agent for new DTC brands launching their first product from Asia.

Selected findings:
[
  {"finding_id":"F1","claim":"60% of first-time DTC importers get burned by an unverified Alibaba supplier","evidence":"Internal Sourcy survey 2026 Q1, n=140","confidence":"High","tags":["pain_point","first_time_importer"]},
  {"finding_id":"F2","claim":"Sourcy returns first real supplier quote in 3 hours vs industry 7 days","evidence":"390+ customers; benchmark","confidence":"High","tags":["winning_angle","speed"]}
]
Channel: meta."""
    print(f"  Prompt: 3 Meta ad variants (PAS/AIDA/BAB) with images")
    t0 = time.time()
    result = await Runner.run(ad_writer, prompt, max_turns=20)
    elapsed = time.time() - t0
    text = str(result.final_output)
    print(f"  ⏱  {elapsed:.1f}s")
    saved = latest_file("public/reports", "ad_*.html")
    if saved:
        body = saved.read_text()
        print(f"  📄 Saved: {saved.name}")
        images = re.findall(r"/content/images/[^\"\s]+\.png", body)
        print(f"  🖼  Images embedded: {len(set(images))}")
        c = check_compliance("ad", body)
        ok = print_compliance(c, threshold_pref=1, threshold_proof=0)
        variants = sum(1 for k in ["Variant A", "Variant B", "Variant C"] if k in body)
        principles = sum(1 for k in ["PAS", "AIDA", "BAB"] if k in body)
        print(f"  {'✓' if variants == 3 else '✗'} 3 variants: {variants}/3")
        print(f"  {'✓' if principles == 3 else '✗'} 3 principles (PAS/AIDA/BAB): {principles}/3")
        return ok and variants == 3 and principles == 3 and len(set(images)) >= 3
    print("  ⚠ No artifact saved")
    return False


async def test_case_study():
    from skills.content_skills.case_study_writer import case_study_writer
    print("\n" + "═" * 64)
    print("  TEST 4 · CASE STUDY WRITER")
    print("═" * 64)
    prompt = """Write a case study using Before/What we did/After.

Customer: Confidential beauty brand (anonymous), DTC, US-based.
Industry: beauty / personal care.

Selected findings:
[
  {"finding_id":"F1","claim":"Customer cut sourcing cycle from 28 days to 4 days after switching to Sourcy","evidence":"Anecdotal — verify with customer","confidence":"Medium","tags":["customer_outcome","speed"]},
  {"finding_id":"F2","claim":"Customer launched 3 new SKUs in Q2 vs 1 in Q1","evidence":"Customer share","confidence":"Medium","tags":["customer_outcome","scale"]}
]

Generate one landscape hero image."""
    print(f"  Prompt: Beauty brand case study, 28→4 day sourcing cycle")
    t0 = time.time()
    result = await Runner.run(case_study_writer, prompt, max_turns=15)
    elapsed = time.time() - t0
    text = str(result.final_output)
    print(f"  ⏱  {elapsed:.1f}s")
    saved = latest_file("public/reports", "case-study_*.html")
    if saved is None:
        # case_study_writer might still save as brief if artifact_type fallback
        saved = latest_file("public/reports", "*.html")
    if saved:
        body = saved.read_text()
        print(f"  📄 Saved: {saved.name}")
        images = re.findall(r"/content/images/[^\"\s]+\.png", body)
        print(f"  🖼  Images embedded: {len(set(images))}")
        c = check_compliance("case_study", body)
        ok = print_compliance(c, threshold_pref=1, threshold_proof=0)
        has_before = "Before" in body or "before" in body.lower()
        has_after = "After" in body or "after" in body.lower()
        print(f"  {'✓' if has_before and has_after else '✗'} Has Before / After structure")
        return ok and has_before and has_after
    print("  ⚠ No artifact saved")
    return False


async def main() -> int:
    print("┌" + "─" * 62 + "┐")
    print("│  PHASE 3 MULTI-PROMPT TEST SUITE                              │")
    print("│  Blog · Landing page · Ad (3 variants + images) · Case study  │")
    print("└" + "─" * 62 + "┘")

    results = {}
    results["blog"] = await test_blog()
    results["landing_page"] = await test_landing_page()
    results["ad"] = await test_ad()
    results["case_study"] = await test_case_study()

    print("\n" + "═" * 64)
    print("  SUMMARY")
    print("═" * 64)
    for k, ok in results.items():
        print(f"  {'✓ PASS' if ok else '✗ FAIL'}  {k}")

    all_ok = all(results.values())
    print(f"\n  {'🎉 ALL PASSED' if all_ok else '⚠ SOME FAILED'}")
    return 0 if all_ok else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
