# Journal selection, 2026

Assessed against the **revised** contribution — a single-system case study with a methodological
finding, strongest in the configuration and specification dimensions, with no physical hardware
measurement — rather than against impact factors.

---

## 0. Verification status, stated before any recommendation

Part 12 of the brief forbids inferring quartile status from an impact factor, a CiteScore or a
website claim, and requires that Scopus CiteScore quartiles be kept distinct from JCR Impact
Factor quartiles. Both constraints bind hard here, because the independent indexing source could
not be reached.

| What was verified, and how | What was **not** |
|---|---|
| Scope, ISSN, article-type statements and APC: read from each publisher's own pages | **Independent Scopus or JCR records.** The indexing source returned an automated challenge, which was **not** circumvented |
| Metric *values* where a publisher states them | **The metric years.** No publisher page visited stated the year for any figure |
| Quartiles *as claimed by a publisher* | **Any independently confirmed quartile.** None is asserted anywhere in this document or in the manuscript |

**Consequence: no quartile below is a verified quartile.** Where one appears it is labelled as a
publisher claim, and every metric value carries "year not stated". A Q2 target cannot be confirmed
from here, and the manuscript asserts no quartile anywhere.

---

## 1. Best fit — Journal of Systems Architecture (Elsevier)

| | |
|---|---|
| ISSN | 1383-7621 (print), 1873-6165 (online) |
| Scope, as published | Design and architectural aspects of embedded systems and software, from microarchitecture through system software to application-specific architecture: real-time systems, operating systems, programming languages, communications limited to analysis and the software stack, parallel and distributed architectures, hardware/software co-design with an emphasis on software. **"Hardware design itself is not a focus."** |
| Article types | **"Case studies are welcome but must contribute more than just a design for a particular piece of software."** |
| Metrics as stated by the publisher | Impact Factor 5.3; CiteScore 9.1. **Years not stated on the page.** |
| Indexing | Not stated on the pages retrieved; **not independently verified** |
| Model and APC | Hybrid; APC not retrieved |

**Why it is the best fit.** Three reasons, in order of weight.

1. **The article-type bar is explicit and this work clears it.** JSA welcomes case studies that
   contribute more than a design. This work contributes a methodological finding, 9,600 adversarial
   trials, eight live-broker scenarios, exhaustive model checking and a conditional theorem. A
   reviewer applying that sentence literally should find the bar met.
2. **The scope matches all three dimensions**, which no other candidate does. Build-time
   configuration of system software, formal specification of an embedded state machine, and
   response-time analysis of a FreeRTOS task are all squarely inside "system software" and
   "real-time systems". That "hardware design itself is not a focus" also works in this paper's
   favour: it signals a software-architecture readership rather than a measurement readership.
3. **The manuscript is already compliant.** Its Guide for Authors was obtained and verified in
   earlier work, and the manuscript satisfies every requirement checked: 33 pages, 23 references
   with none dangling, a 249-word abstract, 7 keywords, declarations in the publisher's named
   sections, 5 highlights with the longest at 80 of 85 characters, and 8 vector figures with all
   fonts embedded and no Type 3.

**Main reviewer risk, and it is serious.** A real-time or embedded-architecture reviewer will go
straight to the response-time section and find a conditional theorem with **no number for $R$** and
no measured WCET. The honest answer is that the theorem converts the question into "is $\bar{I}$
small enough?" and that the protocol to answer it is pre-registered and published unexecuted. That
answer is defensible but it will not satisfy a reviewer who wants a timing result, and this is the
single likeliest cause of rejection.

**Required before submission.** Subordinate the execution dimension explicitly in the cover letter:
state that the paper's contribution is the assumption analysis, that the response-time work is
reported as a *defect-finding* instrument rather than a certification, and that no timing claim is
made. Draw the reviewer's attention to §12, the pre-registered protocol, as the answer to "why no
measurement" — before they ask.

---

## 2. Second choice — Applied Sciences (MDPI)

