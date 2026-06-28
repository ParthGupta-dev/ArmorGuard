# ArmorGuard — Latest Project Document (Post-Judge Rebuild Plan)

**File:** latest_project.md
**Owner:** Parth — sole owner of this project and this document. There are no ownership boundaries, no "do not modify without flagging" zones, and no per-person area splits in this file. Every section below (frontend, backend, governance, agent) is Parth's to read, change, and rebuild. Where the original `PROJECT.md` assigned areas to Sujat/Kirti/Kanishk, that division no longer applies here — this is the single owner's working document going forward.

**Audit basis:** This plan is built directly on `ARMORGUARD_AUDIT_REPORT.md` (the full judge-level technical audit of `agent/`, `backend/`, `frontend/`, and `demo-target/`). That audit is confirmed complete as of this writing — it covers governance (ArmorIQ wiring), the agent/tool execution model (hardcoded pipeline vs. LLM-driven, failure handling), the backend (API, WebSocket, concurrency, auth, CORS), and the frontend (routing, live-data wiring, dead code). If you make further changes to the code, re-run the relevant section of that audit before trusting this plan again — it describes the codebase as it was at audit time, not a moving target.

---

## Closing ArmorGuard Gaps

### What the judge actually said
At NeuroX 2026, the judge scored ArmorGuard **7/10** and gave feedback that should be treated as the real scope of work, not a footnote:

- **"This has nothing to do with ArmorIQ — it's just a pentester tool."** That is the single most damaging sentence a sponsor-track judge can say about a project built specifically for ArmorIQ's must-use sponsor track. It means the judge looked at the demo and the pitch and concluded the governance layer wasn't visible, wasn't convincing, or wasn't real enough to register as the point of the project. The audit backs this up at the code level: the real ArmorIQ policy call (`invoke()`) is never executed in the live scan path, the drift classification shown on screen is hardcoded, and the per-tool ArmorIQ hooks exist in only two of nine tool files — and even those two are never reached because the pipeline doesn't pass them the arguments they need. The judge wasn't being harsh. The judge was reading the same gap the audit found.
- **"Suggested an agent-to-agent architecture."** This is the judge telling you, directly, what would have made this a governance project instead of a scanner with a sponsor SDK imported into `requirements.txt`. An agent-to-agent architecture means: ArmorGuard's pentesting agent is *one* agent, and ArmorIQ (or a governance layer built around it) is a *second*, independent agent/service that the pentesting agent must negotiate with before every action — not a function call buried inside the same process that the pentesting agent's own author wrote the policy logic for. Right now, ArmorGuard plays both roles itself: it's the agent *and* it's grading its own homework on whether its actions are safe. A real agent-to-agent design removes that conflict of interest structurally, not just by adding more code to the same file.

### What "closing the gap" means, concretely
Closing this gap is not "add more ArmorIQ comments to the README." It's three things, in order:
1. Make the existing ArmorIQ integration *real* — the SDK's actual policy decision (`invoke`/`invoke_with_policy`) has to be the thing that blocks or allows every tool call, not a string comparison `agent.py` makes on ArmorIQ's behalf.
2. Move toward the agent-to-agent shape the judge asked for — governance as a structurally separate decision-maker the pentesting agent has to call out to and cannot route around, even by accident.
3. Stop calling a hardcoded `for` loop an "autonomous AI agent" until tool selection is actually adaptive — and if it becomes adaptive, every adaptive decision has to go through step 1's real governance call, or the fix to the pitch makes the product more dangerous, not just more honest.

Everything below is organized so you can work through it in order without losing track of what's done.

---

## Phase 1 — Make ArmorIQ governance real (fixes "this has nothing to do with ArmorIQ")

**Goal:** Every tool call in the scan pipeline is actually evaluated by ArmorIQ's policy logic before it runs — not by a local string comparison `agent.py` wrote on ArmorIQ's behalf.

- [ ] Step 1: In `agent/agent.py`, update every `_xxx_run(deps)` adapter (`_nmap_run`, `_katana_run`, `_ffuf_run`, `_arjun_run`, `_httpx_run`, `_nuclei_run`, `_nikto_run`, `_sqlmap_run`, `_hydra_run`) to accept and pass `client=armoriq_client` and `intent_token=deps.intent_token` through to the underlying `run_xxx_scan()` call.
- [ ] Step 2: Give all nine functions in `agent/tools/*.py` the same signature: `(target, scan_id, client=None, intent_token=None, **tool_specific_args)`. Right now nmap/httpx have the hooks, nuclei/sqlmap accept but ignore them, and katana/ffuf/arjun/nikto/hydra don't have them at all — pick the one shape and apply it to every file.
- [ ] Step 3: Inside each tool function, replace the `if client is not None and intent_token is not None:` dead branch with an always-on call to `client.invoke(mcp="agent_tools", action=<tool_name>, intent_token=intent_token, params={"target": target, **relevant_params})`, and let a `PolicyBlockedException`/`IntentMismatchException` propagate up — don't swallow it locally.
- [ ] Step 4: Delete (or fundamentally rewrite) `_armoriq_gate()`'s hand-rolled scope check in `agent.py`. The scope decision belongs inside ArmorIQ's `invoke()` call (real or mock), not in a `target.rstrip("/") != approved` comparison sitting in your own orchestration code.
- [ ] Step 5: Delete the hardcoded drift-classification coercion (the `# [ArmorGuard AI Rewrite]` comment block in `_handle_armoriq_block`). Whatever classification reaches the UI must come from ArmorIQ's response metadata, not from an `if/else` you wrote to make the demo read a certain way.
- [ ] Step 6: Update `build_armoriq_plan()` in `agent/governance/policies.py` so each plan step carries the actual target URL and parameters, not just `{"action": tool_name}`. A policy engine can't evaluate scope against a plan that never recorded scope.
- [ ] Step 7: Get a real `ARMORIQ_API_KEY` / `ARMORIQ_AGENT_ID` configured for at least one demo environment, and rehearse the live block coming from the actual hosted ArmorIQ service — not `MockArmorIQClient`. If you must demo on mock mode, make that fact visible on screen (see Phase 4, Step 2) instead of leaving it invisible.
- [ ] Step 8: Add one automated test that asserts `client.invoke` is called exactly once per tool, per scan, with the correct action name — so Phase 1's fix can't silently regress into the same disconnected state the audit found.

