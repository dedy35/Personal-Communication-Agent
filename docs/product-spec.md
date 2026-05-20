# Product Specification: Personal Communication Agent (Production-First)

## 1. Document Control
- Version: 1.0
- Date: 2026-05-20
- Product: Local Personal Communication Agent
- Deployment model: Local-first on Windows laptop, private remote access from phone/tablet via Tailscale

## 2. Product Vision
Build a reliable personal communication operating system that helps the user understand, prioritize, and draft replies across multiple messaging platforms, with Japanese-to-Indonesian language intelligence and strict human approval before any outgoing send.

## 3. Product Principles (Hard Requirements)
1. Local-first and production-first: the system runs on the user's Windows laptop as the source of truth.
2. Approval-first sending: no outgoing message is allowed without explicit user approval.
3. Translation-first for Japanese communication: translation, intent, nuance, and hierarchy context are core, not add-ons.
4. Safety and auditability over automation speed.

## 4. Hard Safety Rule (Non-Negotiable)
The agent may automatically read, summarize, translate, explain context, draft, and revise drafts.

The agent must never send any outgoing message unless the user explicitly approves the exact message body and target recipient/conversation.

This applies to all platforms (Slack, WhatsApp Web, LINE), all chat types (DM, group, channel), and all message classes (text, follow-up, apology, clarification).

## 5. Users and Access
- Primary user: single owner/operator.
- Device model:
  - Host: Windows laptop (always-on when in use).
  - Clients: phone/tablet browser over Tailscale private network.
- No public internet exposure for dashboard/API.

## 6. Platform Scope
- Phase 1 connector: Slack.
- Phase 2 connector: WhatsApp Web (monitoring/draft-assisted first).
- Phase 3 connector: LINE.
- Cross-platform unified inbox and status model are required from the beginning.

## 7. Core Features

### 7.1 Japanese-to-Indonesian Translation Intelligence
For each relevant Japanese message, provide:
- Original message (unaltered).
- Literal Japanese -> Indonesian translation.
- Real meaning in practical context.
- Tone/nuance classification (for example: neutral, urgent, indirect, formal).
- Hierarchy context (senior/peer/client/friend) and communication implication.
- Expected action recommendation.
- Risk level (Low/Medium/High/Critical).
- Suggested Japanese reply + Indonesian meaning of the draft.
- Assumption notes when context confidence is limited.

### 7.2 Intent Explanation and Nuance Analysis
- Explain what the sender likely wants, why it matters now, and what response style is safest.
- Highlight ambiguity and uncertainty clearly.
- Provide conservative recommendations for high-risk/sensitive threads.

### 7.3 Hierarchy-Aware Drafting
- Generate drafts based on relationship and social hierarchy.
- Support tone presets (business formal, concise polite, friendly, apology, delayed-reply recovery, clarification).
- Every draft must show Indonesian meaning before approval.

### 7.4 Unreplied-Message Tracking
- Track incoming messages requiring response.
- Detect overdue non-replied messages (for example 12h/24h/48h thresholds).
- Track waiting-reply state for messages already sent by user.
- Offer recovery/follow-up draft suggestions only (never auto-send).

### 7.5 Agent Chat
- Natural-language command interface for the user.
- Example intents: "what is urgent today", "explain this thread", "make a safer reply", "show overdue items".
- Agent chat can execute read/analyze/draft actions, but cannot bypass approval gate.

### 7.6 Approval Gate (Mandatory Before Send)
Before any send action, the UI must present:
- Platform and destination identity (user/channel/group).
- Conversation context summary.
- Exact outgoing message body (locked for approval).
- Indonesian meaning/translation of outgoing draft.
- Risk level and sensitive-topic warnings.
- Checklist confirmations (target correct, tone appropriate, no confidential leak, translation reviewed).

Only after explicit user confirmation may the system trigger connector send API.
If draft content changes, approval must reset and require fresh confirmation.

## 8. Functional Requirements
1. System stores messages, drafts, approvals, and audit events in local database.
2. System supports conversation statuses: Need Reply, Draft Ready, Waiting Reply, Overdue, FYI.
3. System computes daily command center summary: urgent, overdue, draft pending, promises/follow-ups.
4. System logs every approval decision with timestamp and approved payload hash.
5. System supports emergency send-stop mode (global send disable).
6. System provides manual correction loop so user feedback improves future drafts.

## 9. Security Constraints
1. Private-network only access through Tailscale; no public dashboard endpoint.
2. Encrypt secrets at rest (connector/session secrets); never store raw credentials in plain text.
3. Use least-privilege permissions for each connector integration.
4. Maintain immutable audit logs for read/analyze/draft/approval/send events.
5. Enforce explicit approval token/state before send execution server-side (not UI-only).
6. Require re-approval when target or body changes.
7. Support local backup and restore with encrypted backup artifacts.
8. Provide retention controls and selective conversation deletion.
9. Respect do-not-store flags for selected contacts/conversations when configured.
10. Disable or hard-block auto-send pathways in code and configuration by default.

## 10. Privacy Constraints
- Data residency is local laptop by default.
- Sync only metadata/content required for product functionality.
- No training-data export from personal communication content without explicit opt-in.
- Optional external LLM use must be transparent and user-controllable per provider.

## 11. Non-Goals
1. Fully autonomous communication agent that sends messages by itself.
2. Public SaaS multi-tenant deployment.
3. Broad social media automation outside Slack/WhatsApp Web/LINE.
4. Voice-call handling/transcription in initial phases.
5. Perfect linguistic certainty; system should surface uncertainty rather than overclaim.
6. Push-notification ecosystem integrations in early build (in-app dashboard first).

## 12. Quality Attributes
- Reliability: stable local operation with recoverable failures.
- Explainability: every recommendation must be inspectable and understandable.
- Safety: approval-first guardrails are more important than speed.
- Mobile usability: dashboard works well on phone/tablet browsers.
- Extensibility: connector and model-provider modules can be added without changing safety core.

## 13. Acceptance Criteria (Release Gate)
1. User can access dashboard from phone/tablet through Tailscale and review all core queues.
2. Japanese analysis output includes translation, intent, nuance, hierarchy context, expected action, risk.
3. User can generate and revise hierarchy-aware drafts with Indonesian meaning preview.
4. Unreplied/overdue/waiting-reply tracking works across integrated platforms.
5. Agent chat answers operational questions and can trigger draft generation.
6. Any send attempt without explicit approval is blocked server-side.
7. Audit log can prove who approved what, when, and for which exact payload.

## 14. Open Implementation Notes
- Connector rollout should start from read-only + draft-assist, then approved send.
- Approval policy must be implemented as central middleware/service, not duplicated per connector.
- Risk and sensitive-topic signals should affect checklist strictness, never bypass it.
