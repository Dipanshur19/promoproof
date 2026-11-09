# PromoProof: deployment handoff verification

Prepared November 5, 2026. This record distinguishes local verification from
deployment steps that have not run. No GitHub repository or Hugging Face Space
was created, uploaded, published or configured while preparing this handoff.

## Completed checks

| Check | Result and scope |
|---|---|
| Clean Python dependency installation | Installed the declared application requirements in a separate virtual environment and froze exact versions into `requirements-lock.txt`; OpenAI SDK 2.54.0 |
| Python dependency consistency | `pip check` reported no broken requirements before installing optional deployment tooling |
| Unit tests | 46 passed: 36 engine tests and 10 handoff/uploader safety tests |
| TypeScript | `npm run check` passed |
| Production build | `npm run build` passed |
| Production HTTP smoke | A separately started production Node server served the frontend and `/api/status`, spawned the Python worker, and returned mechanically valid proposals for an original synthetic fixture; rules-only mode, no model requests |
| Malformed-request privacy | The production smoke test also requires a generic 400 response for malformed JSON and checks that its synthetic private marker is absent from captured server logs; the template's exception-object logger was removed |
| Clean source export | Exported and extracted a source-only ZIP into a separate directory; fresh `npm ci`, type check, production build and production HTTP smoke all passed there |
| GitHub workflow YAML | Both workflow files parsed locally; this is syntax checking, not an actual GitHub Actions execution |
| Hugging Face SDK contract | Installed uploader SDK 1.33.0 and checked Docker/private metadata fields plus in-memory byte-content commit operations offline |
| Upload safety policy | Tests confirmed refusal of public/non-Docker targets and omission of GitHub workflows from a Space upload |
| Source export guardrails | Tests covered environment files, archive files, unknown root files, recognizable credential patterns, reviewer-run JSON and symlinks |

Local runtime: Node 20.20.2 and Python 3.14.8 on Linux. Docker and CI target
Node 22 / Python 3.11. Those target runtimes were not executed locally.

## Pending checks before claiming a hosted deployment

- Docker image build and container smoke: no Docker or Podman engine is
  available in this sandbox. A separate CI job and local commands are supplied.
- GitHub Actions execution: requires pushing to the user's reviewed repository.
- Real private-Space upload/build/startup: requires user authentication and an
  existing private Docker Space.
- Provider inference with the packaged OpenAI SDK 2.54.0: this handoff used
  offline/mock and rules-only checks, not a new model call. Earlier saved Groq
  results are not proof of inference on this newly packaged runtime.
- Interview-key/model swap and authorized reviewer access: validate on the
  actual independent host, with a small authorized synthetic input first.
- Production security review, load testing and public-access authentication.
  The included source checker is not a complete secret scanner or DLP system.

## Contents and confidentiality

The ZIP contains generic tracked source and documentation only. It does not
contain Git history, node_modules, built output, virtual environments, saved
credentials, the uploaded assignment scripts, source-derived reviewer outputs
or the confidential walkthrough examples. The original synthetic application
fixture and synthetic unit-test fixtures are intentionally included.

Optional upload tooling has its direct SDK version pinned; its transitive
dependencies and Docker image tags are not fully reproducible snapshots.
`package-lock.json` and the application `requirements-lock.txt` are included.
Native image construction and dependency security still require review.
