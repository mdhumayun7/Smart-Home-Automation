#!/usr/bin/env python3
"""Build a reproducible corpus of open-source embedded MQTT firmware projects.

Selection criteria are fixed in this file and applied mechanically, so the corpus can be
rebuilt. Repository contents change, so every entry records the exact commit SHA analysed.

Criteria, applied in order:
  1. Found by one of the GitHub repository searches in QUERIES below.
  2. Primary language C or C++ (embedded firmware, not a Python or JS client).
  3. Not archived. Forks are excluded, because a fork duplicates its parent's code and would
     inflate any prevalence figure.
  4. At least MIN_STARS stars, as a crude filter against abandoned scratch repositories.
  5. Repository size under MAX_KB, to exclude vendor SDK mirrors whose bulk is not the
     project's own code.
  6. De-duplicated by full name across queries.

Writes corpus.json. Does not clone anything; fetch_corpus.sh does that.

Usage: python3 build_corpus.py [--out corpus.json]
"""
import argparse
import json
import os
import subprocess
import sys

MIN_STARS = 3
MAX_KB = 80_000

# Fixed queries. Each targets embedded MQTT firmware from a different angle so the corpus is
# not shaped by a single phrasing. They are recorded verbatim in the output for auditability.
QUERIES = [
    "esp32 mqtt alarm",
    "esp32 mqtt relay control",
    "esp8266 mqtt home automation firmware",
    "arduino mqtt smart home firmware",
    "esp-idf mqtt client application",
    "mqtt door lock esp32",
    "esp32 mqtt garage door",
    "embedded mqtt command topic firmware",
    "esp32 mqtt switch actuator",
    "zephyr mqtt iot firmware",
    "esp32 mqtt sensor node",
    "esp8266 mqtt relay switch",
    "esp32 home assistant mqtt",
    "mqtt firmware actuator control embedded",
    "esp32 mqtt irrigation controller",
    "esp32 mqtt thermostat",
    "esp32 mqtt access control rfid",
    "esp8266 mqtt garage opener",
    "esp32 pubsubclient",
    "mqtt esp32 security system",
    "esp32 mqtt light controller",
    "nodemcu mqtt automation",
]


def search(query, pages=2, per_page=50):
    """Two pages of 50, sorted by stars. GitHub caps search at 1000 results per query."""
    items = []
    for page in range(1, pages + 1):
        out = subprocess.run(
            ["gh", "api", "-X", "GET", "search/repositories",
             "-f", f"q={query} language:C language:C++",
             "-f", f"per_page={per_page}", "-f", f"page={page}", "-f", "sort=stars"],
            capture_output=True, text=True)
        if out.returncode != 0:
            print(f"  query failed: {query}: {out.stderr.strip()[:120]}", file=sys.stderr)
            break
        try:
            got = json.loads(out.stdout).get("items", [])
        except json.JSONDecodeError:
            break
        items.extend(got)
        if len(got) < per_page:
            break
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "corpus.json"))
    args = ap.parse_args()

    seen, kept, rejected = set(), [], {"language": 0, "archived": 0, "fork": 0,
                                       "stars": 0, "size": 0, "duplicate": 0}
    for q in QUERIES:
        items = search(q)
        print(f"{q!r}: {len(items)} results")
        for r in items:
            name = r["full_name"]
            if name in seen:
                rejected["duplicate"] += 1
                continue
            seen.add(name)
            if (r.get("language") or "") not in ("C", "C++"):
                rejected["language"] += 1; continue
            if r.get("archived"):
                rejected["archived"] += 1; continue
            if r.get("fork"):
                rejected["fork"] += 1; continue
            if r.get("stargazers_count", 0) < MIN_STARS:
                rejected["stars"] += 1; continue
            if r.get("size", 0) > MAX_KB:
                rejected["size"] += 1; continue
            kept.append({
                "full_name": name,
                "clone_url": r["clone_url"],
                "default_branch": r.get("default_branch", "main"),
                "stars": r.get("stargazers_count", 0),
                "language": r.get("language"),
                "size_kb": r.get("size"),
                "license": ((r.get("license") or {}).get("spdx_id")),
                "found_by": q,
            })

    kept.sort(key=lambda d: -d["stars"])
    doc = {
        "criteria": {
            "min_stars": MIN_STARS, "max_size_kb": MAX_KB,
            "languages": ["C", "C++"], "exclude_archived": True, "exclude_forks": True,
        },
        "queries": QUERIES,
        "rejected_counts": rejected,
        "n_projects": len(kept),
        "projects": kept,
    }
    with open(args.out, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    print(f"\nkept {len(kept)} projects; rejected {rejected}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
