# Submission package, ethics compliance and final QA

Phases 16, 17 and 19. What exists, what a journal will ask for, what is still missing, and the
cover letter.

**Status: the package is complete except for the experiments.** See §4 before submitting
anything.

---

## 1. Publication ethics and originality (Phase 16)

| Requirement | Status | Evidence |
|---|---|---|
| Original writing | **Met** | All text written for this project; no text recycled from another publication |
| Accurate citations, verified records | **Met with two exceptions** | All 14 references resolved against publisher or preprint records (`RELATED_WORK.md` §7). Exceptions: the full author list of Yun et al. could not be confirmed and is cited "et al."; the venue for Bley et al. is cited as "ACM, 2025" with its DOI rather than a named proceedings |
| No fabricated or falsified data | **Met** | Every number regenerates from committed seeds; verified byte-identical (`IMPLEMENTATION.md` §16) |
| No manipulated or misleading images | **Met** | All figures generated from source scripts in the repository; no figure shows data that does not exist (`FIGURES.md`) |
| No plagiarism or duplicate publication | **Met** | Not submitted anywhere. Submit to one venue at a time |
| No inappropriate text recycling | **Met** | The repository documentation and the manuscript share subject matter but were written separately; check overlap with a similarity tool before submission since both are public |
| Permission for reused material | **Not applicable** | No third-party figures, tables or datasets are reused |
| Dataset and software licensing | **Met** | MIT licence, author-owned. No third-party datasets. Arduino libraries are dependencies, not redistributed |
| Author order and contributions | **Met** | Single author; CRediT statement in the manuscript |
| Conflict of interest and funding | **Met** | Both declared in the manuscript: none |
| AI-assisted tool disclosure | **Met** | Declared in the manuscript. Check the target journal's exact wording requirement, which differs between IEEE, Elsevier and MDPI |
| No invented reviewers, affiliations, funding or approvals | **Met** | None suggested or claimed |

### 1.1 On similarity checking

Run a similarity check before submission to find citation gaps and accidental overlap, not to
tune a percentage. Two specific risks for this project:

1. **Self-overlap with the public repository.** `IMPLEMENTATION.md` and `ARCHITECTURE.md` are
   public and cover the same material. A similarity tool will flag this. It is not plagiarism —
   it is the author's own preprint-like material — but be ready to say so, and cite the
   repository in the manuscript (already done, in Code Availability).
2. **Standard technical phrasing.** Descriptions of HMAC, SHA-256 and MQTT will resemble other
   papers. Normal and acceptable.

No similarity score can be promised, and no report guarantees originality.

### 1.2 Research ethics specific to this work

The project studies an attack. Three standing rules, already enforced in the repository and
stated in the manuscript:

- **No attack tooling is published.** `experiments/hardware/README.md` deliberately omits
  attack-generation procedures.
- **No third-party system is targeted.** Every result so far comes from host simulation of the
  author's own firmware.
- **Condition D requires authorisation.** Radio-layer stress is to be run only on
  experimenter-owned equipment, in an isolated or shielded environment, with institutional
  permission obtained first.

Note that prior work (Kremser and Graffi 2026; Cayre et al. 2023) has already published
ESP32-based deauthentication tooling. That does not change our position: we cite the capability
as evidence that the threat is realistic, and still publish no procedure of our own.

---

## 2. Submission package inventory (Phase 17)

| Item | Status | Location |
|---|---|---|
| Manuscript, journal format | **Partial** | `paper/paper.tex` — compiles standalone; needs reformatting to the chosen journal's template |
| Editable manuscript source | **Ready** | `paper/paper.tex` |
| Separate high-quality figure files | **Ready** | `docs/images/*.pdf` (vector), `*.png` (raster, 2.5× scale) |
| Editable figure sources | **Ready** | `docs/figures/make_diagrams.py`, `experiments/make_figures.py`, hand-authored `*.svg` |
| Tables in editable format | **Ready** | LaTeX source in `paper/paper.tex`; underlying data in `experiments/results/summary.json` |
| Bibliography | **Partial** | Inline `thebibliography` in `paper.tex`. A `.bib` file is needed if the journal requires BibTeX |
| Supplementary material | **Ready** | The repository itself, CI-verified and reproducible |
| Cover letter | **Ready** | §3 below |
| Highlights | **Ready** | §3.2 below |
| Graphical abstract | **Not produced** | Figure 8 (methodology) is the natural candidate; adapt if the journal requires one |
| Title page and author details | **Ready** | In the manuscript |
| Author contribution statement | **Ready** | CRediT statement in the manuscript |
| Funding and COI declarations | **Ready** | In the manuscript |
| Data and code availability statements | **Ready** | In the manuscript |
| Ethics declarations | **Ready** | In the manuscript |
| Copyright and permissions | **Not applicable** | No reused material |
| Submission checklist | **Ready** | §5 below |

