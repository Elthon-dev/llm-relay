# llm-relay

Run a real LLM on **GitHub's servers for free**, tunnel it out with cloudflared,
and point the Bruh-Bot Browser Pilot userscript at it. No GPU, no VPS, no RAM
budget on your phone.

```
userscript  ──HTTPS──▶  *.trycloudflare.com  ──▶  auth proxy :8081  ──▶  Ollama :11434  ──▶  qwen2.5:7b
                 │                     │                        │
             Bearer RELAY_TOKEN    quick tunnel            OpenAI /v1 API
```

## How it works

`.github/workflows/serve-llm.yml` boots an Ubuntu runner, installs Ollama,
pulls a 7B model, fronts it with a tiny auth proxy (`proxy.py`), opens a
`cloudflared` quick tunnel, then parks in a health-monitor loop for ~5h50m.
A cron fire every 6 hours starts the next runner before the old one dies.

The current public endpoint is committed to `endpoint.txt` on every run, so you
can always read it back.

## Setup (one time)

```bash
# 1. make a strong shared secret
TOKEN=$(openssl rand -hex 24)

# 2. store it as the repo secret the proxy checks
gh secret set RELAY_TOKEN -R Elthon-dev/llm-relay --body "$TOKEN"

# 3. save it locally too, for the helper + the userscript API-key field
echo "$TOKEN"   # <- paste this into Bruh-Bot → 🔑 Settings → API Key
```

## Use

```bash
# start a relay (default model qwen2.5:7b)
gh workflow run serve-llm.yml -R Elthon-dev/llm-relay

# or pick a model
gh workflow run serve-llm.yml -R Elthon-dev/llm-relay -f model=qwen2.5:3b

# wait ~3-5 min for the pull, then:
./get-endpoint.sh
```

Then in **Bruh-Bot → 🔑 Settings**:

| Field | Value |
|---|---|
| API Key | your `RELAY_TOKEN` |
| API endpoint | the printed `…/v1/chat/completions` URL |
| Model | `qwen2.5:7b` |

## Honest limits

- **CPU only.** ~3-8 tok/s on a 7B Q4. Fine for an agent, slow for chat.
- **6h job cap.** Cron relaunches; expect a small gap between runs.
- **URL changes** if the tunnel restarts (or every ~6h). Re-run `get-endpoint.sh`.
- **Public URL.** Obscure + token-gated, but don't hammer it from elsewhere.
- **ToS:** GitHub's Acceptable Use Policy discourages using Actions as general
  compute. Keep it modest, keep the repo real, don't be surprised by a flag.
- **Scheduled workflows pause after ~60 days** of repo inactivity — push a
  commit or re-dispatch to revive.
