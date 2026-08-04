# Development roadmap

## Phase 1 — Foundation
- Create the monorepo layout for frontend, backend, and deployments.
- Stand up PostgreSQL, Redis, RabbitMQ, and object storage.
- Implement auth, user management, and the initial API shell.
- Establish coding standards, CI, and quality gates.

## Phase 2 — Core editors
- Deliver 2D canvas editing for CAD and PCB schematics.
- Deliver a 3D viewport for assemblies and design review.
- Add project files, folder structures, and content versioning.
- Enable real-time collaboration with Yjs and WebSocket events.
- Parametric 3D CAD engine (`services/backend/app/cad/`), built on CadQuery/OpenCascade:
  - 2D sketch entities (points, lines, circles, arcs) with a real geometric constraint
    solver (`scipy.optimize.least_squares`, `trf` method) supporting horizontal, vertical,
    parallel, perpendicular, equal-length, equal-radius, distance, length, angle,
    concentric, tangent, coincident, and radius constraints, with rank-based
    over/under-constrained detection.
  - Feature-history modeling: bodies are stored as an ordered list of feature operations
    (extrude, revolve, fillet, chamfer, boolean union/cut/intersect) and rebuilt on demand
    by replaying them through the CadQuery kernel — genuinely parametric, so editing an
    earlier feature re-derives everything downstream.
  - Export to STEP, STL, and OBJ from real OCCT tessellation/geometry.
  - Assembly system with part instances, revolute/prismatic motion constraints (real
    Rodrigues-rotation and translation math), and AABB-based collision detection.
  - 27 REST endpoints under `/api/v1/cad/*`; AI tool registry can create sketches, extrude,
    revolve, fillet, and chamfer through the same real engine.
  - Frontend: `Viewport3D` renders the kernel's real tessellated mesh via Three.js
    `BufferGeometry`; the CAD editor page can build a body from a sketch and export it.
  - Not yet implemented: sweep/loft/draft/rib/hole features, multi-loop sketch profiles
    (holes in a face), and a full interactive feature-tree UI — a "quick cube" flow
    demonstrates the pipeline end-to-end in place of a full sketcher UI for now.

## Phase 3 — AI platform
- Introduce a multi-provider LLM router and cost controls.
- Implement LangGraph-based agents and a central tool registry.
- Add RAG over datasheets, standards, and internal documents.
- Stream AI responses and capture usage metrics.

## Phase 4 — Advanced workflows
- Add simulation jobs, firmware generation, and manufacturing planning.
- Improve PCB automation with DRC and auto-routing.
- Add release packaging, BOM generation, and documentation workflows.

## Phase 5 — Production hardening
- Run load and security testing at enterprise scale.
- Add autoscaling, SLO monitoring, and incident response playbooks.
- Expand compliance, disaster recovery, and enterprise support readiness.

## Landing page & billing integration (Velorah)
Velorah is Enginex AI's public marketing/signup site — a standalone Vite +
React + TypeScript + Tailwind app (`apps/velorah/`, deployed independently
of `apps/web`) integrated with real backend services:
- Signup (`/api/v1/landing/signup`) creates a genuine login-capable account
  through the existing `AuthService` (real password hashing, real JWTs) and
  auto-provisions an `Organization` — not a parallel, insecure user-creation
  path. Re-submitting an already-registered email returns `409` rather than
  the account-takeover-shaped "return the existing user's tokens" behavior
  from an earlier draft of this flow.
- Billing (`/api/v1/billing/*`) is a real Stripe integration: Checkout
  session creation and a signature-verified webhook handler
  (`checkout.session.completed`, `customer.subscription.updated/deleted`,
  `invoice.payment_failed`). With no `STRIPE_SECRET_KEY` configured (the
  default in dev), it returns a clean `503 SERVICE_UNAVAILABLE` — signup
  still succeeds, just without a checkout session — rather than crashing or
  faking success.
- Age verification (`/api/v1/age/*`) is a real, authenticated 18+ check with
  every attempt (pass or reject) logged to the existing `audit_logs` table.
  Only a birth year is stored (not a full DOB), and it is **not** encrypted
  at rest — real field-level encryption (pgcrypto/KMS) is a follow-up.
- Analytics events (`/api/v1/landing/analytics/event`) persist to a new
  `analytics_events` table — real funnel data, no third-party analytics
  vendor wired in yet.
- Email (welcome, payment-failed) renders real Jinja2 templates and sends
  over real SMTP when `SMTP_HOST` is configured; otherwise it logs the
  rendered email instead of silently dropping it, mirroring the AI
  provider router's fallback-provider pattern.
- Not yet implemented: SendGrid/Mixpanel/Auth0/Sentry vendor integrations
  (SMTP/log and DB-native analytics stand in for now), async email/analytics
  dispatch via Celery (currently synchronous), GDPR data-export/erasure
  flows, refunds/cancellation UI, and the affiliate/referral program —
  all called out as forward-looking in the original spec's own "next steps."
