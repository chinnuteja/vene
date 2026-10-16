# Groundwork — portable runtime (Linux/macOS)

Date: 16 October 2026. Plan: IMPLEMENTATION_PLAN_PHASES_9-12.md, "Groundwork before Phase 9".

## What changed

- `scripts/platform.mjs` and `tests/e2e/platform.ts` resolve the virtual-environment Python, the LiveKit server and the test Chromium per platform. Every former `.venv/Scripts/python.exe` / `livekit-server.exe` reference now goes through them. Windows paths are unchanged.
- `scripts/setup.sh`, `dev.sh`, `check.sh`, `stop.sh`, `setup-media.sh` and `common.sh` mirror the PowerShell scripts. Setup creates a project-owned Postgres cluster under ignored `.local/pgdata` (scram-sha-256, loopback only), the `bring_vene` and `bring_vene_test` databases, migrations, seed data, contracts and the pinned LiveKit server. In root-only containers the cluster runs as the system `postgres` account, because Postgres refuses to run as root. `stop.sh` stops only the recorded launcher tree after checking its command line.
- `infra/livekit-binary.json` now pins the official v1.13.9 Linux amd64 and arm64 archives by SHA-256 from the release's `checksums.txt`. The existing Windows pin matched that file. The release has no macOS archive; on macOS, setup uses `livekit-server` from PATH (for example Homebrew) and states that it is not checksum-pinned.
- Offline fixture voice: `scripts/synthesize-fixture.py` speaks the same in-memory JSON line protocol as the Windows SAPI helper, using espeak-ng on Linux and `say` on macOS. A missing engine returns `offline_synthesis_failed`; there is no tone or silent fallback. `speech/player.py` selects the helper per platform.
- `scripts/ensure-browser.mjs` prefers Playwright's pinned Chromium. If that revision is not installed and downloads are disabled, it uses an existing Chromium from `PLAYWRIGHT_BROWSERS_PATH` and records the exact executable in `.local/chromium.json`.
- Browser runs now write screenshots and JSON evidence to `.local/evidence` (override with `BRING_VENE_EVIDENCE_DIR`) instead of overwriting committed `docs/qa` files. Promote selected evidence deliberately.

## Defects found and fixed while verifying

1. **WebRTC overlap assertion raced the 100 ms audio batching** (`media.spec.ts`). Receipts advance once per batch. The test asserted overlap as soon as both tracks had any non-silent window, which can happen inside the second track's first batch. The test now waits until overlap is observable, then asserts it; the assertion itself is unchanged.
2. **Owned test-process stop used SIGTERM on POSIX** (`browser-check.mjs`). Uvicorn then waited for open SSE streams past the harness's 10 s limit, the stop reported failure, and every later test saw a stopped API. It now uses SIGKILL, the same abrupt stop as `taskkill /F` on Windows.
3. **Media-server loss used SIGTERM on POSIX** (`tests/e2e/platform.ts`). LiveKit then performs a graceful shutdown, which is a different scenario from the abrupt loss the test simulates. It now uses SIGKILL, like `Stop-Process`. Ownership checks (recorded PID, parent, executable and config) are unchanged.

A filtered re-run also showed that the continuity test depends on the sandbox-execution test creating a booking first. This is an existing order dependency, not a product defect; full runs execute them in order.

## Environment

- Linux 6.18 x64 cloud container, running as root.
- Node 22.22.0, pnpm 11.25.0, uv with Python 3.12.3.
- **PostgreSQL 16.15** (system package). Windows uses the pinned 17.11. The migrations and suite pass on 16; 17 was not exercised on Linux.
- LiveKit server 1.13.9 (checksum-pinned linux_amd64).
- Chromium revision 1194 from `/opt/pw-browsers` (Playwright 1.64 expects 1248, which cannot be downloaded here).
- espeak-ng 1.51.
- Docker CLI present; engine unavailable.

## Results

| Check | Result |
|---|---|
| `scripts/setup.sh --skip-dependencies` (fresh runtime) | Passed; committed contracts and audio fixtures unchanged |
| Backend (pytest, real Postgres) | 144 passed |
| Child-log regression | Passed |
| Contract drift, TypeScript, production build | Passed |
| First full browser run | 16 passed, 7 failed, 4 skipped; failures traced to the three defects above |
| Targeted re-runs after fixes | All previously failing scenarios passed |
| Final full `scripts/check.sh --all` | **Passed**: 144 backend, 23 browser passed, 4 skipped (live-provider gate, 20-trial timing gate, Firefox and WebKit smoke without project-installed browsers) |
| `scripts/dev.sh --mode fixture --production` | Started Postgres-backed API, LiveKit, voice, understanding, office, execution and callback workers; printed `http://127.0.0.1:3000` |
| Browser review of the launcher | Maria via /dev; prepare, visit and follow-up desktop and 390 px mobile. No page errors; only navigation aborts (`net::ERR_ABORTED`); no mobile horizontal overflow; call panel ready with real LiveKit |
| `scripts/stop.sh` | Stopped all 15 owned processes; project Postgres left running as intended |

Skipped browser scenarios are the explicit live-provider and timing gates plus the Firefox/WebKit smoke, which needs project-installed browsers.

## Not verified

- macOS: no host available; `say`, Homebrew LiveKit and the Postgres layout are untested.
- Windows after these changes: no host available in this session. The Windows code paths were left byte-identical except for routing through the helpers.
- Live providers, physical audio and human review remain open, as in Phase 8.
