# Similarity screening checklist

Phase 5 of the finalization task. Prepared 7 November 2026.

**No similarity report exists, and no similarity percentage is claimed.** This document
records what was reviewed by hand here, what only the institution can do, and one defect the
review found and fixed.

---

## 1. Tool availability

| Tool | Available here | Note |
|---|---|---|
| iThenticate | **no** | Elsevier uses it in Crossref Similarity Check; access is through the publisher or the institution |
| Turnitin | **no** | SVNIT licenses this centrally; the library or the supervisor's account is the route |
| Any other licensed checker | **no** | — |

This environment has no licensed similarity tool and none can be installed. Running an
unlicensed or free web checker would be worse than running none: it would upload an unpublished
manuscript to a third party, and several such services retain what they are given.

**Action required: obtain the report through SVNIT.** §6 is the checklist for that.

---

## 2. What was reviewed by hand, and what was found

### 2.1 Direct quotations — clean

Every quoted string in the manuscript body was extracted and read. There are nine, and
**none quotes an external source**:

| Quoted string | What it is |
|---|---|
| "Operator admitted", "Locked out", "Delivered", "defeated by replay" | the author's own table column and metric names |
| "survives every case" | the author's own earlier wording, quoted in order to correct it |
| "refused by policy" | a protocol concept — MQTT 3.1.1 has no such return code |
| "TLS enabled and a broker login configured" | the author's paraphrase of the guard's own logic |
| "exactly as the firmware does" | the author's own text |

The remaining quoted strings are paper titles inside the bibliography, which is correct form.

**No passage of external text appears verbatim in the manuscript.** For a similarity check
this is the most important single fact: there is no copied prose to find.

### 2.2 Attribution of external experimental results — correct

The manuscript reports one set of numbers it did not produce: Behnke et al.'s cycle-loss
measurements. The attribution is explicit:

> "Behnke et al.~\cite{behnke2020} measured a periodic critical task's lateness on an ESP32
> under IP packet load … and found measurable degradation: the task lost 2.15–3.8 % of its
> cycles for packets addressed to a listened port and 3.17–6.67 % for an unused port …
> **Their** conclusion was that …"

Named, cited, and the findings marked as theirs in both the attributing verb and the
possessive. These are the only external numeric results in the paper, and they appear nowhere
in the results sections, where every figure is the author's own.

### 2.3 Overlap with the public repository — measured, and low

This matters practically. **iThenticate and Turnitin index GitHub**, and this repository is
public, so the author's own work will be matched against itself.

Measured directly: of 453 manuscript sentences of twelve words or more, **3 (0.7 %) appear
verbatim in a committed Markdown file**. All three run the other way — the audit documents
quote the manuscript, not the reverse:

| Doc | Sentence |
|---|---|
| `docs/CONSISTENCY_AUDIT.md` | "we therefore make no claim that the pattern is widespread …" |
| `docs/SECURITY_ANALYSIS.md` | "TLS secures a hop; it does not convey end-to-end provenance across a relay." |
| `docs/TITLE_ASSESSMENT.md` | "each can be falsified by a method that costs far less than the system it checks." |

**0.7 % is negligible.** But the raw percentage a tool reports will be higher than this,
because it also matches tables, figure captions, numbers, the README's description of the
work, and code identifiers. Expect a non-trivial self-match against
`github.com/mdhumayun7/Smart-Home-Automation` and be ready to explain it: the repository is
the artefact accompanying the paper, authored by the same person, and self-matches are
excluded from the similarity figure that matters. Most reports let you filter a source;
otherwise state it in the cover letter.

### 2.4 Paraphrased related work — reviewed

The related-work and introduction sections paraphrase rather than quote throughout, and every
paraphrase carries its citation on the same sentence. 47 `\cite` commands across 22 sources.
Spot-reading the Behnke paragraphs, the mixed-criticality paragraph and the MQTT-security
paragraph found no sentence that follows a source's structure closely enough to read as
close paraphrase.

### 2.5 Citation completeness — clean

| Check | Result |
|---|---|
| Bibliography entries | 22 |
| Entries cited in the text | 22 |
| **Uncited entries** | **0** |
| **Undefined citations** | **0** |
| LaTeX warnings on three passes | 0 |

### 2.6 Reference accuracy — one gap

17 of 22 entries carry a DOI, arXiv identifier or URL. **Five do not**, and should be
completed before submission:

| Key | Note |
|---|---|
| `lamport2002` | the TLA+ book; a pre-DOI monograph, so an ISBN is the right identifier |
| `mcreview2026` | add DOI |
| `espwn2023` | add DOI or a stable URL |
| `mqtttls2026` | add DOI |
| `zeghida2024` | add DOI |

Each entry's bibliographic details should also be checked against the publisher record — this
review confirmed the entries are well formed and consistently styled, not that every volume,
page and year is correct against the source.

### 2.7 Unsupported claims — one found and fixed

The manuscript was scanned for novelty words, absolutes, generality claims and
measured-timing language. Nearly every hit was benign and several were disclaimers
("Neither method we used is novel"; "no claim that the pattern is widespread").

**One genuine defect:**

