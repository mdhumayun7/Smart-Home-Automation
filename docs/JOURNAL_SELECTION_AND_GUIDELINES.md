# Journal selection and author guidelines

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
| Length | 30 pages in a neutral `article` class. JSA publishes full-length work; this is not a letters-length paper. |

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
| Article types and any page limit | 30 pages, `article` class | confirm no limit is exceeded |
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
