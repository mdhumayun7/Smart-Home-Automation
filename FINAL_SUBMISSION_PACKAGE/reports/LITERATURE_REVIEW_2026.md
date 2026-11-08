# Literature review, 2026

Targeted review conducted for this revision. Its purpose is to validate or refute the novelty
claim, not to pad the bibliography.

**Verification rule applied to every entry below.** Title, authors, year and venue were read from
the publisher's or repository's own page, not inferred from a search-result snippet. Where a DOI
was not visible on a page actually retrieved, **no DOI is asserted**. Where only the title and a
partial abstract were accessible, the entry says so and the methodological detail is attributed to
whatever source supplied it. **Nothing here was cited from its title alone.**

Searches were run against general academic indexing across IEEE, ACM, Springer, ScienceDirect,
MDPI, NDSS and arXiv. Several targets were not retrievable in this environment; those are recorded
in §6 rather than silently omitted.

---

## 1. Configuration-level security assumptions

### 1.1 Paixão, Santos, Silveira Neto, Menasche, Figueiredo and de Almeida (2026)

- **Title:** Automated Detection of Configuration-Specific Security Vulnerabilities via Patch
  Analysis
- **Venue:** *Proceedings of the ACM on Software Engineering*, vol. 3, FSE, Article FSE119,
  July 2026. Received 2026-02-24, accepted 2026-03-24.
- **DOI:** not visible on the retrieved document; **not asserted**.
- **Read:** full text retrieved and read, including method, corpus and results.

**What it does.** *PatchLens*, a purely static tool, parses security-patch hunks into ASTs with
Tree-sitter, derives presence conditions from surrounding preprocessor guards, resolves file
inclusion through project-specific build-system resolvers, and emits a Boolean *Vulnerability
Impact Condition* over configuration options. It explicitly targets **compile-time variability**
— `#if`/`#ifdef` and build logic such as Kbuild, Autotools and FFmpeg's Make rules — rather than
runtime configuration files. No variants are compiled.

**Scale and results.** 1,192 Linux kernel, 289 FFmpeg and 100 PHP security patches. Analysis
succeeded for 88.67%, 96.88% and 68% respectively. Manual review of 500 sampled conditions found
no incorrect conditions and 5.4% conservative over-approximations. Conditions are compact: 1.84
variables on average for Linux. Tautological conditions — vulnerabilities present in every
configuration — are rare: 6.24% of Linux patches, 39.70% of PHP, none for FFmpeg. CVE descriptions
name a required option in only about 1.50% of cases.

**Relationship to this work.** This is the closest prior work on the configuration dimension and
it is a strong paper, so the distinction matters. PatchLens answers *which configurations contain
code already known to be vulnerable*, taking a patch or CVE as input. It does not assess whether
the security inference encoded in a guard is itself sound — the paper's own example, a
vulnerability gated by `CONFIG_IP_SCTP`, concerns where vulnerable code is reachable, not whether
the guard's reasoning is valid. And its corpus is the Linux kernel, FFmpeg and PHP; no embedded
firmware.

**The gap this leaves.** The defect studied here has no CVE and no patch, because nobody had
questioned the inference. A guard that *grants* a security property on unsound grounds is
invisible to a patch-driven method: there is no patch until someone notices. That is the
complementary question, and it needs a different instrument — in this case an ablation that
measures the safety cost.

### 1.2 Ghazi Asgar and Reddy (2025)

- **Title:** Analysis of Misconfigured IoT MQTT Deployments and a Lightweight Exposure Detection
  System
- **Authors:** Seyed Ali Ghazi Asgar, Narasimha Reddy (Texas A&M University)
- **Venue:** Workshop on Security and Privacy in Standardized IoT (SDIoTSec) 2025, co-located with
  NDSS, San Diego, 24 February 2025
- **DOI:** 10.14722/sdiotsec.2025.23010
- **Read:** full text retrieved.