> "Credential separation, not ACL syntax, carries the protection, and shared credentials are
> **common practice in deployed IoT fleets**."

That is an empirical claim about the world, it carried no citation, and no source in the
bibliography establishes it. Inventing a citation was not an option, so the claim was removed
and replaced with what the paper can actually support:

> "Credential separation, not ACL syntax, carries the protection. We include this arm because
> a single shared credential is the configuration an operator reaches for when per-device
> provisioning is inconvenient; we have no deployment data on how often that happens, and we
> make no claim about its prevalence."

No other unsupported claim about the world was found. The paper is otherwise disciplined
about this: it states no prevalence from the corpus, no new vulnerability, and no measured
timing.

---

## 3. What a similarity tool will probably flag, and why each is fine

Set expectations before reading the report, so a high headline number does not cause a panic.

| Likely match | Why it is not misconduct |
|---|---|
| The author's own public GitHub repository | Same author; the artefact accompanying the paper. Exclude as a self-match or declare it. |
| Technical identifiers: `AUTH_COMMANDS`, `ALLOW_REMOTE_DISARM`, `xQueueReceive`, `HMAC-SHA256`, `Mann–Whitney U`, `Wilson score` | Terminology cannot and must not be reworded to lower a score. |
| Standard method sentences on Mann–Whitney *U*, Wilson intervals, Fisher exact | Statistical boilerplate matches every paper that uses the same tests. |
| Bibliography | Reference lists always match. Most tools exclude them; if not, exclude manually. |
| Quoted paper titles | Correctly quoted and cited. |
| ESP32 / FreeRTOS API names and pin numbers | Platform vocabulary. |

**Do not rewrite legitimate technical terminology to reduce a similarity score.** It makes the
paper worse and the reviewers notice.

---

## 4. What would be a real problem

If the report shows any of the following, act before submitting:

- a contiguous passage of 25+ words matching a source that is not quoted and cited;
- a match against a paper **not** in the bibliography;
- a match in the Results or Discussion sections, where every sentence should be the author's
  own account of the author's own data;
- a match against another author's figure caption or table;
- a match against a paper the author has read but not cited.

None of these is expected given §2, but the report is the check, not this document.

---

## 5. Text recycling and prior dissemination — declare these

Elsevier asks about prior publication. The honest position:

| Item | Status | What to declare |
|---|---|---|
| Public GitHub repository with full artefact and analysis documents | public since before submission | Declare it as the accompanying artefact. It is not a prior publication, but it is public and will be matched. |
| `paper/paper.tex`, a short letters-format version | in the repository, **not submitted anywhere** | No action, but do not submit both. |
| `docs/` analysis documents | public, not peer-reviewed, not preprints | Declare if the form asks about prior dissemination. |
| Preprint on arXiv or similar | **none** | — |
| Prior conference version | **none** | — |
| Thesis chapter | — | **Confirm with the supervisor** whether any of this work appears, or will appear, in the M.Tech dissertation. If it does, most publishers permit it with a declaration, but it must be declared. |

---

## 6. Checklist for obtaining the institutional report

For the author. Items 1–4 are prerequisites; 5–9 are the run and its handling.

- [ ] **1.** Confirm with the supervisor which tool SVNIT licenses (Turnitin or iThenticate) and who can submit on the author's behalf.
- [ ] **2.** Add the missing DOIs (§2.6) before submitting the file, so the bibliography is final.
- [ ] **3.** Export the manuscript as a single PDF — `paper/manuscript.pdf`, 31 pages. Do not submit the `.tex`; markup inflates the score.
- [ ] **4.** Confirm the submission does **not** add the manuscript to the tool's permanent repository, or a later publisher check will match it against itself. For Turnitin this is the "no repository" / "do not store" submission option.
- [ ] **5.** Run the check.
- [ ] **6.** In the report settings, exclude: the bibliography, quoted material, and matches under about 10 words.
- [ ] **7.** Separately identify and exclude the self-match against `github.com/mdhumayun7/Smart-Home-Automation`, recording the figure before and after exclusion.
- [ ] **8.** Read every match above 1 % individually. The percentage is not the finding; the matched passages are.
- [ ] **9.** Keep the PDF of the report with the submission package, and record the date, the tool and the version.

**Record the outcome here when it exists:**

```
Tool:                     ____________________
Date run:                 ____________________
Overall similarity:       ______ %
After excluding self-match and bibliography: ______ %
Highest single source:    ____________________  ______ %
Matches above 1 % reviewed individually:  yes / no
Action taken:             ____________________
Supervisor sign-off:      ____________________
```

---

## 7. Status

| | |
|---|---|
| Manual review of quotations, attribution, citations, references and claims | **complete** |
| Defects found | **1** (unsupported prevalence claim), **fixed** |
| Measured self-overlap with the public repository | **0.7 %** of manuscript sentences |
| Missing DOIs | **5**, listed, outstanding |
| Institutional similarity report | **NOT OBTAINED — blocking** |
| Similarity percentage | **not claimed, and must not be claimed until a report exists** |

**This phase is not complete and cannot be completed here.** The manuscript is prepared for
screening; the screening itself requires institutional access.
