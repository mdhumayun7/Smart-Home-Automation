# Journal selection and author guidelines

> **Updated 7 November 2026, second pass.** The Guide for Authors has since been retrieved in
> full through a real browser and every formatting requirement below is now **verified** from
> Elsevier's own page. Indexing is also verified. The quartile remains unverified: SCImago
> serves a Cloudflare challenge (HTTP 403), which was not circumvented. See §2a and §4a, which
> supersede the corresponding rows above them where they disagree.

Phase 4 of the finalization task. Checked 7 November 2026.

Every claim below is marked **verified** (read from the publisher's own page during this
check) or **unverified** (could not be read, or comes from a third party). No quartile is
asserted without evidence, and no bot protection or CAPTCHA was circumvented.

---

## 1. What could and could not be read

| Source | Outcome |
|---|---|
| Elsevier journal page for JSA (shop.elsevier.com) | **read** — aims and scope, ISSN |
| ScienceDirect JSA journal page | **read** — open-access status, APC, a scope line on case studies |
| ScienceDirect JSA "Insights" metrics page | **read** — CiteScore, Impact Factor, review timings |
| ScienceDirect **Guide for Authors** | **not retrievable.** Two attempts returned a client error from the site. Not circumvented. |
| SCImago (quartile) | **not retrievable.** Returned a client error. Not circumvented. |
| Scopus / JCR (quartile, indexing) | **not attempted** — both require institutional authentication the author has and this environment does not |
| ACM TECS official site | **read**, but it carries no formal scope statement |
| Springer EMSE aims and scope | **read** |

**Consequence: the detailed formatting requirements cannot be stated here.** Section 4 lists
exactly what must be looked up, so the author can do it in one sitting with institutional
access.

---

## 2. Journal of Systems Architecture — what is verified

| Item | Value | Status |
|---|---|---|
| Publisher | Elsevier | verified |
| ISSN | 1383-7621 | verified |
| CiteScore | **9.1** | verified, from Elsevier's own Insights page |
| Impact Factor | **5.3** | verified, same page |
| Year these metrics refer to | **not stated on the page** | **unverified** |
| Time to first decision | 1 day | verified |
| Review time (submission to decision after review) | 43 days | verified |
| Submission to acceptance | 123 days | verified |
| Acceptance to online publication | 11 days | verified |
| Acceptance rate | not published | unverified |
| Open access supported | yes | verified |
| **APC (open access route)** | **USD 2,260 excluding taxes** | verified |
| Subscription route | "No publication fee charged to authors" | verified |
| **Quartile** | — | **UNVERIFIED. No quartile is claimed.** |

### On the quartile

Earlier documents in this repository assumed Q2. **That assumption should not be carried into
the submission.** SCImago could not be read during this check, and Scopus and JCR need
institutional authentication. What can be said is narrower and still useful: CiteScore 9.1 and
IF 5.3 are, in computer-architecture and embedded-systems categories, figures more often
associated with Q1 than Q2. **That would raise the bar, not lower it**, and it is a reason to
check rather than to relax.

The author can settle this in minutes through the institutional library: open
`scimagojr.com` in an ordinary browser, or check Scopus Sources or JCR. Record the year
alongside the quartile, because last year's ranking is not this year's.

### Scope fit — verified text

Elsevier's own page says the journal covers:

> "all design and architectural aspects related to embedded systems and software", from
> microarchitecture through system software to application-specific architecture, including
> real-time systems, operating systems, programming languages and design automation, with
> hardware/software co-design emphasising software.

And, from the ScienceDirect journal page, a line that applies directly to this manuscript:

> "Case studies are welcome but must contribute more than just a design for a particular piece
> of software."

**This is the single most important sentence for this submission**, and it is also the
manuscript's main risk at this venue. See §3.

---

## 3. Does the manuscript genuinely fit JSA?

### Where it fits well