| | |
|---|---|
| ISSN | 2076-3417 |
| Scope, as published | "All aspects of applied natural sciences", peer-reviewed, open access, semimonthly |
| Indexing, **publisher-stated** | Scopus, SCIE (Web of Science), Ei Compendex, Inspec, Embase, CAPlus/SciFinder |
| Metrics, **publisher-stated** | Impact Factor 2.9; CiteScore 6.1. **Years not stated.** |
| Quartiles, **publisher claim only** | JCR Q2 in Engineering, Multidisciplinary; CiteScore Q1 in Fluid Flow and Transfer Processes. **Neither independently verified; note the CiteScore quartile is in an unrelated category** |
| Model and APC | Fully open access; **APC CHF 2,400** plus local VAT, payable only on acceptance. IOAP institutional discounts exist |
| Article types | Not listed on the page retrieved |

**Why it is a serious candidate despite the breadth.** There is **direct scope precedent**: the
nearest-neighbour work to this paper's broker experiment — Radwan and Sheldon's experimental
quantification of MQTT authentication enforcement and ACL misconfiguration impact — was published
in this journal in 2026, in volume 16 issue 7. A venue that accepted that paper is a venue whose
scope accommodates this one, and this work's E/E′ comparison is the question that paper's design
could not ask.

It is also the only candidate whose Scopus indexing was confirmed from the publisher's own page,
and the breadth of scope means the absence of hardware measurement is far less likely to be
treated as disqualifying.

**Main reviewer risks.** Reviewer expertise is the real concern: a multidisciplinary applied
journal may not supply a reviewer who can assess a TLA+ vacuity argument, so the specification
dimension may be under-reviewed — which is a risk to the paper's eventual credibility rather than
to its acceptance. MDPI's review speed also attracts scepticism in some committees, which matters
if this paper is to support a dissertation.

**The practical blocker.** **CHF 2,400 is a hard constraint for a student author and must be
settled before submission, not after acceptance.** SVNIT institutional IOAP membership should be
checked first; if there is no coverage, this option is effectively unavailable and option 1 or 3,
both hybrid, should be preferred.

---

## 3. Third choice — Empirical Software Engineering (Springer)

| | |
|---|---|
| Scope, as published | "A forum for applied software engineering research with a strong empirical component", emphasising industry relevance |
| Study types | Controlled experiments, field studies, data-intensive studies, qualitative studies; original **and replicated** studies; infrastructure for empirical research. **Case studies and experience reports are not explicitly named** |
| Stated requirement on number of cases or subjects | **None stated** |
| Model | **Hybrid** — open access is optional, so no mandatory APC |
| Indexing and metrics | Not stated on the pages retrieved; **not independently verified** |

**Why it is a genuine fit for the actual contribution.** This is the venue whose values match this
work's strongest property. EMSE states that it gives preference to studies that can be replicated
or expanded upon, and this artefact is unusually replicable: fixed seeds, fork-per-trial isolation,
stdlib-only statistics, figure SVGs that regenerate byte-identically, broker verdicts reproduced on
a clean install, and a 6,000-trial campaign re-run from scratch during this revision in which every
trial outcome reproduced identically. EMSE also explicitly welcomes work on infrastructure for
empirical research, and this paper's five documented infrastructure defects — two of which
flattered the intended conclusion, one of which was a test that could not fail — are exactly that
kind of contribution. Being hybrid, it imposes no APC.

**Main reviewer risks, and they are the hardest of the three.** An EMSE reviewer will press on two
points. First, **one system**: the paper argues the defect *categories* generalise while the
instances do not, and EMSE's methodological standards for single-case research are high — the paper
would need to frame itself explicitly as a case study against an accepted case-study methodology
rather than as an engineering report. Second, **the corpus null result**: rule 1 returned 0/135 and
rule 2 is 50% false-positive, and a reviewer may read the generalisation attempt as a failed study
rather than as an honest null. Shen et al.'s comparable 34% false-positive rate across 258 projects
at ISSTA is the right defence and should be cited where the rate is reported.

