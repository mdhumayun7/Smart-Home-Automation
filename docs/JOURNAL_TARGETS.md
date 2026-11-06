# Candidate journals: verified comparison

**Verification date: 6 November 2026.** Every figure below was taken from the publisher's own
pages or official flyers. Where a field could not be verified from an authoritative source it is
marked **Not verified**, not filled from a secondary site.

---

## 1. An important caveat before the table

### 1.1 "Q2" means two different things

The master requirement asked for a Scopus-indexed **Q2** journal. Two independent quartile
systems exist and they are not interchangeable:

| System | Metric | Operator |
|---|---|---|
| **Scopus CiteScore quartile** | CiteScore | Elsevier / Scopus |
| **JCR quartile** | Journal Impact Factor | Clarivate (Web of Science) |

A journal can be CiteScore Q1 and JCR Q2 at the same time, in different subject categories. Every
MDPI journal below is exactly that. So:

- If "Q2" means **JCR Q2**, all four MDPI journals below qualify.
- If "Q2" means **Scopus CiteScore Q2**, none of them are Q2 — they are CiteScore **Q1**, which is
  higher, in the categories their publishers state.

Both readings are satisfied by the shortlist, but the distinction must be stated correctly in any
report to a supervisor or committee. Do not write "Scopus Q2" when the source said "JCR Q2".

### 1.2 What could not be verified here, and how to finish it

**SCImago (scimagojr.com) and the Scopus source list were not reachable from this environment.**
Every quartile below is therefore **publisher-stated**, not independently confirmed against
Scopus's own records. Secondary aggregator sites (researcher.life, letpub, peeref, resurchify,
journalsearches and similar) appeared in search results and were deliberately **not used**: their
figures are unattributed and frequently stale.

To close this gap yourself, which takes about ten minutes:

1. Go to Scopus Sources (`scopus.com/sources`, free to search without a subscription).
2. Enter the journal title or ISSN.
3. Record the CiteScore, the subject category, the percentile and the quartile, and the year shown.
4. For the JCR quartile, use your institution's Web of Science access and check Journal Citation
   Reports for the same journal.

Quartiles are recalculated annually and differ per subject category. A journal that is Q2 today
may not be at submission or publication time, and no one can promise otherwise.

---

## 2. Shortlist

Six candidates, all genuinely in scope for an embedded-systems security and verification paper.

| # | Journal | Publisher | IF | CiteScore | JCR quartile (publisher-stated) | CiteScore quartile (publisher-stated) | APC | Scopus-indexed |
|---|---|---|---|---|---|---|---|---|
| 1 | **IEEE Embedded Systems Letters** | IEEE (CEDA) | Not verified | Not verified | Not verified | Not verified | **None** for traditional; US$2,800 optional OA | Not verified |
| 2 | **Journal of Sensor and Actuator Networks** (JSAN) | MDPI | 4.8 | 11.3 | **Q2** Computer Science, Information Systems | Q1 Control and Optimization | CHF 2,000 | Yes |
| 3 | **Computers** | MDPI | 5.2 | 9.1 | **Q2** Computer Science, Interdisciplinary Applications | Q1 Computer Science (misc.) | CHF 1,800 | Yes |
| 4 | **Sensors** | MDPI | 4.0 (2025 JCR) | 9.4 | **Q2** Instruments and Instrumentation | Q1 Instrumentation | Not verified | Yes |
| 5 | **Electronics** | MDPI | 2.9 (2025 JCR) | 7.0 | **Q2** Engineering, Electrical and Electronic | Q1 Signal Processing | CHF 2,400 | Yes |
| 6 | **Applied Sciences** | MDPI | Not verified | Not verified | Not verified | Not verified | CHF 2,400 | Not verified |

Publisher pages did not state the year for several metrics; those are reproduced as given rather
than assigned a year.

---

## 3. Per-journal assessment

### 3.1 IEEE Embedded Systems Letters — recommended first submission

| Field | Verified detail |
|---|---|
| Sponsor | IEEE; listed under IEEE Council on Electronic Design Automation (CEDA) |
| Scope | **Early-stage research in embedded systems.** Out-of-scope manuscripts may be desk-rejected |
| Article types | Research papers and tutorial papers |
| Length | **Four pages or fewer**, including figures, tables and references (about 2,200 words in IEEE two-column format). Over four pages after typesetting incurs US$125 per page; eight pages is the hard limit |
| Open access | Hybrid. Traditional publication carries **no fee**. Optional OA is US$2,800 on acceptance |
| Discounts | IEEE Members 5 %, Society Members 20 %, not combinable, **students excluded**. Corresponding authors in low-income countries may be eligible for APC discounts |
| Submission | IEEE Author Portal, with a ScholarOne route also linked |

