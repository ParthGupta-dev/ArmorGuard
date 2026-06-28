# ArmorGuard — Project Mark 2

**File:** Project_mark2.md
**Sole owner:** Parth. No restricted boundary of any kind applies to him — frontend, backend, agent, governance, demo-target, deployment, all of it is his to read, run, break, and fix. There is no "Sujat's area" or "Kirti's area" left in this project. Every phase below, regardless of layer, is Parth's.

**What this file is:** the single source of truth for what's actually been fixed in code versus what's still open, across all three source documents — `ARMORGUARD_AUDIT_REPORT.md` (static code review), `ARMORGUARD_BUG_FIXES.md` (real docker-log runtime bugs), and `latest_project.md` (the phased rebuild plan). Boxes are checked **only** where the code change was actually made and verified (compiled + tested where possible) in this conversation — not where a plan exists, not where a file was discussed. Where something is partially done, that's stated explicitly instead of checked.

---

## Phase 0 — Runtime bugs from real docker logs (`ARMORGUARD_BUG_FIXES.md`)

- [x] **Bug #1 — Groq dependency missing.** `groq` added to `backend/requirements.txt`. Needs a Docker rebuild on Parth's machine to take effect — code fix is done, deployment step is his.
- [ ] **Bug #2 — Double `http://` prefix.** **Not fixed — not even found.** Every file that touches the target URL was checked (frontend dialog, `isLocalTarget`, `main.py`, `agent.py`, all nine tool files) and none of them prepend a protocol. A debug line was added at the top of `run_scan()` to trace this (`print(f"[DEBUG] target_url at run_scan entry: {target_url!r}")`). **Action needed from Parth:** run a scan, check that log line, report back what it shows — that determines whether the bug is upstream of this repo entirely.
- [x] **Bug #3 — SPA hash fragments not stripped.** One line added at the top of `run_scan()` in `agent.py`: `target_url = target_url.split("#", 1)[0]`.
- [ ] **Bug #4 — Katana no-op result.** **Not fixed — diagnosis in progress.** A diagnostic print of katana's raw stdout/stderr was added to `katana_tool.py`. **Action needed from Parth:** run a scan, send the printed output, and the real parsing fix gets written against what's actually there.
- [x] **Bug #5 — Double `websocket.close()`.** Guarded in `backend/main.py`: `if websocket.client_state.name != "DISCONNECTED": await websocket.close()`. Verified by re-viewing the file after the edit (an earlier version of this edit accidentally deleted the `if __name__ == "__main__":` guard — caught and corrected before delivery).
- [x] **Bug #6 — Unauthorized third-party scans.** Not a code bug. Logged here as a standing rule: never scan a domain without explicit written authorization. No fix to check off; this is on Parth's usage going forward.

---

## Phase 1 — Make ArmorIQ governance real (`latest_project.md` Phase 1)