---

## Phase 2 — Move toward agent-to-agent architecture (the judge's actual suggestion)

**Goal:** Governance is a structurally separate decision-maker, not a function call living inside the same process and the same author's code as the thing it's supposed to govern.

- [ ] Step 1: Decide the boundary — does ArmorIQ run as its own service/process that ArmorGuard's agent calls over the network (true agent-to-agent), or does it stay an in-process SDK call but with an explicit, auditable contract (request → decision → response) that's logged and inspectable end-to-end? Pick one and write the decision down in this file before building anything else in this phase — this determines the next four steps.
- [ ] Step 2: If you go with a separate service: stand up the ArmorIQ policy decision behind its own endpoint (even a thin wrapper service is enough for a hackathon-grade agent-to-agent demo), and have `armoriq_client.py` call out to it over HTTP instead of importing policy logic in-process.
- [ ] Step 3: Treat every governance call as a negotiation, not a permission check: the pentesting agent proposes an action with full context (target, tool, params, prior findings); the governance agent returns an explicit allow/block/modify decision with a reason, every time — not a boolean.
- [ ] Step 4: Log every proposal + decision pair to a durable store (you already have Supabase wired up via `database.py` — extend `intent_drift_event`-style logging to cover *every* call, not just blocked ones), so the agent-to-agent exchange itself is the audit trail, not an afterthought.
- [ ] Step 5: In the demo, show the negotiation explicitly — two distinct actors on screen (ArmorGuard's agent proposing, ArmorIQ's agent deciding), not one spinner that occasionally shows a red "blocked" toast. This is the visual proof the judge's feedback is asking for.

---

## Phase 3 — Fix the agent/tool execution model (stop calling a `for` loop "autonomous")

**Goal:** Either make tool selection genuinely adaptive and govern every adaptive choice, or be accurate in the pitch about what's actually running.

- [ ] Step 1: Decide explicitly — adaptive (LLM chooses next tool/action based on results so far) or deterministic (current fixed list per scan mode). Write the decision here. If deterministic stays, update README/PROJECT-level language to stop calling it "autonomous AI agent" and describe it accurately as a governed, ordered pentest pipeline with an LLM-written summary.
- [ ] Step 2 (only if going adaptive): Replace the static `TOOLS_BY_MODE` loop in `agent.py`'s `run_scan()` with a real `pydantic_ai.Agent` tool-calling loop, where each tool result (including failures) is fed back to the model and it chooses the next action from an allow-listed set.
- [ ] Step 3 (only if going adaptive): Every tool choice the LLM makes must go through Phase 1's real `client.invoke()` call before executing — an adaptive agent with no governance on its adaptive choices is strictly more dangerous than the current static pipeline, not an upgrade.
- [ ] Step 4: Add retry-with-backoff (1–2 attempts) for transient tool failures (timeout, flaky network) before marking a tool as failed, in both the adaptive and deterministic case.
- [ ] Step 5: Add a distinct `"error"`/`"skipped"` status, separate from `"done"`, in both the WebSocket event payload and the stored scan/finding rows — a tool that crashed must never look identical to a tool that ran clean and found nothing.
- [ ] Step 6: Fix `hydra_tool.py` — wire in the existing-but-unused `_DEFAULT_USERLIST`/`_DEFAULT_PASSLIST` as the real no-wordlist fallback (current fallback is a single `admin:admin` guess), or delete the dead constants and document that a wordlist is required.
- [ ] Step 7: Sweep every tool file for unused parameters (the `client`/`intent_token` args accepted-but-ignored pattern in `nuclei_tool.py`/`sqlmap_tool.py`) — either wire them per Phase 1 or remove them. An unused security parameter is worse than none, because it reads as governed when it isn't.

---

## Phase 4 — Backend hardening (so this survives contact with the real world)

**Goal:** The backend can run more than a single demo instance without breaking, and isn't trivially abusable.

