#!/usr/bin/env bash
# Shallow-clone every project in corpus.json and record the exact commit analysed.
#
# Clones land in a directory given on the command line, which must be outside this one: the
# cloned code is untrusted third-party input and the analysis scripts must not sit beside it,
# so that no interpreter picks up a module from a cloned repository.
#
# After recording each SHA the .git directory is removed, because the history is not needed
# for the analysis and 135 repositories of it is a lot of disk.
#
# Usage: ./fetch_corpus.sh <dest-dir>
set -uo pipefail
cd "$(dirname "$0")"
HERE="$PWD"

DEST="${1:?usage: fetch_corpus.sh <dest-dir>}"
mkdir -p "$DEST"
case "$(readlink -f "$DEST")" in
  "$HERE"|"$HERE"/*) echo "refusing to clone into the script directory" >&2; exit 2 ;;
esac

python3 -c "
import json, sys
d = json.load(open('corpus.json'))
for p in d['projects']:
    print(p['full_name'], p['clone_url'])
" | while read -r name url; do
  safe="${name//\//__}"
  out="$DEST/$safe"
  [ -d "$out" ] && continue
  if git clone --quiet --depth 1 "$url" "$out" 2>/dev/null; then
    sha="$(git -C "$out" rev-parse HEAD)"
    printf '%s\t%s\n' "$name" "$sha" >> "$DEST/_shas.tsv"
    rm -rf "$out/.git"
  else
    printf '%s\tCLONE_FAILED\n' "$name" >> "$DEST/_shas.tsv"
  fi
done

ok=$(grep -cv 'CLONE_FAILED' "$DEST/_shas.tsv" 2>/dev/null || echo 0)
bad=$(grep -c 'CLONE_FAILED' "$DEST/_shas.tsv" 2>/dev/null || echo 0)
echo "cloned $ok, failed $bad; SHAs in $DEST/_shas.tsv"
