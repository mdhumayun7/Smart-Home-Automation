# Declarations — author sign-off sheet

Required by the Journal of Systems Architecture Guide for Authors, read from Elsevier's own
page on **7 November 2026**.

**Nothing on this sheet is a declaration made on the author's behalf.** Each item is a *draft*
in the publisher's required wording, prepared so the author has only to confirm or correct it.
Three items need an explicit decision before submission and are marked **CONFIRM**.

---

## 1. Declaration of competing interest — **CONFIRM**

**What Elsevier requires.** All authors must disclose any financial or personal relationships
that could inappropriately influence or bias the work. The Guide lists the categories
explicitly: employment, consultancies, stock ownership, honoraria, paid expert testimony,
patent applications or registrations, grants or other funding, and affiliation with the journal
as an editor or advisory board member.

Two separate obligations:

1. The **declarations tool in the submission system** "should always be completed". If there is
   nothing to declare, select *"I have nothing to declare."*
2. The resulting **Word document** must be uploaded at the "attach/upload files" step, saved as
   `.doc` or `.docx`. **Author signatures are not required.**

**Draft text, now in the manuscript** as `\section*{Declaration of competing interest}`:

> The author declares that he has no known competing financial interests or personal
> relationships that could have appeared to influence the work reported in this paper.

**CONFIRM before submission.** Check each category against your own circumstances:

- [ ] Employment — any paid position with an organisation with an interest in this work?
- [ ] Consultancies
- [ ] Stock ownership
- [ ] Honoraria
- [ ] Paid expert testimony
- [ ] Patent applications or registrations touching this work
- [ ] Grants or other funding (see §2)
- [ ] Any editorial or advisory-board role at JSA
- [ ] **Your Teaching Assistant position at SVNIT** — ordinary academic employment at the
      institution where the work was done. This is normally not a competing interest and is
      covered by the affiliation on the title page, but it is your call, not mine.

**Signed off by:** ______________________  **Date:** ____________

---

## 2. Funding — **CONFIRM**

**What Elsevier requires.** Authors must disclose any funding source that supported the
research or the preparation of the article, and must state the sponsor's role, if any, in study
design, data collection, analysis and interpretation, writing, and the decision to submit. **If
funding sources had no such involvement, that must be stated.** The Guide gives the standard
form:

> Funding: This work was supported by the National Institutes of Health [grant numbers xxxx,
> yyyy]; …

**Draft text, now in the manuscript** as `\section*{Funding}`, using Elsevier's standard
no-funding sentence:

> This research did not receive any specific grant from funding agencies in the public,
> commercial, or not-for-profit sectors.

This replaces the previous wording ("This research received no external funding"), which said
the same thing but not in the publisher's standard form.

**CONFIRM before submission.**

- [ ] No grant, scholarship, fellowship or award supported this work?
- [ ] No departmental or institutional block grant was drawn on?
- [ ] Your **Teaching Assistantship** is a stipend for teaching, not a research grant for this
      work — correct?
- [ ] This work is **not** part of, or funded by, the MeitY-sponsored drone-swarm project or any
      other sponsored project?

**If any box cannot be ticked, the sentence above is wrong and must be replaced** with the
funder's name and grant number in Elsevier's format, plus a statement of the sponsor's role.

**Signed off by:** ______________________  **Date:** ____________

---

## 3. CRediT authorship contribution statement — **CONFIRM**

**What Elsevier requires.** Corresponding authors must acknowledge contributions using CRediT
roles. The taxonomy on the Guide page: Conceptualization, Data curation, Formal analysis,
Funding acquisition, Investigation, Methodology, Project administration, Resources, Software,
Supervision, Validation, Visualization, Writing – original draft, Writing – review & editing.

**Draft text, now in the manuscript:**

> **MD Humayun:** Conceptualization, Methodology, Software, Validation, Formal analysis,
> Investigation, Data curation, Writing – original draft, Writing – review & editing,
> Visualization, Project administration.

Roles deliberately **not** claimed, and why:

| Role | Why omitted |
|---|---|
| Funding acquisition | no funding was acquired (§2) |
| Resources | no special resources were provided |
| Supervision | **see the question below** |

**CONFIRM before submission.**

- [ ] Is MD Humayun the **sole author**, or should Dr. M. A. Zaveri be listed as a co-author
      with the *Supervision* role? This is a question for the supervisor, not for the author to
      decide alone, and it changes the title page, the submission system's author list and this
      statement.
- [ ] If sole-authored, is the supervisor to be thanked in an **Acknowledgements** section
      instead? The Guide requires acknowledgements to be a separate section immediately before
      the reference list, and **not** on the title page or in a footnote. There is currently no
      Acknowledgements section; if one is wanted, say whom to name.

**Signed off by:** ______________________  **Date:** ____________

---

## 4. Declaration of generative AI use — prepared, no confirmation needed beyond a read

**What Elsevier requires.** A statement at the end of the manuscript, in a **new section before
the reference list**, declaring the use of generative AI in manuscript preparation. AI tools
must not be listed as authors. Authors remain accountable for accuracy, for checking sources
(the Guide warns AI-generated references "can be incorrect or fabricated"), and for ensuring
the work is their own.

**In the manuscript**, retitled to match the Guide's example exactly:
`Declaration of generative AI and AI-assisted technologies in the manuscript preparation
process` — previously it read "in the writing process".

The existing text already states the tool's use, the author's review, full responsibility, and
that every reference was checked against its publisher record. **Read it once and confirm it
describes what actually happened.**

- [ ] Read and accurate.

---

## 5. Data availability — prepared

Elsevier requires a data-availability statement at submission, and it appears with the
published article. The manuscript carries one as its own section, describing deterministic
regeneration from fixed seeds, which records are committed, which are regenerated, and that the
broker testbed's throwaway keys are deliberately not committed.

- [ ] Confirm the repository will be public at the submission URL given in the paper.

---

## 6. Ethics — prepared

No human or animal subjects; no third-party system was attacked or tested; no attack tooling is
published. Nothing further is required for this journal.

---

## What to upload, and where

| File | Where it goes |
|---|---|
| `paper/manuscript.pdf` | main manuscript |
| `paper/manuscript.tex` | LaTeX source (bibliography is embedded; there is no separate `.bib`) |
| `paper/submission/highlights.txt` | **as a separate editable file with "highlights" in the filename**, per the Guide |
| `paper/submission/declaration-of-competing-interest.md` | convert to `.doc`/`.docx` and upload at the "attach/upload files" step |
| Figure files | `FINAL_SUBMISSION_PACKAGE/figures/COMPLETE_FIGURE_COLLECTION.zip` — use the **PDF** versions; EPS or PDF is what the Guide asks for vector drawings |

The declarations tool inside the submission system must also be completed — that is separate
from the manuscript sections and from the uploaded Word document.