**Why this is the strongest fit.** Three reasons, in order of weight:

1. **The scope statement is "early-stage research."** This is the only venue on the list whose
   stated remit matches the project's actual evidential position: a formally verified design with
   simulation results and a specified-but-unrun hardware campaign. Elsewhere that is a weakness;
   here it is the category.
2. **No APC on the traditional route.** CHF 1,800–2,400 is roughly ₹1.7–2.3 lakh. For a
   self-funded M.Tech student that is the difference between submitting and not. Note the student
   exclusion applies only to the optional OA discount, not to the free traditional route.
3. **The four-page limit matches the existing draft**, which is already a four-page two-column
   paper. The manuscript would need tightening and reformatting to IEEE style, not expansion.

**Risks.** The quartile is unverified, so confirm it before committing. The four-page ceiling is
genuinely tight for a paper carrying formal results, a campaign table and a figure — some material
would move to a supplementary repository reference. Acceptance standards at IEEE letters venues
are not lower than at the MDPI journals; "early-stage" governs scope, not rigour.

### 3.2 JSAN — recommended if open access is wanted

| Field | Verified detail |
|---|---|
| ISSN | 2224-2708 |
| Scope hits | "WSAN reliability, trust, security, and privacy"; "Intrusion Detection in SANs"; lightweight cryptography; "system architecture, operating systems, and network hardware"; IoT-based WSANs |
| Article types | Research papers, reviews, short communications. Explicitly encourages "detailed experimental and theoretical reporting" and accepts supplementary material such as software |
| Indexing | Scopus, ESCI (Web of Science), dblp, Inspec |
| APC | CHF 2,000 |

**Best scope match on the list.** Security, trust, intrusion detection, lightweight cryptography
and system architecture are all named scope items, and this paper touches four of them. That the
journal accepts software as supplementary material suits a repository-backed artifact. It is
JCR Q2 in Computer Science, Information Systems — precisely the category a reader would expect
this work to be judged in.

### 3.3 Computers — cheapest Q2 option

APC CHF 1,800, the lowest on the list. JCR Q2 (Computer Science, Interdisciplinary Applications),
CiteScore Q1 (Computer Science, miscellaneous), CiteScore 9.1, IF 5.2. Scope includes "Hardware
components and architecture" and "Security and privacy", but the flyer does not name embedded
systems or IoT explicitly, so the fit is good rather than exact. A reasonable second MDPI choice
if JSAN declines on scope.

### 3.4 Sensors — strong metrics, weakest scope fit

CiteScore 9.4 and wide readership, and the directly comparable prior work (Kremser and Graffi on
ESP32-S3 deauthentication, *Sensors* 26(11):3287, 2026) appeared here, which is a real argument
for fit. Against that: the journal is organised around sensing, and this paper's contribution is
task isolation and command authentication, not sensing. The PIR and mmWave fusion component is
genuinely sensor work but is a secondary feature, not the headline. Expect a scope challenge
unless the framing is shifted toward the sensor-fusion and detection aspects. APC was not
verifiable and should be checked before submitting.

### 3.5 Electronics — broad and safe

IF 2.9 (2025), CiteScore 7.0, JCR Q2 (Engineering, Electrical and Electronic). Broad scope with
no named embedded-systems or IoT-security section; the closest are Networks, Computer Science and
Engineering, and Systems and Control Engineering. Workable but less targeted than JSAN, at a
higher APC than Computers.

### 3.6 Applied Sciences — listed for completeness only

APC CHF 2,400 verified; metrics and quartile not verified here. A very broad multidisciplinary
journal. No specific reason to prefer it over JSAN or Computers for this work.

---

## 4. Recommendation

| Priority | Journal | Reason |
|---|---|---|
| 1 | **IEEE Embedded Systems Letters** | Scope explicitly covers early-stage embedded research; no APC on the traditional route; four-page format already matches the draft |
| 2 | **JSAN** (MDPI) | Best scope match; JCR Q2 in the right category; accepts software artifacts; CHF 2,000 |
| 3 | **Computers** (MDPI) | JCR Q2, lowest APC at CHF 1,800, acceptable scope fit |