**What it does.** Measures MQTT brokers that accept connections with no username or password,
combining a GitHub repository review (≥ 900 stars, ≥ 10 Shodan records) with Shodan exposure
counts, plus a proof-of-concept ESP32 detector (~250 lines C, ~230 lines Python) validated against
one self-hosted Mosquitto broker. Ten repositories across home automation, camera, tracking and
energy management. Reports ~500,000 devices on open port 1883 returning connection code 0; Tasmota
1,225 and Home Assistant 1,221 exposed instances; normalised exposure highest for tracking at
6.85% against 2.91% for home automation.

**It explicitly defers access control lists, rate limits and other misconfigurations to future
work**, and performs no static analysis of firmware, source code or build configuration — GitHub
is used only to rank repositories by popularity.

**Relationship to this work.** Complementary and non-overlapping. They measure *deployed* broker
posture at internet scale; this work examines *source-level* configuration reasoning in one
firmware artefact and the ACL behaviour they defer. Their scale is a strength this work does not
have; their lack of any actuation or safety outcome is a limit this work does not share.

### 1.3 Radwan and Sheldon (2026)

- **Title (published):** Experimental Quantification of Authentication Enforcement Correctness and
  ACL Misconfiguration Impact in Standards-Compliant MQTT Deployments
- **Venue:** *Applied Sciences*, vol. 16, no. 7, Article 3583, published 7 April 2026
- **DOI:** 10.3390/app16073583
- **Read:** title, authors, volume, issue, article number, DOI and the opening of the abstract
  were read from the publisher's issue page. **The full text was not retrievable in this
  environment.**

**Caveat that must travel with this citation.** Methodological detail below comes from a
Preprints.org manuscript by the same authors (202601.2125.v1) titled *"Experimental Evaluation of
MQTT Authentication Mechanisms: Reliability, Enforcement Accuracy, and Security Implications"*.
The subject matches and the authors match, but **the title differs, so the identity of the two
documents is unconfirmed.** The detail is therefore attributed to the preprint, and the published
article is cited only for what was verified from the publisher.

**What the preprint does.** Mosquitto with anonymous access disabled; Eclipse Paho C++ clients
plus Mosquitto CLI; GNU g++ on Ubuntu; two PCs on a local network. Six scenarios — valid
credentials, invalid credentials, certificate authentication, authorised topic access,
unauthorised topic access, improper ACL configuration — each run 10 to 100 times, with summary
tables reporting 100 trials. Metrics: authentication time and success rate, FAR, FRR,
authorisation time and success rate, broker CPU, response time; numeric values are given for
success rates, FAR and FRR only. Username/password succeeded 95/100; certificate authentication
88% in phase 1 and 0/100 in phase 2; FAR approximately 0 throughout; ACL-restricted access
succeeded 97/100 against 78/100 under a default policy.

**Relationship to this work.** This is the nearest neighbour to experiment E6 and the comparison
is the most important one in this review. Four differences are decisive:

1. It does **not** compare broker ACLs against application-layer message authentication as
   alternatives; HMAC does not appear.
2. It does **not** model compromise indexed by *which identity holds which secret*. It defines two
   roles with fixed privileges and does not compromise either.
3. It does **not** touch embedded firmware or build-time configuration.
4. It measures **no safety or actuation outcome** — only authentication and authorisation
   outcomes.

This work's decisive result, the E/E′ pair, is unavailable to that design: it requires the *same
valid signature* to be carried by two different broker identities, which presupposes both an
application-layer MAC and a compromise model indexed by secret. Conversely their FAR/FRR
treatment of certificate authentication is outside this work's scope.

Two internal inconsistencies were noted in the preprint and are recorded for fairness rather than
as criticism of the published version, which could not be checked: a denominator of 105 in one
equation against 100 in the corresponding table, and a "convergence to zero" claim about FAR
resting on zero observed events.

---

## 2. Specification-level assumptions and vacuity

### 2.1 Kupferman and Vardi (2003) — the foundational work

- **Title:** Vacuity detection in temporal model checking
- **Journal:** *International Journal on Software Tools for Technology Transfer*, 4(2), 224–233,
  2003 (online 22 January 2002)
- **DOI:** 10.1007/s100090100062
- **Read:** publisher page, abstract and article metadata.

