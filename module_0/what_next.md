# What is Next

In **Module 1: Talking to Any Model**, you build `packages/ai` for real:

- What a provider adapter is, and why pi has ten wire formats for forty providers
- Server-sent events, and the state machine that turns a byte stream into typed events
- Streaming a reply token by token, from a hosted API and from a local server, through **one interface**
- The model catalog: where `contextWindow`, `maxTokens`, and cost rates come from
- Token accounting and cost, done properly
- `Model.compat` from Pass 8 — read properly this time, and how much of that machinery you actually need
- Retries, rate limits, and what to do when a provider returns a 429

The foundation you built here is exactly what that needs. `Message`, `Context`, and `Usage` are the types the adapters
produce. `asyncio` generators are how they stream. `CancelledError` is how you stop them.

Python's tools for this are good. `httpx` gives you streaming HTTP and connection reuse, and `httpx-sse` handles the
server-sent-events framing that pi decodes by hand. So expect your build track to be *shorter* than pi's implementation.
Spend the time you save on reading pi's adapters more carefully — the ten wire shapes are where the knowledge is, and
they are the part no library gives you.

Module 1 is also the first place you have a real design choice to make. pi supports forty providers and needs a model
catalog, a compat-flag system, and an OAuth flow to do it. That is a lot of machinery for day one. The module shows you
all of it, then asks which parts earn their place in *your* harness.

By the end of Module 1, your harness talks to a real model and streams a real reply. It will not be an agent yet — there
is no loop and there are no tools. That is Module 2.

One thing worth knowing before you go. The temptation in Module 1 is to support one provider well and move on. The
provider abstraction is the most valuable thing in `packages/ai`, and you only find out whether yours is right by
pointing it at a second, differently-shaped API. So building for two from the start — one hosted, one local — is the
cheapest test available.
