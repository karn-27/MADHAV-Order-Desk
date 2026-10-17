# WhatsApp Integration Roadmap — MADHAV Order Desk

**Status (17 October 2026): Planned, NOT implemented.** The existing app is a WhatsApp-style simulation. It does **not** connect to any shop number, read real WhatsApp chats, or deliver messages. Payment recording is manual. No real number, account, or API token is associated with this repository.

## Goal

A shop owner should retain control over their customer conversations and use MADHAV as an order assistant:

1. A customer sends a message to the shop's WhatsApp number.
2. Meta's official WhatsApp Business Platform delivers a verified webhook to MADHAV.
3. MADHAV saves the message to a secure shared inbox and optionally prepares a draft using AMD TokenFactory.
4. Server-side catalog and reservation rules check product, quantity, pickup date, price and capacity.
5. **The owner must explicitly approve** a reservation and then separately approve the outgoing reply.
6. MADHAV sends the approved reply using the official Cloud API, records its provider message ID and status, and avoids duplicate sends.
7. Payments remain **unpaid until independently confirmed**; a customer message claiming payment never updates the ledger.

No unattended confirmation, payment marking, stock substitution, or medical/allergy assurance.

## Existing personal WhatsApp number — do not risk the shop account

The owner's current shop number uses **regular WhatsApp Messenger on Android**, not the WhatsApp Business app.

- **Do not try to attach regular WhatsApp Messenger directly to Cloud API.** A standard Cloud API migration of a registered Messenger number requires disconnecting/deleting its Messenger registration; that is **not** the chosen plan and can put access and chat history at risk.
- **Do not delete the existing WhatsApp account or uninstall/clear its data.** Do not attempt QR-code scraping, unofficial WhatsApp Web bots, or services requesting the OTP or backup credentials.
- First test MADHAV on a **separate dedicated test number / Meta test number**, without touching the shop number.
- If the owner later opts in, document and verify an Android backup and complete a carefully supervised move from regular WhatsApp to the **official WhatsApp Business app on the same phone number**, checking preserved conversations afterward.
- Then check **eligibility for WhatsApp Business App + Cloud API coexistence** through a supported Solution Partner / Tech Provider and the correct Embedded Signup flow. Coexistence, when eligible, lets the Business app stay active on the phone while the platform handles messaging. It is not guaranteed for every number, account or region, and provider requirements/limitations can change.
- Stop before any step that proposes **Delete my account**, app-only to API-only migration, number replacement, or lost chat history; owner review is mandatory. Do not silently fall back to API-only registration if coexistence is not offered.
- Launch on the real shop number **only after** the separate-number end-to-end pilot passes and the owner explicitly approves the transition.

## Target architecture

```text
Customer WhatsApp
    |
    v
Meta WhatsApp Business Platform (Cloud API)
    | incoming events / delivery receipts
    v
Public HTTPS webhook on Cloudflare Workers
    | verify Meta webhook challenge and signature
    | deduplicate provider message IDs; rate-limit / queue
    v
Durable DB (D1/Postgres): tenants, channels, chats, messages, drafts,
orders, order-events, catalog, audit logs and outbound job state
    |
    +--> AI extraction (AMD TokenFactory; untrusted input)
    |       |
    |       v
    |    Server-side schema validation and catalog/capacity checks
    |
    v
Authenticated MADHAV owner inbox (review/edit/approve)
    | signed, authorized approval action
    v
Server-side outbound service -> Cloud API POST /{PHONE_NUMBER_ID}/messages
    |
    v
Provider message status webhook -> DB and inbox
```

Never call Graph API directly from the browser or embed an access token in a React bundle. Cloudflare Workers secrets should hold the access token, webhook verification token and app secret. Use tenant-specific authorisation checks on all inbox, order and sending APIs.

## Engineering work breakdown

