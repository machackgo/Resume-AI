"""Application package generator: resume and cover letter (DOCX), answers, outreach drafts.

Adapted from the private Resume AI control center (resume_ai/docs.py, generator 2.1.0):
  * the candidate header/education/roles/items come from a Profile, not module globals;
  * PDF rendering (LibreOffice or headless Chromium + a macOS PDFKit helper) is omitted, so the
    validator runs on text read back from the DOCX instead of text extracted from the PDF.

Resume bullets come ONLY from profile.items (by id), so a resume cannot contain an unsourced
bullet. Free text written per job (summary, cover-letter paragraphs) is validated after rendering.
Nothing in this module submits anything.
"""
import json
import os
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, Inches

from . import validate

GENERATOR_VERSION = "2.1.0-showcase"
FONT = "Arial"


def _para(doc, text="", bold=False, size=10, align=None, space_after=0, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    if align:
        p.alignment = align
    if text:
        r = p.add_run(text); r.bold = bold; r.italic = italic; r.font.size = Pt(size); r.font.name = FONT
    return p


def _bullet(doc, text, size=9.5):
    p = doc.add_paragraph()  # plain-text bullet (U+2022) so every ATS parser extracts it
    p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.left_indent = Inches(0.18); p.paragraph_format.first_line_indent = Inches(-0.13)
    r = p.add_run("• " + text); r.font.size = Pt(size); r.font.name = FONT
    return p


def _heading(doc, text):
    p = _para(doc, text.upper(), bold=True, size=10.5, space_after=1)
    p.paragraph_format.space_before = Pt(5)
    return p


def _setup(doc, top=0.45, side=0.55):
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Inches(top)
        s.left_margin = s.right_margin = Inches(side)
    st = doc.styles["Normal"]; st.font.name = FONT; st.font.size = Pt(10)


def _contact(doc, header):
    _para(doc, header["name"].upper(), bold=True, size=15, align=WD_ALIGN_PARAGRAPH.CENTER)
    _para(doc, " | ".join(header[k] for k in ("location", "phone", "email") if header.get(k)), size=9.5, align=WD_ALIGN_PARAGRAPH.CENTER)
    _para(doc, " | ".join(header[k] for k in ("github", "website") if header.get(k)), size=9.5,
          align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)


def build_resume(spec, profile, out_dir, base):
    doc = Document(); _setup(doc); _contact(doc, profile.header)
    _heading(doc, "Summary"); _para(doc, spec["summary"], size=9.5)
    _heading(doc, "Education")
    for e in profile.education:
        _para(doc, f"{e['school']}, {e['place']} | {e['degree']} | {e['dates']}", bold=True, size=9.5)
        detail = e.get("detail", "") + (f" | Coursework: {e['coursework']}" if e.get("coursework") and spec.get("coursework", True) else "")
        if detail:
            _para(doc, detail.strip(" |"), size=9.5)
    _heading(doc, "Technical Skills")
    for label, val in spec["skills"]:
        p = _para(doc, size=9.5); r = p.add_run(label + ": "); r.bold = True; r.font.size = Pt(9.5); r.font.name = FONT
        r2 = p.add_run(val); r2.font.size = Pt(9.5); r2.font.name = FONT
    for section, key in (("Experience", "experience"), ("Projects", "projects")):
        if not spec.get(key):
            continue
        _heading(doc, section)
        for role_key, ids in spec[key]:
            ro = profile.roles[role_key]
            _para(doc, f"{ro['title']} | {ro['org']}, {ro.get('place', '')} | {ro['dates']}".replace(", |", " |"), bold=True, size=9.5)
            for i in ids:
                _bullet(doc, profile.items[i]["text"])
    path = os.path.join(out_dir, base + "_Resume.docx")
    doc.save(path)
    return path


def build_letter(paragraphs, profile, out_dir, base, heading_line, salutation="Dear Hiring Team,"):
    doc = Document(); _setup(doc, top=0.8, side=0.9); _contact(doc, profile.header)
    _para(doc, heading_line, bold=True, size=10, space_after=8)
    _para(doc, salutation, size=10.5, space_after=8)
    for ptxt in paragraphs:
        _para(doc, ptxt, size=10.5, space_after=8)
    _para(doc, "Sincerely,", size=10.5)
    _para(doc, profile.header["name"], size=10.5)
    path = os.path.join(out_dir, base + "_CoverLetter.docx")
    doc.save(path)
    return path


def docx_text(path):
    """Read the rendered document back (what a parser would see) so validation runs on the output, not the spec."""
    return "\n".join(p.text for p in Document(path).paragraphs)


def job_text(job):
    return " ".join([job.get("title", ""), job.get("jd_summary", "") or "", " ".join(job.get("required", job.get("required_qualifications", []))),
                     " ".join(job.get("preferred", job.get("preferred_qualifications", []))), " ".join(job.get("key_tech", [])),
                     job.get("salary") or "", job.get("start_text") or "", job.get("timing_text") or ""])


def build_package(job, spec, profile, root, version=1):
    """Build every artefact for one job; returns (results, manifest). Never submits anything."""
    base = re.sub(r"[^A-Za-z0-9]+", "_", profile.header["name"]).strip("_") + "_" + spec["slug"]
    out_dir = os.path.join(root, job["job_id"]) if version == 1 else os.path.join(root, job["job_id"], f"v{version}")
    os.makedirs(out_dir, exist_ok=True)
    jt = job_text(job)
    results = {}
    rdocx = build_resume(spec, profile, out_dir, base)
    rtext = docx_text(rdocx)
    results["resume"] = {"docx": rdocx, "issues": validate.check_document(rtext, profile, jt, "resume"), "text": rtext}
    if spec.get("cover_letter"):
        cdocx = build_letter(spec["cover_letter"], profile, out_dir, base, spec["letter_heading"], spec.get("salutation", "Dear Hiring Team,"))
        ctext = docx_text(cdocx)
        results["cover_letter"] = {"docx": cdocx, "issues": validate.check_document(ctext, profile, jt, "cover"), "text": ctext}
    answers = "\n".join(f"Q: {q}\nA: {a}\n" for q, a in spec.get("answers", []))
    apath = os.path.join(out_dir, base + "_ApplicationAnswers.txt")
    with open(apath, "w", encoding="utf-8") as f:
        f.write(answers)
    results["answers"] = {"path": apath, "issues": validate.check_answers(spec.get("answers", []), profile, jt), "text": answers}
    outreach = spec.get("outreach", {})
    otext = "\n\n".join(f"[{k}]\n{v}" for k, v in outreach.items())
    opath = os.path.join(out_dir, base + "_Outreach.txt")
    with open(opath, "w", encoding="utf-8") as f:
        f.write(otext)
    results["outreach"] = {"path": opath, "issues": validate.check_document(otext, profile, jt, "cover")}
    manifest = {"job_id": job["job_id"], "version": version, "generator_version": GENERATOR_VERSION,
                "validator_version": validate.VALIDATOR_VERSION,
                "evidence_ids": [i for _, ids in spec["experience"] + spec.get("projects", []) for i in ids],
                "open_items": spec.get("open_items", []),
                "artifacts": {k: {kk: vv for kk, vv in v.items() if kk != "text"} for k, v in results.items()}}
    with open(os.path.join(out_dir, "PACKAGE.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    return results, manifest