Defines vacuous satisfaction — a specification holds but part of it never affects the result, the
canonical example being "every request is eventually followed by a grant" satisfied by a system
that never requests. Gives a general method for detecting vacuity and generating *interesting
witnesses* for CTL\* specifications, strengthening the earlier Beer et al. notion by checking
whether every subformula affects the truth value.

**Consequence for this work's claims, stated plainly.** Vacuity detection is prior art of more
than two decades' standing, with later sanity-check and mutation-of-checkers literature on top of
it. **This work contributes no vacuity-detection technique and claims none.** What it reports is a
field instance: a specification of a real embedded artefact, model-checked in continuous
integration on every push, that was vacuous as shipped, and whose vacuity had a specific cause —
the model asserted a build-time configuration assumption instead of parameterising it. Published
vacuity work is largely technique-and-benchmark; an instance tied to a concrete firmware defect
that other methods did catch is a different kind of evidence.

Related prior art identified and not claimed as novel here: Beer, Ben-David, Eisner and Rodeh on
vacuity in ACTL formulas; Kupferman's later work on sanity checks in formal verification;
vacuity analysis by mutation of checkers for property qualification.

### 2.2 Canedo (2026) — a live parallel worth positioning against

- **Title:** Oracles That Cannot Fail: Anchoring and the Expectation That Moves With the Fault
- **Author:** Arquimedes Canedo
- **Status:** **arXiv preprint** arXiv:2608.17214v1 [cs.SE], submitted 17 August 2026. No
  indication of peer review. **Labelled as a preprint wherever cited.**
- **Read:** full text retrieved and read.

**What it does.** Argues that a test oracle whose expected value derives from the system it judges
cannot detect faults that shift measurement and expectation together — *oracle anchoring*. An
oracle is *specification-anchored* if its expected value comes from constants, published
procedures or values outside the mutated code, and *state-anchored* otherwise. Evidence: a
deployed air-traffic-control simulator in TypeScript, property-based temporal testing evaluated by
mutation testing with Stryker; 4 modules, 366 mutants, 12 property suites. Re-anchoring one oracle
on published procedure recovers 8 mutants with no new assertion; state-anchoring a healthy
debounce oracle loses 4. The author acknowledges one system and one author as a limitation.

**Relationship to this work.** A conceptual sibling in a different domain. The vacuous invariant
reported here is an assumption-anchored oracle in exactly Canedo's sense: the TLA+ action encoded
the refusal the firmware was supposed to implement, so the expectation moved with the assumption.
Canedo studies test oracles in application software with mutation testing as the instrument; this
work studies formal-specification vacuity and build configuration in embedded firmware, with an
inverted model-checking configuration as the instrument. Citing it places this work in a current
conversation rather than presenting the observation as unprecedented.

---

## 3. Execution-level assumptions, real-time interference and bounded work

### 3.1 Prior ESP32 interference measurement

The existing bibliography's measurement anchor — single-digit-percent critical-task cycle loss on
an ESP32 under IP-layer load with the network task already on the other core — remains the one
empirical data point for the execution dimension, and it is a **different load class** from the
radio-layer question this work leaves open. No newer ESP32 radio-layer timing measurement was
found in this review.

### 3.2 Bounded-work analysis

Deterministic arrival-curve / service-curve analysis (network calculus, and Real-Time Calculus in
the embedded setting) is a mature field, with recent activity concentrated in TSN and
time-triggered Ethernet rather than in single-chip Wi-Fi SoCs. **This work claims no contribution
to that theory.** It applies the deterministic formulation — chosen precisely because it requires
only an upper envelope on arrivals, which an adversary model can legitimately supply, whereas a
stochastic model would have to be fabricated — to the verified queue capacities and drain bounds
of one firmware artefact. See `docs/MATHEMATICAL_MODEL_AND_PROOFS.md` §4.

### 3.3 What was not found

No work was found that treats response-time decomposition as a **defect-finding** instrument
rather than a certification instrument. That is a narrow observation and it is reported as one: the
derivation here was never completed to a numerical WCET, and it still exposed a real defect because
it required a bound the code did not possess.

