#!/usr/bin/env bash
# Fetch the current llm-relay endpoint + tell you exactly what to paste into
# the userscript. Run from Termux (needs `gh` authed to Elthon-dev).
set -euo pipefail

REPO="${REPO:-Elthon-dev/llm-relay}"
BRANCH="${BRANCH:-main}"

ENDPOINT=$(gh api "repos/$REPO/contents/endpoint.txt?ref=$BRANCH" --jq '.content' 2>/dev/null \
  | base64 -d 2>/dev/null | tr -d '\r\n')

if [ -z "${ENDPOINT:-}" ]; then
  echo "No endpoint.txt yet. Has the serve-llm workflow run?"
  echo "  gh workflow run serve-llm.yml -R $REPO"
  exit 1
fi

echo "Endpoint : $ENDPOINT"
echo "Model    : qwen2.5:7b   (or whatever you dispatched)"
echo "API key  : your RELAY_TOKEN secret"
echo
echo "Quick check:"
curl -s -m 20 "$ENDPOINT" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${RELAY_TOKEN:-}" \
  -d '{"model":"qwen2.5:7b","messages":[{"role":"user","content":"say hi"}],"max_tokens":16}' \
  && echo
