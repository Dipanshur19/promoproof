---
title: PromoProof
sdk: docker
app_port: 7860
pinned: false
---

# PromoProof

A working upload-first screenplay-to-promo prototype. Timing and validation are deterministic; optional model ranking and a separate critic produce evidence-linked editorial judgments. No Kuku content is bundled.

## Run locally

Requires Node 20.19+ (Docker uses Node 22) and Python 3.11+.

```sh
npm ci
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-lock.txt
npm run dev
```

Open `http://localhost:5000`. Use the original synthetic demo, or upload the confidential pack at runtime. Rules-only analysis requires no model key.

## Connect a model

Set `GROQ_API_KEY` in the server environment, choose Groq in Model & run settings, enter an available model ID such as `openai/gpt-oss-120b`, and authorize excerpt processing after checking provider privacy/ZDR settings. Free-tier quotas, rate limits and availability apply.

For an OpenAI-compatible provider, configure `OPENAI_API_KEY`, optional `OPENAI_BASE_URL`, and optional `PROMOPROOF_MODEL` on the server. Model changes do not affect parsing or validation. No keys are entered into the browser or committed to source.

Hosted vault proxies use `CUSTOM_CRED_API_GROQ_COM_URL` and `CUSTOM_CRED_API_GROQ_COM_PROXY_AUTH_KEY`; aliases `PROMOPROOF_GROQ_URL` and `PROMOPROOF_GROQ_TOKEN` are also supported. Missing keys, failed bounded retries or invalid evidence produce an explicitly labeled `rules_only` or `partial_ai` run.

## Capabilities and limits

- ZIP/TXT ingestion; bounded decompression with no extraction to disk.
- Full-pack parsing; scene-header mismatches flagged with original event timecodes unchanged.
- Safe 20–60s windows, including overlapping-dialogue checks.
- Impact proxies deduplicated; generic door slams do not qualify alone.
- Diverse continuous cuts plus conservative same-episode compression.
- Cross-episode composition and automatic ambiguous alias merges are not implemented.
- Entity registry, source/quality tabs, notes, human decisions, and audience/format/search filters.
- Complete JSON, spreadsheet-safe slate CSV and raw-log ZIP exports.
- No saved originals, database, authentication, video inspection, or performance prediction.

Mechanical validity does not establish creative quality. Rules-only scores cannot pass the semantic gate. Closing the tab discards unexported review state.

## Tests and build

```sh
python -m unittest discover -s tests -v
npm run check
npm run build
```

## Privacy

Inputs travel to the analysis server and are processed in memory. Optional AI sends excerpts to the configured provider. HTTP logs omit bodies and responses. This is a prototype, not an audited confidential-data service; prefer local mode for sensitive material. Never put private run artifacts in `client/public`.

## Deployment handoff

See [DEPLOYMENT.md](DEPLOYMENT.md) for private GitHub setup, Hugging Face Docker
Spaces, runtime secrets, smoke tests, rollback and the interview checklist.
No repository or Space has been published as part of preparing this handoff.
Use a private Space for a keyed demo: this app has no authentication, and its
in-memory rate limits are not a security boundary.