### 2.1 Reformatting work required per venue

| Target | Work needed |
|---|---|
| **IEEE Embedded Systems Letters** | Switch to `IEEEtran` (`\documentclass[journal]{IEEEtran}`). The manuscript is currently **5 pages**; ESL's free limit is 4, with US$125 per page beyond and a hard limit of 8. Declarations usually move out of the body into the submission system, which recovers roughly half a page; the remainder would come from trimming Section III or moving the transition table to the repository |
| **JSAN / Computers / Sensors / Electronics (MDPI)** | Switch to the MDPI LaTeX template. These journals expect a fuller article than 5 pages; **do not pad** — expand only once hardware results exist, which will naturally add a results section, figures and discussion |

---

## 3. Cover letter

Addressed to the editor. Replace the bracketed fields at submission.

> Dear Editor,
>
> I submit for your consideration the manuscript "Does Core Pinning Isolate the Safety Function
> on a Single-Chip Wi-Fi SoC?" for publication in [JOURNAL].
>
> Consumer intrusion alarms are now built almost entirely on single-chip Wi-Fi SoCs, where the
> radio driver, the network stack and the safety application share one die, one scheduler and one
> interrupt controller. The standard engineering mitigation is to pin the safety task to its own
> core. That advice derives from a literature studying Linux-class and hypervisor-capable
> platforms, in which the attacked network interface is physically separate from the protected
> core. Whether it still holds when the attacked resource is the chip's own radio driver has not,
> to our knowledge, been measured.
>
> The manuscript makes three contributions. First, it specifies and model-checks the isolation
> argument itself in TLA+: the network task is given no fairness assumption and may stall
> indefinitely, flood, fail or crash, and TLC verifies exhaustively that the safety step remains
> enabled and that the network side never writes alarm state. Both specifications are
> mutation-tested, so the verified properties are demonstrably non-vacuous. Second, it reports a
> 6,000-trial seeded adversarial campaign and a 3,000,000-iteration sanitizer-backed fuzzing
> campaign against the unmodified firmware, with the full artifact public and reproducible to the
> byte. Third, it specifies the measurement protocol for the one claim that cannot be established
> without silicon.
>
> I draw your attention to a limitation stated plainly in the manuscript: the physical timing
> result is not yet measured, and no latency figure is claimed. The paper establishes logical
> isolation and reports the protocol for the timing measurement rather than speculating about its
> outcome. [If submitting to IEEE ESL: I believe this fits the journal's remit of early-stage
> embedded systems research.]
>
> All adversarial work was confined to the author's own simulated system. No third-party network
> or device was targeted, and the manuscript and its public repository deliberately contain no
> attack-generation procedure or tooling.
>
> The manuscript is original, has not been published elsewhere, and is not under consideration by
> any other journal. The author declares no conflict of interest and received no external funding.
>
> Yours sincerely,
> MD Humayun
> M.Tech, Department of Computer Science and Engineering
> Sardar Vallabhbhai National Institute of Technology, Surat, India
> [email] · [date]

### 3.1 Suggested reviewers

Do **not** invent names. If the submission system asks, draw from the authors of the verified
related work in `RELATED_WORK.md` whose expertise genuinely matches — the timing-isolation group
(Fischer et al.; Hoornaert et al.) or the ESP32 security group (Cayre et al.; Kremser and
Graffi) — and only where you have no personal connection that would be a conflict.

### 3.2 Highlights

Five bullets, for journals that require them:

- Formalises the task-isolation argument for a single-chip Wi-Fi SoC in TLA+ and verifies it
  exhaustively with TLC, under a network task given no fairness assumption.
- Both specifications are mutation-tested, demonstrating the verified properties are not vacuous.
- A 6,000-trial seeded adversarial campaign shows command authentication preserves command
  availability under flooding, where an unauthenticated baseline loses it in every flooded trial.
