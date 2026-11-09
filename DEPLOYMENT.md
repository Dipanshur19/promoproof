# PromoProof: GitHub and Hugging Face deployment handoff

This handoff contains generic application source and an original synthetic story.
It excludes Git history, credentials, confidential input scripts, research PDFs,
reviewer JSON/CSV/ZIP outputs and source-derived walkthrough examples. Preparing
these files does not create or publish a GitHub repository or Hugging Face Space.

## Recommended deployment

Use a private GitHub repository for version control and a private Hugging Face
Docker Space for the React/Express/Python runtime. GitHub Pages is not a suitable
standalone host for this application's Python worker.

The Dockerfile builds the frontend and Node server, installs Python in a virtual
environment and runs the same-origin application on port 7860 as UID 1000.
README frontmatter declares `sdk: docker` and `app_port: 7860`; Hugging Face
documents that configuration and runtime secrets as environment variables in its
[Docker Spaces guide](https://huggingface.co/docs/hub/spaces-sdks-docker).

The app has no authentication. Keep the keyed Space private and arrange reviewer
access through your Hugging Face account or organization. Do not make a keyed
Space public based on its in-memory limits: two concurrent workers and 20 runs
per IP per 30 minutes are prototype safeguards, not reliable abuse prevention.
Behind shared proxies, multiple users may share the same apparent IP.

## Start locally

Extract the source ZIP and open its `promoproof` folder. Node 20.19+ and Python
3.11+ are required; the image uses Node 22 and Debian's Python 3.11.

```sh
npm ci
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m unittest discover -s tests -v
npm run check
npm run build
python scripts/smoke.py
npm start
```

Open `http://localhost:5000`. On Windows, activate with
`.venv\Scripts\Activate.ps1`; running the application in Docker avoids shell and
Python-path differences. Rules-only mode needs no provider key.

For local AI, copy `.env.example` to `.env` and fill the appropriate server-side
values using your editor. Never paste the filled file into chat or commit it.
Configure keys before starting the server; restart after changing them.

## Create a private GitHub repository

The following commands are intended for you to run after reviewing the source.
They publish the application to your account; they have not been executed here.
The GitHub CLI must already be authenticated.

```sh
git init
git branch -M main
git add .
python scripts/release_bundle.py --check-only
git commit -m "Initial PromoProof deployment handoff"
gh repo create promoproof --private --source=. --remote=origin --push
```

If the repository name is taken, choose another name. Do not import the earlier
confidential reviewer-output ZIP or copy it anywhere inside this repository.
The source checker is a useful guardrail, not a complete secrets/DLP audit.
Review `git diff --cached` and the file list before the first push.

The CI workflow runs unit tests, type checking, production build and a synthetic
HTTP smoke test, then separately builds and smoke-tests the container. It does
not call a model or require production credentials.

## Create and populate the Hugging Face Space

In Hugging Face, create a new Space under your account or organization, select
Docker and a blank template, and choose private visibility. Choose available CPU
hardware appropriate to your account; no local GPU is used because inference
is remote. Verify current hardware pricing and availability in the account UI.

From the initialized local source repository:

```sh
python -m pip install -r requirements-deploy.txt
hf auth login
python scripts/push_space.py YOUR_ACCOUNT/promoproof
```

Enter your token only in Hugging Face's own login prompt. Alternatively, use
`HF_TOKEN` from your local secret manager. The uploader refuses a public or
non-Docker target, adds/updates approved tracked source files, does not force-push
or delete unrelated files, and excludes GitHub workflows. It does not create the
Space, configure keys, change visibility or grant reviewer permissions.

The build starts from the uploaded Dockerfile. Wait for Running in the Space UI
and inspect build/runtime logs if it fails. Do not put real scripts in an upload
until privacy and reviewer access have been checked.

## Configure runtime secrets

Use the Space's Settings to add secrets rather than committing a `.env` file.
Runtime secrets become environment variables as documented by
[Hugging Face](https://huggingface.co/docs/hub/spaces-sdks-docker).

| Setting | Location | Purpose |
|---|---|---|
| `GROQ_API_KEY` | Space secret | Groq inference |
| `OPENAI_API_KEY` | Space secret | Optional OpenAI-compatible provider; omit if unused |
| `OPENAI_BASE_URL` | Space variable | Optional compatible endpoint; omit if unused |
| `PROMOPROOF_MODEL` | Space variable | Default compatible-provider model; e.g. `openai/gpt-oss-120b` |
| `PORT` | Already in Docker image | 7860; keep aligned with README `app_port` |
| `HF_TOKEN` | Local login or GitHub environment secret | Upload source only; not needed inside the app |

The UI selects Groq when only Groq is available and initializes its model to
`openai/gpt-oss-120b`. For a different model, select the provider and enter the
model ID in Model & run settings; the Groq UI initialization currently does not
read `PROMOPROOF_MODEL`. Model availability and JSON/schema compatibility still
require a real smoke test with the interview provider.

Do not copy the sandbox's `CUSTOM_CRED_*` proxy variables. They are not portable
credentials for an independent host. Supply your own provider keys.

## Optional manual deployment from GitHub Actions

Create a GitHub environment named `huggingface`, add `HF_TOKEN` as its secret,
and configure an approval rule if available to your account. Use a fine-grained
token limited to the intended Space's write access.

Run the workflow named “Manually deploy to private Hugging Face Space” and enter
`OWNER/SPACE`. It runs only when manually dispatched, not on every push.
Run the validation workflow first and deploy only a reviewed passing commit.
Provider keys stay in Hugging Face settings, not in GitHub build arguments.

## Docker verification and rollback

These commands run the container without model credentials:

```sh
docker build -t promoproof:local .
docker run -d --name promoproof -p 127.0.0.1:7860:7860 promoproof:local
python scripts/smoke.py --url http://127.0.0.1:7860
docker rm -f promoproof
```

For local keyed execution, use a reviewed runtime `--env-file .env`; never use a
build argument for keys. The host port is loopback-bound in the example to avoid
accidental LAN exposure.

For rollback, check out a known-good source commit and rerun the uploader, then
rebuild/restart the Space. Because uploads do not delete unrelated files, remove
any genuinely obsolete files deliberately through the Space UI after review.
Never use force-push as an automatic recovery procedure.

## Interview readiness checklist

- Confirm the independent Space is Running and the interviewer can open it
  using the intended access permissions; test from another authorized account.
- Keep an offline local checkout, dependencies and rules-only path ready.
- Verify `/api/status`, a fresh synthetic rules run and all three exports.
- Configure Kuku's key only in server-side secrets and restart the app.
- Run a small authorized synthetic AI test with the exact provider/model. Do
  not infer model compatibility merely from a successful rules-only run.
- Authorize confidential excerpt processing only after provider/data-use review.
- For an unseen pack, show the parse audit and actual mode; never relabel a
  partial AI run as complete.
- Explain that saved results are saved, not a fresh live run. Full inference can
  take several minutes under quota backoff; the server caps runs at ten minutes.
- Require human footage/cold-viewer review even after the model gate passes.
- Export approved artifacts privately and clear browser state after the demo.
- Rotate/remove temporary provider keys after the interview; keep `.env` and
  confidential data outside Git and the Space repository.

## Verification status

Local checks are recorded in `HANDOFF_VERIFICATION.md` in the accompanying
handoff, with completed checks distinguished from pending Docker/hosted checks.
Preparing this handoff does not establish that GitHub Actions or a Space build
has run. Docker image bases and unpinned npm version ranges must be periodically
reviewed; `package-lock.json` and `requirements-lock.txt` capture dependencies,
but image tags are not digest-pinned and no production security audit is claimed.