| Phase | Deliverables | Acceptance tests |
| --- | --- | --- |
| 0. Offline preparation | Separate test number, test Meta Business Portfolio/app, sandbox credentials, documented consent and an isolated test environment | No change to production shop number; no secrets committed |
| 1. Durable storage | Move production inbox, catalog, reservations, payments and message IDs from browser `localStorage` to secured shared database; keep demo mode isolated | Different browsers see permitted records consistently; unauthorised access fails |
| 2. Meta webhook | GET verification + POST events endpoint, raw-body HMAC signature verification, strict payload validation, idempotency key, retry-safe ingest and error logging | Forged payload rejected; duplicate webhook doesn't create duplicate conversation or order |
| 3. Real inbox | Map verified contacts/messages into shop inbox, persist media metadata cautiously, distinguish inbound messages from app/outbound message echoes | Incoming test WhatsApp message appears only once; no cross-tenant leaks |
| 4. AI draft and business rules | Reuse `app/api/analyze/route.ts` concept and `lib/domain.ts`; server-side catalog, date-capacity and order-state checks | Hinglish examples, sold-out alternatives, missing fields and invalid-date checks pass |
| 5. Approval and sending | Owner authentication, roles, draft editing, explicit reserve and send buttons; outbound API, status reconciliation and human takeover | No send before approval; no duplicate sends on retry or double-click |
| 6. Compliance and reliability | Customer-service window enforcement, approved templates outside allowed window, rate limits, opt-out, encryption, retention, audit history, contact-consent records, alerting and observability | Payment claims never self-confirm; retries and outage tests pass |
| 7. Coexistence review | Verify eligibility and provider fees for existing Business App number, backup/restore review, cutover and rollback plan | Owner explicitly approves, phone access and chats remain intact; stop if eligibility fails |

**Development note:** `app/page.tsx` currently manages demo conversations, orders and catalog via localStorage; its `send()` adds a message to the simulated conversation, and `incoming()` adds a fabricated customer message. These are **not** connected to WhatsApp. `app/api/analyze/route.ts` currently analyzes text via AMD and does not handle Meta events. Replace these paths with a proper authenticated backend; do not repurpose the demo handlers as real send endpoints.

### Suggested new modules (not present yet)

- `app/api/whatsapp/webhook/route.ts`: verify incoming Meta challenge; verify request signature and persist/queue events.
- `lib/whatsapp/verify.ts`: timing-safe raw-body signature check.
- `lib/whatsapp/outbound.ts`: authorized, idempotent Cloud API sending and status tracking.
- `lib/whatsapp/normalise.ts`: safe parsing/normalization of message, status and echo events.
- `db/...`: durable data model, shop-scoped foreign keys and audit logs.
- `app/api/orders/... / app/api/messages/...`: authenticated business operations, owner approval and read APIs.
- Tests: signed/forged events, duplicate deliveries, order concurrency, blocked sends and currency/payment invariants.

This is a **plan**, not a claim that those endpoints are deployed.

## Secrets and data safety

Store `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_APP_SECRET`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` and relevant account IDs server-side only. Keep credentials out of the repository, screenshots, logs and demo chat text. Validate every provider callback before storing customer data. Keep customer phone numbers and messages private with role-based access, documented retention/deletion and access audit. Never forward an entire customer's conversation to a model without a justified minimum-data policy and the shop's appropriate notice/consent.

## Pricing and constraints

Do **not** promise the integration is free. Official Cloud API fees can vary by message category, country, customer-service window and current Meta policies; an onboarding partner may charge separately. Infrastructure, storage, AI inference and support can also cost money. Validate **current India pricing** and partner terms at setup time. Messages outside the permitted customer-service window may require approved message templates, subject to Meta's current policies.

## Demo/evidence rules

The current recording and hosted demonstration must be described as **sample-mode simulation** unless a particular interaction demonstrably uses the live AMD API. Never describe an AI-powered proposal in a sample-mode video as live AMD inference. Never present simulated messages as actual WhatsApp transmissions or manual entries as verified gateway payments. Use fictional contacts in hackathon media.

## Official / industry references (revalidate before onboarding)

- Meta WhatsApp Cloud API overview: https://developers.facebook.com/docs/whatsapp/cloud-api/overview
- Meta-owned WhatsApp Cloud API collection: https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api
- Meta-owned message sending endpoint reference: https://www.postman.com/meta/whatsapp-business-platform/folder/13382743-ba8d099d-007e-4b52-b9f2-3cf3c60e4fbc
- Solution provider coexistence explanation (Gupshup): https://bizgate-docs.gupshup.io/docs/what-is-coexistence

A provider article or GitHub tutorial is not a guarantee of eligibility for a specific shop number. Official Meta onboarding flow and the chosen provider's live terms govern the actual migration.