---

## 4. Generalisation: static analysis over embedded corpora

### 4.1 Shen, Pillai, Yuan, Davis and Machiry (2025) — the key comparator for RQ5

- **Title:** Finding 709 Defects in 258 Projects: An Experience Report on Applying CodeQL to
  Open-Source Embedded Software (Experience Paper)
- **Venue:** *Proceedings of the ACM on Software Engineering*, vol. 2, ISSTA, Article ISSTA048,
  July 2025
- **DOI:** 10.1145/3728923
- **Read:** extended report retrieved and read, including corpus construction, validation
  procedure and limitations.

**What it does.** Applies CodeQL to open-source C/C++ embedded software. Corpus: GitHub search on
8 April 2023 for original, non-archived C/C++ embedded projects, ranked by stars, top 250, minus 12
manually removed as non-embedded; plus 32 RTOS repositories from osrtos.com with more than 100
stars; de-duplicated to 258. Validation: 123 built repositories sampled as the 50 most-starred, 50
least-starred and 23 random; two trained analysts classified every issue over about a month.
**Overall false-positive rate 34%** (538 of 1,577), concentrated in a few rules.

**Stated limitations.** May not transfer to commercial SAST tools; may not transfer to commercial
embedded software, which may use costlier methods including formal verification; GitHub only; the
developer survey had 25 responses; and **it is a measurement study making no causal claims**.

**Relationship to this work, and why it matters for honesty.** Three points.

1. **Corpus construction is nearly identical in kind** — star-ranked, non-fork, non-archived
   GitHub C/C++ — and they decline population-level claims. That directly supports this work's
   decision to report an existence claim only, from a smaller 135-project convenience sample with
   a 3-star threshold.
2. **Their 34% false-positive rate is the right yardstick for this work's 50% (9 of 18).** A
   roughly half-wrong loose heuristic is in the same range as a mature commercial-grade tool's
   output on this kind of code, which makes the figure unremarkable rather than anomalous — and
   makes the manual adjudication essential rather than optional.
3. **They do not study preprocessor guards or security configuration.** Build configuration
   appears only as an engineering step needed to make CodeQL run. The gap for dimension 1 holds.

Also relevant: their article type is an **Experience Paper** at a top venue. That is a useful
precedent for this work's article type, which is taken up in `docs/JOURNAL_SELECTION_2026.md`.

### 4.2 Other corpus and configuration-extraction work

Work deriving IoT security configurations by static analysis of stripped ARM binaries addresses a
related question — what configuration a shipped binary embodies — from the opposite end of the
toolchain. It was identified but not retrieved in full, and is therefore not cited in support of
any sentence.

---

## 5. The counter-lockout mechanism: a claim this review falsified

Recorded prominently because it caused a claim in this project to be **withdrawn**.

### 5.1 Wara and Yu (2020)

- **Title:** New Replay Attacks on ZigBee Devices for Internet-of-Things (IoT) Applications
- **Authors:** Mohammad Shafeul Wara, Qiaoyan Yu (University of New Hampshire)
- **Year:** 2020 (IEEE copyright line on the accessible copy)
- **Venue:** **unverified.** The retrievable copy carries an IEEE copyright line but names no
  conference, and the publisher record could not be retrieved. Accessible as NSF Public Access
  Repository accession 10215772. **No venue, volume or page range is asserted.**
- **Read:** full text of the accessible copy.

**The relevant passage.** In its introduction the paper describes a denial of service in which an
attacker sets "the device frame counter to a higher than normal value" so that packets with a
lower counter are discarded. The passage has **no citation and no experiment**. The paper's own
contribution runs the other way: it replays captured frames, and it tests counter manipulation
only to see whether a *replay* succeeds — on a Philips Hue bulb, raising a captured turn-off
frame's counter by one, to higher values, and to `0xFFFFFFFF` all failed. It does not test whether
raising the stored counter blocks legitimate commands.

**Effect on this project's claims.** The report previously stated that the authors had not found
the owner-lockout mechanism reported for counter-based replay protection in embedded command
paths. **That statement was false and has been withdrawn.** The mechanism is reported, as
background, for ZigBee frame counters.