- [ ] Step 1: Add authentication (API key or session-based) to every backend endpoint — currently `/scan`, `/report/{scanId}/export`, `/sessions`, and the WebSocket are all open to anyone who can reach the host.
- [ ] Step 2: Lock CORS down to known frontend origins; drop `allow_credentials=True` unless it's actually needed (current config — `allow_origins=["*"]` + credentials — is both insecure and likely non-functional per browser spec). While here, surface mock-vs-real ArmorIQ mode visibly in the UI so this is never silently invisible again.
- [ ] Step 3: Move `_active_scans` and `_subscribers` out of in-process Python memory (e.g. into Redis) so the backend can run more than one worker/replica — right now duplicate-scan protection and WebSocket fan-out both silently stop working the moment you scale past a single process.
- [ ] Step 4: Add rate limiting and full audit logging on `/scan` (source IP, consent record, timestamps) beyond what's currently captured.
- [ ] Step 5: Add network-layer scope enforcement (not just the app-layer consent check) so nmap/sqlmap/hydra physically cannot reach hosts outside an approved CIDR — defense in depth beyond a single string comparison.
- [ ] Step 6: Move secrets (`ARMORIQ_API_KEY`, `SUPABASE_KEY`, LLM provider keys) into a managed secret store instead of `.env` files baked into Docker images.
- [ ] Step 7: Add multi-tenancy boundaries on Supabase rows (`scan_id` ownership) so `/report/{scanId}` and `/sessions` can't leak another user's data.

---

## Phase 5 — Frontend completion

**Goal:** Everything that's built is reachable, and nothing reachable lies about what it does.

- [ ] Step 1: Wire the six fully-built but currently unrouted pages — `assets.tsx`, `fixes.tsx`, `history.tsx`, `reports.tsx`, `settings.tsx`, `vulnerabilities.tsx` (1,279 lines total) — into `App.tsx`'s router and `layout.tsx`'s sidebar nav. If any of them are stale and not worth finishing, remove them from the bundle instead of shipping dead UI.
- [ ] Step 2: Implement a real `DELETE /scan/{id}` backend endpoint, or delete the existing no-op `useDeleteScan()` hook — right now it would show a success toast for an action that silently does nothing if any page ever calls it.
- [ ] Step 3: Add basic client-side validation on the target URL field in `new-scan-dialog.tsx` (scheme + format check) before allowing submit, instead of relying entirely on the backend to reject bad input with no immediate feedback.
- [ ] Step 4: Once Phase 2's agent-to-agent negotiation exists, design a visible UI moment for it — this is the most important frontend work in this entire plan, because it's the part of the product the judge's feedback says is currently invisible.

---

## Phase 6 — Real-world / production credibility

**Goal:** This stops being a hackathon demo and starts being defensible as an actual security product.

- [ ] Step 1: Replace heuristic/substring-based vulnerability detection (header-presence checks in `httpx_tool.py`, string matching in `sqlmap_tool.py`'s raw output) with confidence scoring and basic false-positive suppression.
- [ ] Step 2: Add report integrity — sign the PDF/report hash, reusing the signature infrastructure ArmorIQ's intent tokens already depend on.
- [ ] Step 3: Get ArmorGuard itself penetration tested before pitching it as a tool that protects other people's applications.
- [ ] Step 4: Once Phases 1–5 are done, re-run the full audit (or have it re-run) against the rebuilt codebase, and update `ARMORGUARD_AUDIT_REPORT.md` to reflect what's actually fixed versus what's still open — don't let this plan go stale the way `PROJECT.md`'s checklist did.

---

## What this file actually is, in plain terms

This document is the to-do list for fixing ArmorGuard, written after a judge scored the hackathon submission 7/10 and said two specific things: it doesn't really show off ArmorIQ (it just looks like a regular pentesting tool with a sponsor's SDK installed), and it should have been built as two AI agents talking to each other — one that pentests, and one that watches and approves what the first one does.

The audit found exactly why the judge said that: the code that's supposed to ask ArmorIQ "is this action allowed?" mostly never runs. Instead, ArmorGuard checks its own homework with a simple piece of code that just compares two web addresses to see if they match — that's not ArmorIQ deciding anything, that's ArmorGuard deciding and putting ArmorIQ's name on it.

This plan fixes that in order:
1. **Phase 1** makes the ArmorIQ check real instead of fake, for every tool, every time.
2. **Phase 2** restructures things so ArmorIQ acts like a second, independent agent the pentesting agent has to ask permission from — which is literally what the judge asked for.
3. **Phase 3** fixes the part where the project calls itself an "autonomous AI agent" even though it currently just runs a fixed checklist of tools in the same order every time, with no ability to recover or adapt if a step fails.
4. **Phase 4** makes the backend safe enough that it wouldn't immediately break or get abused if more than one person used it at once.
5. **Phase 5** turns on the parts of the website that were already built but never connected to anything — right now about a third of the frontend is invisible to anyone using the app.
6. **Phase 6** is the final polish to make this believable as a real product instead of a demo.

There are no team boundaries in this file anymore — it's all Parth's to work through, in this order, checking off each step as it's actually done in the code (not just written here).
