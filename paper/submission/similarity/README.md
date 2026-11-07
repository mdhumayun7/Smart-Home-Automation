# Similarity screening — what to upload

**No similarity check has been run, and no similarity percentage is claimed.** This folder
holds the file to submit and the settings to use. The full review done by hand, and what it
found, is in `docs/SIMILARITY_SCREENING_CHECKLIST.md`.

## Upload this

`manuscript-for-similarity-check.pdf` — 31 pages, about 16,750 words of extractable text.

It is a copy of `paper/manuscript.pdf`. **Do not upload the `.tex`**: LaTeX markup inflates the
score with false matches on commands and environment names.

## Settings

| Setting | Value | Why |
|---|---|---|
| Add to repository / store submission | **NO** | If the tool stores it, the publisher's own later Crossref Similarity Check will match the paper against itself. |
| Exclude bibliography | yes | Reference lists match every paper that cites the same work. |
| Exclude quoted material | yes | — |
| Exclude small matches | under ~10 words | Below that, matches are technical vocabulary. |

## Then do this

1. Record the overall figure **before** any manual exclusion.
2. Find and exclude the self-match against `github.com/mdhumayun7/Smart-Home-Automation`.
   The repository is this paper's artefact, authored by the same person. Expect a non-trivial
   match: similarity tools index GitHub, and the repository contains the figures, tables,
   numbers and a README describing the work. Measured verbatim prose overlap with the
   committed documentation is only **0.7 %** of manuscript sentences, so most of any
   repository match will be figures, numbers and identifiers rather than copied text.
3. Record the figure **after** exclusion. That is the one that matters.
4. Read every remaining match above 1 % individually. The percentage is not the finding; the
   matched passages are.
5. Keep the report PDF with the submission package.

## What would be a real problem

- A contiguous passage of 25+ words matching a source that is not quoted and cited.
- A match against a paper **not** in the bibliography.
- A match inside Results or Discussion, where every sentence should be the author's own
  account of the author's own data.
- A match against another author's figure caption or table.

None is expected: the manual review found no verbatim external text anywhere in the body, and
all 22 bibliography entries are cited. But the report is the check, not that review.

## What not to do

**Do not reword technical terminology to lower the score.** `AUTH_COMMANDS`,
`ALLOW_REMOTE_DISARM`, `xQueueReceive`, HMAC-SHA256, Mann–Whitney *U*, Wilson score — these
match because they are the correct terms. Changing them makes the paper worse and reviewers
notice.

## Record the outcome

```
Tool and version:                      ____________________
Date run:                              ____________________
Overall similarity:                    ______ %
After excluding self-match + bibliography: ______ %
Highest single source:                 ____________________  ______ %
Matches above 1 % reviewed one by one:  yes / no
Action taken:                          ____________________
Supervisor sign-off:                   ____________________
```