- [x] **Centralized real governance call.** Rather than wiring `client`/`intent_token` into all nine tool files individually (the original plan, and exactly the pattern that broke last time — two files had it, seven didn't), governance was centralized at `_armoriq_gate()` in `agent.py`, the one chokepoint every scanner and the summary agent's `http_request` tool already passes through. This one change means all nine tools are now actually gated by ArmorIQ, not two.
- [x] **`_armoriq_gate` now calls `armoriq_client.invoke()` for real**, instead of a local `target.rstrip("/") != approved` string comparison. Verified end-to-end against the mock client: an in-scope `nmap` call succeeds, an out-of-scope `http_request` call is genuinely blocked by ArmorIQ's own logic.
- [x] **Hardcoded drift-classification coercion removed** from `_handle_armoriq_block`. The classification shown on screen now comes from whatever ArmorIQ's `invoke()` response actually returns, not a hand-written `if/else` written to make the demo read a certain way.
- [x] **`build_armoriq_plan()` now binds target + scan mode into every step**, and registers `http_request` as a governed action so the summary agent's tool call is evaluated by the real policy engine instead of raising a spurious "action not in plan" error.
- [x] **Dead `client`/`intent_token` parameters removed** from `nmap_tool.py`, `httpx_tool.py` (which had unreachable internal `invoke()` calls — the adapters in `agent.py` never passed those args) and `nuclei_tool.py`, `sqlmap_tool.py` (which accepted but never used them). Governance now lives in exactly one place.
- [ ] **Get a real `ARMORIQ_API_KEY`/`ARMORIQ_AGENT_ID` configured** so at least one demo runs against the actual hosted ArmorIQ service instead of `MockArmorIQClient`. This is a deployment/credentials step — Parth's to do, not a code change.
- [ ] **Automated test asserting `client.invoke` is called once per tool per scan.** Not written. The governance path was verified manually (one-off script run against the mock client in this conversation), not as a committed regression test.
- [x] **Known consequence surfaced, not hidden:** running the real governance path against the demo's prompt-injection scenario now returns `drift_classification: "hallucination"`, not `"prompt_injection"` — because the mock's keyword check doesn't trigger on the demo's actual injected URL. This is the honest result of removing the coercion, not a new bug. If the demo needs to show `prompt_injection` specifically, the fix is a better classifier or a payload that actually trips the keyword check — not re-hardcoding the label.

---

## Phase 2 — Agent-to-agent architecture (`latest_project.md` Phase 2)

- [ ] **Decide the boundary** — separate ArmorIQ service vs. in-process SDK with an auditable contract. **Not decided yet.**
- [ ] Stand up governance behind its own callable boundary.
- [ ] Treat every governance call as a negotiation (allow/block/modify + reason), not a boolean.
- [ ] Log every proposal + decision pair durably, not just blocked ones.
- [ ] Show the negotiation visibly in the demo UI.

**Status: not started.** This is the phase that most directly answers the judge's "should have been agent-to-agent" feedback, and it hasn't been touched yet.

---

## Phase 3 — Tool execution model (`latest_project.md` Phase 3)

- [ ] **Adaptive vs. deterministic tool selection — decision still outstanding.** Parth was asked directly and has not yet confirmed which way to go. Everything fixed so far assumes deterministic stays, per the conservative default stated in `latest_project.md`.
- [ ] LLM-driven tool-calling loop replacing the static `TOOLS_BY_MODE` loop — not built (depends on the decision above).
- [ ] Every adaptive tool choice routed through real governance — not applicable yet (no adaptive loop exists).
- [ ] Retry-with-backoff for transient tool failures — not built. A failed tool still gets marked `0` findings with no retry.
- [ ] Distinct `"error"`/`"skipped"` status separate from `"done"` — not built. A crashed tool and a clean-zero-findings tool still look identical in the UI/logs.
- [x] **Hydra's dead default credential lists wired in.** `_DEFAULT_USERLIST`/`_DEFAULT_PASSLIST` were defined but never used — now written to temp wordlist files and passed via `-L`/`-P` when no `HYDRA_WORDLIST` is configured, with cleanup in a `finally` block. No more single `admin:admin` guess.
- [x] **Unused `client`/`intent_token` parameters swept** from `nuclei_tool.py` and `sqlmap_tool.py` (covered under Phase 1 above — listed here too since it was originally a Phase 3 item).

---

## Phase 4 — Backend hardening (`latest_project.md` Phase 4)

- [ ] Authentication on every backend endpoint — none added. `/scan`, `/report/{scanId}/export`, `/sessions`, and the WebSocket remain open to anyone who can reach the host.
- [ ] CORS locked to known origins — still `allow_origins=["*"]` with `allow_credentials=True`.
- [ ] Mock-vs-real ArmorIQ mode surfaced visibly in the UI — not done.
- [ ] `_active_scans`/`_subscribers` moved out of in-process memory into Redis (or equivalent) — not done; still breaks past a single worker.
- [ ] Rate limiting + full audit logging on `/scan` — not done.
- [ ] Network-layer scope enforcement (not just app-layer consent) — not done.
- [ ] Secrets moved to a managed secret store — not done; still `.env`-based.
- [ ] Multi-tenancy boundaries on Supabase rows — not done.

**Status: not started.** Nothing in this phase has been touched.

---

## Phase 5 — Frontend completion (`latest_project.md` Phase 5)

- [ ] Six orphaned pages (`assets.tsx`, `fixes.tsx`, `history.tsx`, `reports.tsx`, `settings.tsx`, `vulnerabilities.tsx` — 1,279 lines) wired into `App.tsx`'s router and `layout.tsx`'s nav — not done.
- [ ] No-op `useDeleteScan()` hook fixed or removed — not done.
- [ ] Client-side target URL validation in `new-scan-dialog.tsx` — not done.
- [ ] Visible UI for the Phase 2 agent-to-agent negotiation — not applicable yet (Phase 2 doesn't exist).

**Status: not started.**

---

## Phase 6 — Production credibility (`latest_project.md` Phase 6)

- [ ] Confidence scoring / false-positive suppression on heuristic findings — not done.
- [ ] Report integrity (signed PDF/report hash) — not done.
- [ ] Independent penetration test of ArmorGuard itself — not done.
- [ ] Re-run the full audit after Phases 1–5 land and update the audit report to match reality — not done (this file is that update, partially, for Phase 1 and Phase 0 only).

**Status: not started.**

---

## What's actually different right now, in plain terms

Phase 0 and Phase 1 are real, working, verified code changes — not just plans. Three of six runtime bugs are fixed outright (Groq, hash fragments, websocket crash); two need Parth to run a scan and report back what the diagnostic logging shows before they can be closed; one was never a code bug to begin with. Governance went from "decorative" to "actually calling ArmorIQ's policy engine for every tool, every time" — that's the single biggest fix in this whole project, and it's done and tested.

Everything else — agent-to-agent architecture, adaptive tool orchestration, backend hardening, frontend routing, production credibility — is still exactly where it was: planned, not built. None of that is a small job, and none of it should get checked off until it's actually in the code and verified the same way Phase 0 and Phase 1 were.