| Aspect | Assessment |
|---|---|
| Subject | Embedded systems and software on a dual-core SoC, with real-time response-time analysis and operating-system-level task isolation. Squarely inside the stated scope. |
| Formal methods | TLA+ specification, exhaustive model checking, a disclosed vacuous invariant and mutation testing of the specification. Design and architecture, which the scope names. |
| Response-time analysis | A decomposition that reduces four interference terms to one. Classical real-time systems work, and the scope names real-time systems first among its topics. |
| Reproducibility | Byte-identical regeneration from committed seeds, commit-pinned corpus, a live-broker testbed whose verdicts reproduce. Well above the norm. |
| Length | 31 pages in a neutral `article` class. JSA publishes full-length work; this is not a letters-length paper. |

### Where it is at risk

**1. The case-study sentence.** JSA welcomes case studies "but must contribute more than just a
design for a particular piece of software." The manuscript is a case study of one artefact.
Its defence is already written and is the right one: it claims no new mechanism, attack,
protocol or formalism, and instead argues that **applying cheap falsification to a system's
assumptions rather than to its running behaviour** caught three defects that testing, fuzzing,
exhaustive model checking and 9,600 adversarial trials all missed. That is a transferable
practice, not a design. A reviewer who reads only the figures may still see one alarm clock.
**The abstract and introduction must carry the transferability argument early and explicitly;
they currently do.**

**2. The corpus study cuts both ways.** It was the attempt to generalise, and it returned zero
hits in 135 projects. The manuscript reports that honestly and declines to claim prevalence.
A sympathetic reviewer will read this as integrity; an unsympathetic one will read it as
confirmation that the finding is local. There is no way to improve this without more data, and
manufacturing a prevalence claim would be worse than the risk.

**3. No physical measurement.** The paper's own stated open question needs hardware. JSA is an
architecture journal and its readers are accustomed to measured results. Mitigations already in
place: the title no longer claims timing isolation, the hypothesis is marked untested, and the
protocol is published. This remains the most likely reviewer objection, and
`docs/HARDWARE_VALIDATION_PLAN.md` shows conditions A–C are blocked by about £25 of hardware.
**Running A–C before submission would materially reduce this risk.**

**4. Security framing versus an architecture readership.** Two of the three defects are
security findings. JSA's scope names security only implicitly. The framing — defects in
*assumptions*, one configuration, one specification, one response-time — is the architecture
framing, and the new title reflects that.

### Verdict

**JSA is a defensible fit, and the manuscript is technically ready for it, but it is not the
only sensible choice and it is not a safe one.** The case-study sentence and the absent
measurement are real risks. Submitting is reasonable; submitting *after* conditions A–C would
be considerably stronger. **No prediction of acceptance is offered or implied.**

---

## 4. What must still be looked up before submitting to JSA

The Guide for Authors could not be read here. Each item below must be confirmed from
`sciencedirect.com/journal/journal-of-systems-architecture/publish/guide-for-authors` before
submission. The manuscript's current state is given so the gap is visible.

| Requirement | Current state of the manuscript | Action |
|---|---|---|
| Article types and any page limit | 31 pages, `article` class | confirm no limit is exceeded |
| Abstract: word limit, structured or not | ~430 words, unstructured | **likely over a typical 250-word limit; check first** |
| Keywords: how many | 10 supplied | confirm the permitted range |
| Reference style | Numbered `\bibitem`, 22 entries | JSA is typically numbered Elsevier style; confirm, and consider `elsarticle-num` with a `.bib` |
| Title page, highlights, graphical abstract | none prepared | Elsevier commonly requires **Highlights** (3–5 bullets, ≤85 characters each); check |
| Figure formats and resolution | 8 vector PDFs; 600 DPI PNGs also prepared | confirm accepted formats; both are ready |
| Figure colour and numbering | colour, numbered, all `\textwidth` | confirm colour is free online |
| Supplementary material | repository plus the figure ZIP | confirm the mechanism and size limits |
| Declaration of competing interest | **not in the manuscript** | **must be added** |
| Funding statement | **not in the manuscript** | **must be added**, even if "none" |
| Ethics / human subjects | not applicable | confirm the form of words |
| **Declaration of generative AI** | present as a standalone section | confirm the exact wording Elsevier requires |
| CRediT author statement | not prepared | single author; confirm whether required |
| Data availability statement | repository is public | confirm the required form |
| Submission system | Editorial Manager, presumably | confirm |