What survives, and is now the claim made: the mechanism had not been *measured*; this work measures
it as a **complete** lockout (0 of 1,250 operator commands) arising from a design decision taken
for a defensible reason, and draws the consequence that replay resistance and owner availability
are **coupled** under key compromise rather than independent. Two further searches with different
phrasings found no experimental report of the failure mode, which is why the measurement is still
worth reporting — but the concept is not this work's to claim.

---

## 6. Searches that did not yield a usable result

Recorded so the review's coverage is auditable rather than implied.

| Target | Outcome |
|---|---|
| Full text of Radwan and Sheldon (2026) | publisher full text not retrievable in this environment; method attributed to the authors' preprint with the title caveat in §1.3 |
| Venue of Wara and Yu (2020) | two searches plus two publisher-page fetches failed; venue left unasserted |
| Newer ESP32 radio-layer timing measurement | none found; the existing anchor remains the only empirical data point |
| Scopus / JCR quartile data | the indexing source returned an automated challenge, which was **not** circumvented; see `docs/JOURNAL_SELECTION_2026.md` |
| argXtract full text | identified, not retrieved; not cited in support of any sentence |

---

## 7. Conclusions of the review

1. **The three-dimension gap survives contact with 2026 literature**, and now rests on evidence
   rather than assertion. The closest work on each dimension does something adjacent and
   specifically different: patch-driven configuration mapping without guard-soundness assessment
   (§1.1); deployed-broker posture with ACLs deferred (§1.2); broker authentication enforcement
   without any application-layer MAC comparison, compromise model or actuation outcome (§1.3);
   vacuity as technique rather than as field instance (§2.1); corpus-scale static analysis without
   configuration guards (§4.1).
2. **No technique in this work is novel, and the revision must say so explicitly.** Vacuity
   detection in particular is 20-plus years old and the manuscript must not imply otherwise.
3. **One claim was falsified by this review and has been withdrawn** (§5). That is the review
   working as intended.
4. **The corpus study's honest ceiling is confirmed by the best comparator available.** Shen et
   al. use a larger and better-constructed corpus and still decline population claims; this work's
   smaller sample supports strictly less.
5. **The strongest defensible positioning is a single-system case study with a methodological
   finding**, with the configuration and specification dimensions as the headline and the execution
   dimension as a conditional analytical result plus a published, unexecuted protocol.

---

## 8. Sources

- [Automated Detection of Configuration-Specific Security Vulnerabilities via Patch Analysis](https://arxiv.org/pdf/2606.25863)
- [Analysis of Misconfigured IoT MQTT Deployments and a Lightweight Exposure Detection System](https://www.ndss-symposium.org/wp-content/uploads/sdiotsec25-10.pdf)
- [Applied Sciences, Volume 16, Issue 7 — Radwan and Sheldon article listing](https://www.mdpi.com/2076-3417/16/7)
- [Radwan and Sheldon, Preprints.org manuscript 202601.2125.v1](https://www.preprints.org/manuscript/202601.2125/v1)
- [Kupferman and Vardi, Vacuity detection in temporal model checking](https://link.springer.com/article/10.1007/s100090100062)
- [Canedo, Oracles That Cannot Fail (arXiv preprint)](https://arxiv.org/pdf/2608.17214)
- [Shen et al., Finding 709 Defects in 258 Projects (extended report)](https://arxiv.org/pdf/2310.00205)
- [Wara and Yu, New Replay Attacks on ZigBee Devices](https://par.nsf.gov/servlets/purl/10215772)
- [Sanity Checks in Formal Verification](https://link.springer.com/chapter/10.1007/11817949_3)
- [Vacuity Analysis for Property Qualification by Mutation of Checkers](https://dl.acm.org/doi/pdf/10.5555/1870926.1871041)
- [argXtract: Deriving IoT Security Configurations via Automated Static Analysis of Stripped ARM Binaries](https://arxiv.org/pdf/2105.03135)
- [Network Calculus Results for TSN: An Introduction](https://arxiv.org/html/2508.18855v1)
