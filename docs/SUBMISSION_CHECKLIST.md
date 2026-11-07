# Submission-readiness checklist

State at commit `b70f93b`. The verdict is at the bottom; it is **not ready**, and the reason is
one missing experiment rather than anything that can be edited.

## Done and verified

| Item | State | How it was checked |
|---|---|---|
| Manuscript compiles | 29 pages, 0 overfull boxes, 0 undefined references | `pdflatex` twice, log inspected |
| Every figure referenced | 8 figures, all cited in text | label/ref cross-check script |
| Every table referenced | 10 tables, all cited in text | same |
| Every reference cited | 22 references, none orphaned | `\cite` against `\bibitem` |
| Citation fields verified | All 22, from publisher, proceedings, institutional repository or OpenAlex | see below |
| Headline statistics | All recomputed from committed data | recomputation script, cell by cell |
| Trial counts reconciled | 6,000 + 3,300 = 9,300; table in the manuscript names each artefact | derived from raw files |
| Results reproduce | Byte-identical from a clean build | full pipeline re-run, `diff` |
| Formal verification | 3 TLC configurations, one required to fail | `formal/run_tlc.sh` |
| Host tests | 123 checks across 2 core versions and 3 clock offsets | `tests/host/run_tests.sh` |
| HMAC primitive | RFC 4231 cases 1, 2, 6 pass | new known-answer tests |
| Broker validation | 8 scenarios against Mosquitto 2.0.18, all agree with the model | `experiments/broker/run.sh` |
| CI | 7 jobs, including the broker and two required-to-fail checks | each job's script run locally |
| AI disclosure | Standalone declaration in Elsevier's required form | — |
| Author contributions | CRediT terms | — |
| Data and code availability | Present; notes that broker keys are deliberately not committed | — |
| Conflicts, funding, ethics | Present | — |

### Citation verification detail

| Reference | Field that needed checking | Source used |
|---|---|---|
| Yun et al. | Full author list | OpenAlex record for `10.1145/3538644` |
| Bley et al. | Venue | CISPA repository named the published DOI; OpenAlex gave ACM CCS 2025 |
| Yu et al. (MQTT-L) | Full author list | Springer `citation_author` metadata, not the truncated display list |
| Behnke 2020, 2022, 2023 | Authors, venue, DOI | OpenAlex, all three confirmed as cited |

The ACM Digital Library and SCImago are both behind bot verification. **That was not
circumvented.** Each field was resolved from an independent authoritative source instead.

## Blocking

| # | Item | Why it blocks | What it needs |
|---|---|---|---|
| B1 | **Physical timing measurement (conditions A–C)** | The title and central claim assert timing isolation; no latency has been measured. Two of three simulated reviewers require this | Two ESP32 boards and a logic probe. Protocol, firmware, wiring, scripts and pre-registered statistics are all written |
| B2 | **Venue decision, which depends on B1** | If the measurement will not happen, the paper must be retitled and reframed around the claim the evidence supports. Submitting the current framing without the measurement has a poor expected outcome | A decision, not work |

## Not blocking, but a reviewer will raise them

| # | Item | Effort |
|---|---|---|
| N1 | The compile-guard finding rests on $n = 1$. A survey of open-source embedded MQTT projects, or a static-analysis rule over a corpus, would make it a result rather than an anecdote. **This is the highest-value item that needs no hardware** | days |
| N2 | Promote the owner-lockout result; it is underplayed relative to its novelty | hours |
| N3 | Harness correctness rests on inspection plus four documented corrections. Metamorphic or differential testing would strengthen it | days |
| N4 | No trace conformance between the TLA+ model and the firmware | days |
| N5 | Static assertion binding `CMD_DRAIN_PER_PASS` to the queue capacity | minutes |
| N6 | Abstract is 432 words, long for most journals | minutes, once the venue is known |
| N7 | Broker testbed is loopback with a private CA; no wildcards, bridged brokers or client certificates | hours |

## Cannot be resolved from here

| Item | Why | Who |
|---|---|---|
| **JSA Scopus quartile** | SCImago is behind Cloudflare bot verification, which was not bypassed. The repeated "Q2" assumption remains **unverified**, and the journal's metrics (CiteScore 9.1, Impact Factor 5.3) point to Q1 | Open scimagojr.com in a normal browser, or check Scopus/JCR through the institution. Two minutes |
| **JSA Guide for Authors** | Not exposed in the fetched pages; article types, length limits, structured-abstract rules and reference style are unread | Author, from the journal's submission site |
| Plagiarism or similarity check | Requires licensed tooling | Institution |
| Supervisor review | — | Dr. Zaveri |
| Hardware measurement | No hardware, and the author has said he will not perform it | Another laboratory, using the published framework |

## Verdict

**Not ready to submit.**

Everything that can be verified from here has been verified, and the manuscript is in good
shape as a document: the numbers reconcile against the raw data, the references check out, the
claims are scoped, and three of the paper's findings are defects in its own work that the paper
discloses rather than hides.

But the paper is titled after a property it has not measured, and that is not a presentational
problem. There are exactly two honest routes:

1. **Get the measurement.** Two boards and a probe. Everything else is already written, and
   with conditions A–C in hand the paper matches its title and B2 resolves itself.
2. **Change the claim.** Retitle and reframe around the thesis the evidence does support — that
   asserted properties go unchecked, and cheap methods falsify them — and pursue N1 so that the
   compile-guard finding generalises beyond this codebase. This needs no hardware and yields a
   publishable paper.

What should not happen is submitting the current framing to a journal of this standing and
hoping the reviewers do not ask. They will ask; two of the three simulated reviewers asked
first.