The template switch is a one-line change: the preamble already carries commented-out
`elsarticle` and `IEEEtran` alternatives.

---

## 5. Alternative venues

Three alternatives, should JSA prove unsuitable or its requirements unachievable. Metrics are
marked unverified unless read during this check.

### A. ACM Transactions on Embedded Computing Systems (TECS)

| | |
|---|---|
| Scope fit | **Good, by reputation.** The official site carries no formal scope statement, so this is **unverified**; its published output covers embedded design methods, real-time behaviour and embedded security. |
| Contribution expectations | High. ACM transactions generally expect generalisable contributions, which sharpens the same case-study risk JSA poses. |
| Metrics / quartile | **unverified** |
| Weakness for this manuscript | Likely a *harder* venue for a single-artefact case study than JSA. The corpus study's zero result would be pressed harder. |
| Strength | Formal verification and response-time analysis are squarely in its tradition, and the reproducibility package would be valued. |

### B. Empirical Software Engineering (Springer)

| | |
|---|---|
| Scope fit | **Verified, and arguably the best match for what this paper actually is.** Its scope states it "provides a forum for applied software engineering research with a strong empirical component", spanning "controlled experiments to field studies". |
| Replications and negative results | **Verified:** "Both original and replicated studies can be reported" and "Preference is given to studies that can be replicated or expanded upon." Negative results are not named explicitly. |
| Why it fits | This is a paper about *method*: falsifying assumptions cheaply, with a corpus study that returned a negative result and a documented record of four harness defects. EMSE's stated preference for replicable work is exactly what the byte-identical regeneration and commit-pinned corpus deliver. |
| Weakness for this manuscript | The response-time decomposition and the TLA+ work are not empirical software engineering, and would read as a long detour to that readership. The paper would need reframing, not just reformatting. |
| Metrics / quartile | **unverified** |

### C. IEEE Embedded Systems Letters

| | |
|---|---|
| Scope fit | Good for embedded systems. **Unverified** in detail. |
| Format | Letters-length. The repository already holds `paper/paper.tex`, a short version. |
| Why consider it | The compile-guard finding alone — an unsound inference in a build condition that costs a *safety* property and emits no diagnostic — is a self-contained letters-length result. |
| Weakness | Discards the ablation, the broker testbed, the corpus study and the response-time analysis. A much smaller paper. |
| When to choose it | If the priority is to publish the guard finding quickly while the hardware measurement is pending, rather than to publish the full study. |

### Recommendation

**Submit to JSA**, on the strength of the verified scope match — embedded systems and
software, real-time systems, case studies accepted with a contribution beyond a design — and
because the manuscript's framing already answers the case-study condition.

**Before submitting**, in priority order:

1. Obtain the Guide for Authors and work through §4, above all the abstract length and the
   competing-interest and funding declarations, which are currently missing.
2. Verify the quartile and its year through the institutional library.
3. Seriously consider running hardware conditions A–C first. They need about £25 and an
   afternoon, and they address the objection most likely to cost an acceptance.
4. Obtain the institutional similarity report (`docs/SIMILARITY_SCREENING_CHECKLIST.md`).
5. Supervisor approval.

**Keep Empirical Software Engineering as the considered second choice**, not as a fallback: if
the supervisor's judgement is that the methodological claim is the paper's real contribution,
EMSE is the better home and the reframing is worth the work.

---

## Sources