- A 3,000,000-iteration campaign under AddressSanitizer and UndefinedBehaviorSanitizer finds no
  memory-safety defect in the command parser.
- The complete artifact is public and reproduces byte-identically from committed seeds, with
  continuous integration re-running the formal and adversarial checks on every commit.

---

## 4. The submission gate

**Do not submit before closing these.** From `PEER_REVIEW.md` Part G.

| # | Item | Why it blocks |
|---|---|---|
| 1 | **Run hardware conditions A-C** | The paper poses a question it does not answer. This is the one item that changes the outcome |
| 2 | Resolve the two unverified citation fields | A reviewer who checks will find them |
| 3 | Decide the venue and reformat to its template | Wrong format risks desk rejection |
| 4 | Verify the chosen journal's quartile against Scopus Sources | Our quartiles are publisher-stated, not independently confirmed (`JOURNAL_TARGETS.md` §1.2) |
| 5 | Run a similarity check | Expect repository self-overlap; be ready to explain it |
| 6 | Supervisor review and approval | Dr. Zaveri should approve the venue and the claims before submission |

Items 2-6 are a day's work. Item 1 needs two ESP32 boards and a logic probe.

---

## 5. Final QA checklist (Phase 19)

Verified on 6 November 2026 at commit `289638e` unless noted.

| # | Check | Result |
|---|---|---|
| 1 | Architecture elements cross-checked against source | **Pass** — traceability matrix, `ARCHITECTURE.md` §1.1 |
| 2 | Hardware and software details verified against evidence | **Pass** for the host environment and compiler-reported build sizes. Target hardware is specification, not measurement, and is labelled as such |
| 3 | State transitions verified | **Pass** — 11-row transition table built by reading `tickSafety()`, `setState()` and the boot path |
| 4 | Event flows verified | **Pass** — delivery guarantee established as at-most-once from the QoS 0 publish path |
| 5 | Command execution sequence verified | **Pass** — core split confirmed in source |
| 6 | Mathematical notation and pseudocode checked | **Pass** — HMAC, deauth predicate, fusion windows and Mann-Whitney formulation checked against implementation |
| 7 | Key experiments reproduced | **Pass** — full pipeline re-run; `summary.json`, `summary.md` and `fuzz.json` byte-identical |
| 8 | Raw data, scripts, metrics and plots verified | **Pass** — results regenerate from seeds; figure palette validated |
| 9 | Citations and DOIs checked | **Pass with two exceptions**, recorded in §1 |
| 10 | Journal indexing and quartile claims verified | **Partial** — publisher-stated only; SCImago and Scopus Sources unreachable here. Steps to finish in `JOURNAL_TARGETS.md` §1.2 |
| 11 | Figure resolution, captions and formats | **Pass** — SVG, PDF and 2.5× PNG for all 10 figures, captions in `FIGURES.md`, greyscale-safe conventions documented |
| 12 | README links, image paths and commands validated | **Pass** — see §5.1 |
| 13 | Repository structure and documentation consistent | **Pass** |
| 14 | Publication ethics, licensing and disclosures | **Pass** — §1 |
| 15 | Unresolved issues tracked | **Pass** — §4 and `PEER_REVIEW.md` Part H |

### 5.1 Known inconsistencies, all resolved

| Found | Resolution |
|---|---|
| `smart_home.ino` header said v2.1.0 while `FW_VERSION` was 2.2.0 | Fixed, commit `5e1e2f1` |
| `EVALUATION.md` said the literature survey was outstanding | Fixed, commit `5e1e2f1` |
| `state_machine.svg` said "remote DISARM is refused", untrue since v2.2 | Fixed |
| Methodology figure arrows implied the four evidence routes were sequential | Fixed — they now fan out from a shared bus |
| `experiments/README.md` claimed ≈5 min runtime; the real figure is much longer | Documented in `IMPLEMENTATION.md` §9.4 |

### 5.2 Required user inputs still outstanding

| Input | Needed for |
|---|---|
| Two ESP32 DevKit boards and a logic probe | Hardware conditions A-C |
| Institutional permission and an isolated RF environment | Hardware condition D (optional) |
| Supervisor decision on venue | Reformatting |
| Confirmation that an MDPI venue is departmentally acceptable | If choosing JSAN, Computers, Sensors or Electronics |
| Scopus Sources check | Confirming the quartile claim |
| Email address and date for the cover letter | Submission |