**Required before submission.** Reframe the paper's methodology section around a recognised
case-study protocol, and move the embedded and formal material into a form a software-engineering
reviewer can assess without platform expertise. That is a larger rewrite than either option above.

---

## 4. Considered and rejected

| Venue class | Why rejected |
|---|---|
| Real-time systems venues (e.g. *Real-Time Systems*) | Would require a measured or certified WCET. The paper has a conditional theorem with no number. The brief's own warning applies: a venue that expects physical experiments for this research area is the wrong venue |
| Pure security venues (*Computers & Security*, *Journal of Information Security and Applications*) | The configuration and trade-off dimensions fit well, but the response-time dimension and the formal-vacuity finding would have to be cut or heavily subordinated — which would discard the coupling between dimensions that makes the paper a thesis rather than a list |
| IoT-specific venues (*Internet of Things*, *IEEE IoT Journal*) | Plausible, but an IoT reviewer is the most likely to expect a deployed or hardware evaluation, and this work has neither |
| High-APC mega-journals | No scope advantage over option 2 at higher cost |

---

## 5. Does the evidence support a Q2 submission?

**The contribution is defensible at a Q2 level if, and only if, it is positioned as an in-depth
single-system case study with a methodological finding, in a venue that accepts that article type.**

Three things support that: the two couplings between dimensions give the paper a thesis rather than
three anecdotes; the live-broker E/E′ pair and the twelve-arm ablation are real measured evidence;
and the negative results — the layered build's failure to a compromised controller, the owner
lockout, the corpus null, five of its own infrastructure defects, and two statistical errors
corrected in this revision — buy the kind of credibility that is hard to obtain any other way.

**It is not defensible if positioned as a framework, as a prevalence study, or in a venue expecting
physical measurement.** The absence of hardware data is not fatal to the configuration and
specification dimensions; it is fatal wherever the execution dimension is read as the headline.

**And the quartile itself cannot be confirmed from here.** No quartile is asserted in the manuscript
or in this document, because the independent indexing source could not be reached without
circumventing bot protection, which was not attempted. **Whether any of these venues is currently
Q2 must be checked by the author through institutional Scopus or JCR access before submission.**
That is listed as an outstanding item in `FINAL_SUBMISSION_CHECKLIST.md`.

**No guarantee of acceptance or publication is offered or implied.**

---

## 6. Recommendation

1. **Submit to the Journal of Systems Architecture.** Best scope match across all three dimensions,
   an explicit case-study provision this work clears, no APC blocker, and the manuscript is already
   compliant with its verified Guide for Authors. Pre-empt the timing objection in the cover letter.
2. **If desk-rejected on the missing measurement**, go to **Applied Sciences** — but only after
   confirming APC coverage. The 2026 precedent paper makes the scope argument straightforward.
3. **If the supervisor prefers a software-engineering framing**, go to **EMSE**, accepting that it
   needs a methodology rewrite around a recognised case-study protocol.

**Before any submission**, the five author-blocked items in `FINAL_SUBMISSION_CHECKLIST.md` remain
outstanding: institutional similarity screening, supervisor approval, the dissertation-overlap
ruling, the three author declarations, and the corresponding author's contact details.

---

## Sources

- [Journal of Systems Architecture — journal page, ScienceDirect](https://www.sciencedirect.com/journal/journal-of-systems-architecture)
- [Journal of Systems Architecture — Guide for Authors](https://www.sciencedirect.com/journal/journal-of-systems-architecture/publish/guide-for-authors)
- [Applied Sciences — journal page, MDPI](https://www.mdpi.com/journal/applsci)
- [Applied Sciences — Article Processing Charge](https://www.mdpi.com/journal/applsci/apc)
- [Applied Sciences, Volume 16, Issue 7 (the 2026 precedent paper)](https://www.mdpi.com/2076-3417/16/7)
- [Empirical Software Engineering — Aims and scope, Springer](https://link.springer.com/journal/10664/aims-and-scope)