**Submit to one at a time.** Simultaneous submission to multiple journals is a serious ethics
breach and will get the paper retracted or blacklisted.

**Before submitting anywhere, read Section 5.**

---

## 5. The blocker, stated plainly

**The project has no hardware measurements.** All results are formal verification and host-based
simulation, and the paper's headline claim — that core pinning preserves the sensor-to-siren
deadline while the chip's own radio driver is under stress — is explicitly the one claim that
cannot be established without silicon (`docs/RESEARCH.md`, claim C5).

For a reviewer in embedded systems or IoT security this is the first thing they will look for. The
realistic outcomes of submitting as the work currently stands:

| Venue | Likely outcome without hardware data |
|---|---|
| IEEE ESL | Plausible, given the "early-stage research" remit, but reviewers will still ask why the central claim is untested on hardware when the hardware is two inexpensive boards |
| JSAN / Computers / Sensors / Electronics | Major revision requiring new experiments, or reject. MDPI review is fast and reviewers in these journals routinely require measured results for a device-level claim |

**The fix is small and cheap.** Conditions A–C of the hardware protocol
(`experiments/hardware/README.md`) need two ESP32 DevKit boards and a logic probe, no RF isolation
and no institutional clearance. Running those three conditions converts the paper from "formally
verified, empirically untested" to "formally verified and measured", which is a different
submission. Condition D (radio-layer stress) needs an authorised isolated RF environment and can
honestly remain future work.

Recommended sequence:

1. Run hardware conditions A–C.
2. Fold the measured latency distributions into the results section.
3. Verify the quartile of the chosen journal against Scopus Sources (Section 1.2).
4. Reformat to that journal's template and submit to one journal.

---

## 6. Predatory-publishing screen

All six candidates passed the following checks, performed against publisher pages on
6 November 2026:

| Check | Result |
|---|---|
| Publisher identifiable and established | Yes — IEEE and MDPI are both long-established with verifiable corporate identity |
| Indexing claims checkable | Yes for the MDPI journals (Scopus, Web of Science, Inspec, Ei Compendex, dblp named explicitly). Not verified for IEEE ESL, but IEEE's indexing is not in doubt |
| Fees stated openly before submission | Yes — all APCs are on public pages with currency and conditions |
| No guaranteed or implausibly fast acceptance promised | Correct, none found |
| Editorial board verifiable | Yes, both publishers list boards publicly |
| No unsolicited-invitation pattern | Not applicable; these were selected by scope, not from solicitation emails |

**None of these journals was selected because it advertised fast acceptance.** If a solicitation
email arrives offering rapid publication in a journal not on this list, treat it as predatory
until independently verified in Scopus Sources.

A general caution: MDPI's model is high-volume and fast, which is legitimate and Scopus-indexed
but is viewed with varying regard across academic communities. Confirm with Dr. Zaveri that an
MDPI venue is acceptable for your department's purposes before paying an APC.

---

## 7. Sources

All consulted on 6 November 2026.

- [MDPI *Sensors* journal page](https://www.mdpi.com/journal/sensors) and [official flyer](https://pub.mdpi-res.com/journals/3/flyer.pdf)
- [MDPI *Electronics* official flyer](https://pub.mdpi-res.com/journals/127/flyer.pdf) and [APC page](https://www.mdpi.com/journal/electronics/apc)
- [MDPI *JSAN* official flyer](https://pub.mdpi-res.com/journals/138/flyer.pdf), [about page](https://www.mdpi.com/journal/jsan/about) and [APC page](https://www.mdpi.com/journal/jsan/apc)
- [MDPI *Computers* official flyer](https://pub.mdpi-res.com/journals/26/flyer.pdf) and [APC page](https://www.mdpi.com/journal/computers/apc)
- [MDPI *Applied Sciences* APC page](https://www.mdpi.com/journal/applsci/apc)
- [MDPI APC changes effective January 2025](https://mdpi.com/about/apc-2025)
- [IEEE Embedded Systems Letters author instructions (IEEE CEDA)](https://ieee-ceda.org/publication/esl/esl-author-instructions)

Deliberately excluded as non-authoritative: researcher.life, letpub.com, peeref.com,
resurchify.com, journalsearches.com, journalindexes.com, editage.com, journalmetrics.org and
similar aggregators.