- [Journal of Systems Architecture — Elsevier](https://shop.elsevier.com/journals/journal-of-systems-architecture/1383-7621)
- [Journal of Systems Architecture — ScienceDirect](https://www.sciencedirect.com/journal/journal-of-systems-architecture)
- [Journal of Systems Architecture — Insights (metrics)](https://www.sciencedirect.com/journal/journal-of-systems-architecture/about/insights)
- [Guide for Authors — Journal of Systems Architecture](https://www.sciencedirect.com/journal/journal-of-systems-architecture/publish/guide-for-authors) (could not be retrieved during this check)
- [ACM Transactions on Embedded Computing Systems](https://mail.acmtecs.hosting.acm.org/)
- [Empirical Software Engineering — aims and scope](https://link.springer.com/journal/10664/aims-and-scope)

---

## 2a. Second pass: what is now verified

Retrieved 7 November 2026 from Elsevier's own pages, read in a real browser because the
container's network cannot reach them.

### Journal facts

| Item | Value | Source |
|---|---|---|
| Full title | Journal of Systems Architecture: Embedded Software Design | Guide for authors |
| Print ISSN | 1383-7621 | Insights |
| **Online ISSN** | **1873-6165** | Insights |
| Editor-in-Chief | Zonghua Gu, Hofstra University, USA | journal home |
| CiteScore | 9.1 | Guide / Insights |
| Impact Factor | 5.3 | Guide / Insights |
| **Reference year for both metrics** | **not stated anywhere on the page** | read and confirmed absent |
| **Abstracting and indexing** | **Scopus; Science Citation Index Expanded (SCIE); SCImago Journal Rank (SJR); SNIP; Ei Compendex** | Insights |
| Subject areas | Hardware and Architecture; Software; Computer Networks and Communications; Computer Science Applications; Control and Systems Engineering | Insights |
| Publication model | hybrid — open access supported, subscription also available | Insights |
| APC (open access) | USD 2,260 excluding taxes; "actual APCs may differ based on individual author circumstances"; institutional agreements may cover it | Insights |
| Subscription route | "No publication fee charged to authors" | Insights |
| Submission to first decision | 1 day | Insights |
| Submission to decision after review | 43 days | Insights |
| Submission to acceptance | 123 days | Insights |
| Acceptance to online publication | 11 days | Insights |

**SCIE indexing is the useful new fact.** It means the journal carries a Journal Citation
Reports entry, and therefore a JCR quartile, which the author can read directly from JCR
through the SVNIT library. Scopus indexing likewise means a SCImago quartile exists.

### Quartile — still unverified, and why

SCImago was reached in a real browser and returned **HTTP 403 with a Cloudflare interstitial**
("Just a moment…"). That is bot protection and **it was not circumvented**, per the operating
constraint on this work.

**No quartile is claimed anywhere in this repository.** The author can settle it in minutes:

- **JCR** (Clarivate) via the SVNIT library → gives the JCR quartile in its categories.
- **Scopus Sources** → gives the CiteScore percentile and quartile.
- **scimagojr.com** opened manually in an ordinary browser → gives the SJR quartile.

Record the **year** beside whichever figure is used. The absence of a metric year on Elsevier's
own page is exactly why.

### Article types and length

| Item | Verified requirement |
|---|---|
| Accepted types | Original research articles; Review articles; Short Communications |
| This manuscript | Original research article |
| **Page or word limit** | **none stated.** The Guide sets no length limit for research articles; the only length constraint anywhere is the abstract. |

The 31-page length is therefore not a problem, which resolves the earlier open question.

### Special issues

Two calls were open at the time of checking, and one is close to this work but **its deadline
has passed**: *Timing-Verifiable Intelligent Real-Time Systems* (guest editors Shuai Zhao,
Zhuoran Song, Yue Tang), submission deadline **31 October 2026**. Today is 7 November 2026, so
submission must go to the **regular issue**. Worth watching for a successor call, since the
topic fit is strong.

---

## 4a. The nine formatting requirements, resolved

Each row gives the verified requirement, what the manuscript had, and what was done.

| # | Requirement (verified) | Was | Action taken | Status |
|---|---|---|---|---|
| 1 | **Abstract must not exceed 250 words**; must stand alone; avoid references; avoid non-standard abbreviations | **521 words** | Rewritten to **249 words**, keeping all three defects, the measured figures, the independence finding and the logical-isolation-only scope | **RESOLVED** |
| 2 | **1 to 7 keywords**; avoid keywords using "and" or "of"; abbreviations only if firmly established | **10 keywords** | Cut to **7**: embedded systems security; MQTT; configuration defects; specification mutation; response-time analysis; formal verification; ESP32. None contains "and" or "of"; all three title nouns are represented | **RESOLVED** |
| 3 | **Highlights**: encouraged; 3–5 bullets; **max 85 characters each including spaces**; separate editable file with "highlights" in the filename | not prepared | `paper/submission/highlights.txt` — 5 bullets, longest 80 characters, verified programmatically | **RESOLVED** |
| 4 | **Reference style**: numbers in square brackets, numbered in order of appearance; journal names abbreviated per LTWA. *Formatting is not strictly required at submission* provided it is consistent and complete | numbered `\bibitem`, square brackets | Already conforms. 22 entries, 22 cited, none orphaned. Elsevier applies its own style at proof stage and will request missing data then — so the five absent DOIs are a proof-stage request, not a submission blocker | **RESOLVED** |
| 5 | **Figures**: vector drawings as **EPS or PDF**, with *fonts embedded or text saved as graphics*; no Type 3; do not combine multiple graphs in one file except where they are meant to be compared | 8 vector PDFs | Verified with `pdffonts`: **every font in all eight is embedded, and none is Type 3.** Figures 3 and 5 are multi-panel, which the Guide's stated exception covers — their panels exist precisely to be compared, and each caption says so | **RESOLVED** |
| 6 | **Declaration of competing interest**: disclose eight named categories; complete the declarations tool; upload a `.doc`/`.docx`; signatures not required | present, titled "Conflicts of interest" inside a combined Declarations section | Promoted to its own section with Elsevier's title and standard wording. `paper/submission/declaration-of-competing-interest.md` prepared for conversion to `.docx`. **Author confirmation required** — `docs/DECLARATIONS.md` §1 | **PREPARED, CONFIRM** |
| 7 | **Funding**: disclose sources and the sponsor's role; if there was no involvement, say so; use Elsevier's standard form | present as "This research received no external funding" | Rewritten to Elsevier's standard sentence. **Author confirmation required** — `docs/DECLARATIONS.md` §2 | **PREPARED, CONFIRM** |
| 8 | **CRediT**: corresponding author must acknowledge contributions using the listed roles | present but with lower-case ad-hoc role names | Rewritten as its own `CRediT authorship contribution statement` using the exact taxonomy names. **One open question**: sole author, or supervisor as co-author with the *Supervision* role? — `docs/DECLARATIONS.md` §3 | **PREPARED, CONFIRM** |
| 9 | **Declaration of generative AI use**: a statement at the end, in a new section **before the reference list**; AI not listed as an author | present, titled "…in the writing process" | Retitled to the Guide's exact example — "…in the manuscript preparation process" — and sits immediately before the bibliography. AI is not an author | **RESOLVED** |

### Also resolved in this pass

| Requirement | Verified | Status |
|---|---|---|
| Numbered sections, subsections as 1.1, 1.1.1 | required; cross-reference by number, not "the text" | 14 numbered sections; no prose refers to "the text" — **conforms** |
| Title page: title, author names, affiliation with full postal address and country, corresponding author's email | required | Title, name and affiliation present. **The corresponding author's email must be added** — `docs/DECLARATIONS.md` has it as an upload-step item |
| Data statement | required at submission | own `Data availability` section — **conforms** |
| Acknowledgements | separate section immediately before the reference list; **not** on the title page or in a footnote | **none present.** Only needed if someone is to be thanked — the author's decision |
| Supplementary material | cite all supplementary files in the text; submit with the manuscript; appears exactly as received | repository and figure archive — **confirm which, if any, is uploaded as formal supplementary material** |
| Submission system | online submission system linked from the Guide | — |

### The one remaining content question

The Guide repeats, in the aims and scope, the sentence that matters most here:

> "Case studies are welcome but must contribute more than just a design for a particular piece
> of software."

This is now confirmed as the journal's own standing position, not an incidental line on a
marketing page. The manuscript's answer is unchanged and is the right one: it claims no new
mechanism and argues a transferable practice. That argument must remain prominent in the
abstract — and the 249-word rewrite was checked to keep it.
