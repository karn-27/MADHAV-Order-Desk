# MADHAV Order Desk

An owner-approved order assistant for small businesses that sell through chat.
Built for AMD Developer Hackathon ACT III, Reinvent Commerce.

**Try the demo:** https://madhav-order-desk.opalsage3.chatgpt.site

## What the prototype does

The owner opens a fictional customer conversation and clicks **Prepare reply**.
DeepSeek-V4-Flash through AMD TokenFactory extracts the requested product,
quantity and pickup date. TypeScript validates stock and computes prices from
the catalog. The owner reviews every reservation and reply.

- English and Hinglish request extraction with conversation context in live mode.
- Capacity per pickup date and suggestions for available same-size alternatives.
- Missing details and unsupported requests stay blocked or require human review.
- Editing a reservation updates its existing ID and moves capacity without duplication.
- Manually recorded received payments, outstanding balances and reminder drafts.
- Browser-local state, CSV export and responsive layout.

## Quick start

Requires Node.js 24 LTS and npm. Extract this folder or clone the repository.

```sh
npm install
npm run dev
```

Open http://localhost:5173. Without a key, use Setup > Sample mode.
Sample mode is deterministic parsing, clearly labelled, and makes no AI call.

For live AMD mode, copy `.dev.vars.example` to `.dev.vars` in the project root.
Set your own `AMD_API_KEY`, restart the dev process, and select AMD live mode.
The optional `AMD_MODEL` defaults to `DeepSeek-V4-Flash`.
Never put a key in customer text or commit `.dev.vars`.

```sh
npm test
npm run build
npm start
```

The production preview uses Wrangler and normally opens http://localhost:8787.
This export removes the original deployment ID. It does not grant access to
Mohit's hosting account or API secret. Use your own infrastructure and key.

## Judge walkthrough

1. Aanya: prepare the Hinglish request, confirm one chocolate cake, reserve, approve reply.
2. Rohan: Red Velvet has zero capacity. Prepare a reply and see available alternatives.
3. Add a customer message: `Kal 1 vanilla cake kar do`. Prepare, review and reserve.
4. Meera: prepare two cupcake boxes, reserve INR 840, record INR 420 received in Orders.
5. Confirm that the remaining balance is INR 420. Inspect a reminder draft before approval.
6. Try missing quantity/date or an allergy guarantee. Do not infer confirmation or safety claims.

All customers and transactions are fictional. Relative dates use Asia/Kolkata.
Reset sample data in Setup only when you want to clear this browser's demo history.

## Architecture

React 19 + TypeScript UI, Vinext/Vite and Cloudflare Workers runtime.
`app/api/analyze/route.ts` calls AMD's OpenAI-compatible chat-completions endpoint.
Zod validates the structured response. `lib/domain.ts` owns totals, capacity,
reservation edits, available alternatives and payment bounds.
The key stays server-side. Catalog and orders remain in the visitor's localStorage.

AMD base URL: https://developer.amd.com.cn/radeon/api/v1

## Evidence and limits

Three local regression suites cover amount calculations, capacity, duplicate
message prevention, reservation changes, alternatives and payment bounds.
Six synthetic deployed AMD extraction cases passed on 17 October 2026 after
prompt refinement. `evidence/live-order-results.json` records their responses.
Observed request times were 9.68 to 11.22 seconds for those six cases. This is a
small development check, not an official benchmark or accuracy claim.

This is a WhatsApp-style simulation, not a Meta integration. No real messages
or payment collection. No shared database, production accounting, automatic
refunds, or autonomous allergy assurances. AMD availability and shared quotas
may limit live mode. Use synthetic non-sensitive examples only.

## Next steps and business hypothesis

Start with home bakeries. Validate with five merchant pilots, measuring time per
confirmed order, missed requests and wrong-price/overbooking incidents against
their baseline. A monthly subscription is a hypothesis to test, not validated
revenue. Production work includes the official WhatsApp API, durable storage,
authentication and payment webhooks.


## Future WhatsApp integration

**Not connected yet.** The current app simulates chats; it does not receive or send live WhatsApp messages. The architecture, phased implementation, test-number-first approach, and safeguards for keeping an existing Android shop number are described in [WhatsApp Integration Roadmap](docs/WHATSAPP_INTEGRATION.md). Do not migrate or delete a shop account merely to test this prototype.

## Attribution

Project owner: Mohit Joshi. Code, design and submission materials were developed
with OpenAI Codex assistance. The prototype uses a Sites/Vinext starter and
third-party libraries under their respective licenses. Cover artwork is AI-generated.
The earlier narrated-slide video is a draft and is being replaced with an app demo.
Application source: MIT (see LICENSE).
