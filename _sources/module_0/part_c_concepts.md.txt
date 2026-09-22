# Part C: Key Concepts Deep Dive

Part A and Part B showed the code. This part explains the six ideas underneath it. Concept 2 is the one that pays for
this whole module.

## Concept 1: How to Read TypeScript

You do not need to write TypeScript. You need to read it fast enough that pi stops being an obstacle. This section is
the survival kit. Come back to it whenever a line in pi looks like noise.

**The single most useful habit: mentally delete the types.** Everything between a `:` and the next `,` `)` `=` or
newline is annotation. Everything inside `<>` is a type argument. Delete all of it and what remains is ordinary code
that looks a lot like Python without the colons.

```ts
export function createWriteTool<TContext extends ExecutionToolContext = ExecutionToolContext>(): AgentHarnessTool<
	TContext,
	typeof writeSchema,
	undefined
> {
```

Delete the annotations and it is just `def create_write_tool():`. That is genuinely all it says. The other 90 characters
are the return type.

**Syntax you will meet, and what it means:**

| TypeScript | Means | Python |
| --- | --- | --- |
| `x: string` | annotation | `x: str` |
| `x?: string` | property may be absent | `x: str \| None = None`, roughly |
| `x: string \| undefined` | present, may be `undefined` | required, may be `None` |
| `interface Foo { ... }` | a structural shape, erased | `Protocol` or a pydantic model |
| `type Foo = A \| B` | a union alias | `Foo = A \| B` |
| `"text"` as a type | a one-value type | `Literal["text"]` |
| `readonly` | cannot reassign | `Final`, roughly |
| `Foo[]` | list | `list[Foo]` |
| `Record<string, T>` | mapping | `dict[str, T]` |
| `Partial<T>` | all fields optional | `total=False` TypedDict |
| `Extract<T, U>` / `Exclude<T, U>` | filter a union | no equivalent |
| `Omit<T, K>` / `Pick<T, K>` | drop / keep fields | no equivalent |
| `typeof x` in a type position | the type of value `x` | no equivalent |
| `A extends B ? C : D` | if/else at type level | no equivalent |
| `x as T` | trust me, it is a `T` | `typing.cast` |
| `x!` | trust me, not null | `assert x is not None`, silently |
| `x?.y` | `y` if `x` is set, else `undefined` | `x.y if x is not None else None` |
| `x ?? y` | `y` only if `x` is null/undefined | `y if x is None else x` |
| `(x) => expr` | lambda, but can have a body | `lambda x: expr` |
| `` `a ${b}` `` | interpolation | f-string |
| `void promise` | deliberately not awaited | `asyncio.create_task`, roughly |
| `async function*` | async generator | `async def ... yield` |
| `for await (const x of it)` | async iteration | `async for x in it` |

**Things you can skip on a first read.** Being selective is the skill:

- Long generic parameter lists. Read the function name and the body; come back if the body confuses you.
- `Extract`, `Exclude`, `Omit` chains. Read them as "some subset of that other type" and move on.
- Anything of the shape `A extends B ? C : D`. It computes a type. You will meet exactly one that matters
  (`Model.compat`, Pass 8) and this guide explains it.
- `export type { ... } from "..."` lines. Plumbing, equivalent to re-exports in an `__init__.py`.

**Two structural facts to know.**

**Files are modules, and imports are hoisted.** A `.ts` file is a module the moment it uses `import` or `export`, with
no `__init__.py` equivalent. `export` is what makes a name public; without it a name is genuinely unreachable from
outside the file, not private-by-convention. And an `import` statement can legally appear anywhere in the file — you
saw one at line 576 of `types.ts` — because imports are declarations, not statements that run in order.

**`import type` is deleted; `import` is not.** This is the distinction to actually internalize, because it tells you at
a glance which names in a file are real at runtime:

```ts
import { type AssistantMessage, EventStream, validateToolArguments } from "@earendil-works/pi-ai";
```

`EventStream` and `validateToolArguments` exist when the program runs. `AssistantMessage` does not — it is a type, and
the `type` keyword marks it for deletion. This is Python's `if TYPE_CHECKING:` block, made per-symbol and mandatory.

**How pi is built and run**, which you need for Project 1:

```
                      .ts source
                     /          \
     [tsc / tsgo]   /            \   [tsx]
                   v              v
        .js written to dist/    types stripped in memory
        (what gets published)   and run immediately
```

Two commands matter. `npm run check` type-checks without producing files. `./pi-test.sh` runs the TypeScript directly
through `tsx`, which strips the types and executes — fast, and with **no type checking at all**. Type checking and
running are separate activities in TypeScript, which is the opposite of your instinct from `python script.py`.

**One flag worth knowing, because it explains something you will notice.** pi's `tsconfig.base.json` sets
`erasableSyntaxOnly: true`, which forbids any TypeScript syntax that cannot be removed by deleting characters. That
outlaws `enum`, `namespace`, and constructor parameter properties. It is why pi has **no enums anywhere** and uses string
literal unions instead — a habit that maps directly onto your `Literal[...]`.

## Concept 2: Types Are Erased

This is the concept that explains pi's design, so it gets the most space.

**Python:** type hints survive to runtime. They are stored in `__annotations__`, readable with
`typing.get_type_hints()`, and that is precisely how pydantic works — it reads the annotations of your class and builds a
validator from them.

```python
class WriteInput(BaseModel):
    path: str
    content: str

WriteInput.model_json_schema()   # works: the annotations are still there
isinstance(x, WriteInput)        # works: the class is a real object
```

**TypeScript:** annotations are deleted. Completely. After compilation there is no trace.

```ts
interface WriteInput {
	path: string;
	content: string;
}
```

compiles to... nothing. Not an empty object. The declaration is gone. There is no value named `WriteInput` at runtime,
which means:

```ts
// None of these can exist:
WriteInput.jsonSchema();          // no such value
if (x instanceof WriteInput) {}   // no such value
typeof WriteInput;                // no such value
```

**Three consequences follow, and they shape everything.**

**Consequence 1: no runtime validation for free.** You cannot ask a type to validate data. Anything crossing a trust
boundary — an HTTP response, a file on disk, a tool call from a model — needs a separate runtime schema. That is why
TypeBox is a dependency and why every tool in pi carries a `parameters` schema object.

This is the reason for the direction reversal noted in Pass 6. In Python, class first, schema derived. In TypeScript,
schema first, type derived. The schema must be the source of truth, because it is the only part that survives.

**Consequence 2: no `isinstance` for interfaces.** You cannot ask whether a value satisfies an interface, because the
interface is not there to ask. So you check the data instead:

```ts
if (message.role === "assistant") { /* narrowed */ }        // check a discriminant field
if (typeof content === "string") { /* narrowed */ }          // check a primitive's type
if ("partial" in event) { /* narrowed */ }                   // check a key exists
if (error instanceof Error) { /* narrowed */ }               // works: Error is a real class
```

The first three inspect **data**. Only the fourth uses `instanceof`, and only because `Error` is an actual runtime class.

This is the real reason pi's data model is discriminated unions rather than class hierarchies. It is not taste. A class
hierarchy is unusable for anything that gets serialized, because `JSON.parse` gives you plain objects and `instanceof`
returns `false` on all of them. A discriminated union round-trips through JSON perfectly, because its tag is data.

When you need a reusable check, write a **type predicate**:

```ts
function isToolCall(block: unknown): block is ToolCall {
	return typeof block === "object" && block !== null && (block as { type?: string }).type === "toolCall";
}
```

The return type `block is ToolCall` is the interesting part: a `boolean` that also tells the compiler what a `true` result
proves. Python's `TypeGuard[ToolCall]` is exactly this, and it is the one place the analogy is perfect.

Note that the compiler does **not** verify the body. You could `return true` and it would believe you. A type predicate
is a promise you are making, not one the compiler checks — the same trust model as `typing.cast`.

**Consequence 3: generics vanish too.** `ToolResultMessage<ReadDetails>` and `ToolResultMessage<BashDetails>` are the same
thing at runtime. You cannot inspect `TDetails`, dispatch on it, or construct from it. Python's
`get_args(SomeGeneric[int])` has no counterpart.

**What you get in exchange.** It is a real trade, and TypeScript's side is not empty:

| | Python + pydantic | TypeScript |
| --- | --- | --- |
| Runtime validation | built in | needs a schema library |
| `isinstance` on a shape | yes | no |
| Startup cost | builds validators at import | zero |
| Per-call cost | validates on every construction | zero unless you ask |
| Type-level computation | very limited | conditional types, mapped types, `Extract` |
| Narrowing from a check | limited | thorough, and the main way you work |

Zero runtime cost is why the erasure exists. Types that do not exist cannot slow anything down. And because the compiler
is not constrained by needing to produce runtime artifacts, it can do things Python's cannot — Pass 8's conditional type
is not expressible in Python at all.

**What this means for your harness.** You get to delete a whole layer. Everywhere pi keeps a schema *and* a type in sync
by hand, you write one pydantic model and get both. Concretely, across the rest of this course:

| pi has to | You write |
| --- | --- |
| a TypeBox schema plus `Static<typeof schema>` | one pydantic model |
| a separate `Value.Check()` call to validate | `model_validate()`, same object |
| hand-written type predicates for runtime checks | `isinstance`, which actually works |
| `Model.compat` as a conditional type | separate models per wire format, or a plain dict |

That is not a small saving. It is most of `packages/ai`'s type machinery. When you meet a pi pattern in a later module and
it looks like a lot of ceremony for little gain, check whether it is paying this tax — and if it is, skip it.

## Concept 3: Absent, Null, and Set — Reading pi's Optional Fields

Python has one empty value. JavaScript has two, and pi uses both to mean different things. You need this to read pi's
config types correctly; you do not need it to write Python.

| | Meaning | Where it comes from |
| --- | --- | --- |
| `undefined` | "not set" | a missing property, a missing argument, no `return` |
| `null` | "set, to nothing" | only ever explicit — nothing produces it by accident |

Combine that with the optional-property marker `?` and pi gets **three** distinguishable states from one field. Line 86
of `types.ts`:

```ts
export type ThinkingLevelMap = Partial<Record<ModelThinkingLevel, string | null>>;
```

`Partial<...>` makes every key optional, so a key can be absent. The value type includes `null`. The doc comment above
it explains why both are needed: "Missing keys use provider defaults. null marks a level as unsupported."

- key absent — no opinion, fall back to the provider default
- value is `null` — this level is explicitly not supported
- value is a string — use this provider-specific value

Collapse `undefined` and `null` into one and that information is gone. You saw the same three-state shape in Pass 6 with
`constrainedSampling?: false | ConstrainedSamplingConfig`, where absent means "no preference" and `false` means
"explicitly off."

**How to model that in Python.** Python's `None` covers `null` cleanly, but "absent" needs help, because
`x: str | None = None` cannot tell "the caller omitted it" from "the caller passed None." Two standard answers:

```python
# 1. pydantic: ask whether the field was actually provided
model.model_fields_set          # a set of the names the input supplied

# 2. a distinct sentinel for "absent"
class Unset: ...
UNSET = Unset()
level: str | None | Unset = UNSET
```

Reach for these only where the distinction is load-bearing, as it is in provider config. For ordinary optional fields,
plain `None` is right, and pi's own habit is the same — the overwhelming majority of its optional fields are simple
`?` properties where absent is the only empty state.

**Two operators you will read constantly:**

- `x?.y` — **optional chaining**. Evaluates to `undefined` instead of throwing when `x` is null or undefined. You saw
  `context.abortSignal?.aborted` in `write.ts`.
- `x ?? y` — **nullish coalescing**. Falls back to `y` only for `null` and `undefined`, unlike `||` which also falls
  back for `0` and `""`. When you see `??` in pi, read it as "default, but `0` and empty string are legitimate values."

That last distinction is why `options.limit ?? 100` is correct and `options.limit || 100` is a bug when a limit of `0`
is meaningful. You will not write this bug in Python, but you will read code that was careful about it, and the care is
the signal.

## Concept 4: Result Instead of Exceptions

Open [`packages/agent/src/harness/types.ts`](https://github.com/earendil-works/pi/blob/v0.87.0/packages/agent/src/harness/types.ts#L8-L41)
and read lines 8-41:

```ts
/** Result of a fallible operation. Expected failures are returned as `ok: false` instead of thrown. */
export type Result<TValue, TError> = { ok: true; value: TValue } | { ok: false; error: TError };

export function ok<TValue, TError>(value: TValue): Result<TValue, TError> {
	return { ok: true, value };
}

export function err<TValue, TError>(error: TError): Result<TValue, TError> {
	return { ok: false, error };
}

export function getOrThrow<TValue, TError>(result: Result<TValue, TError>): TValue {
	if (!result.ok) throw result.error;
	return result.value;
}
```

`Result` is a discriminated union again — but discriminated on a **boolean**, not a string. `ok: true` and `ok: false` are
distinct literal types, so `if (result.ok)` narrows exactly like `if (message.role === "user")`.

```ts
const result = await env.readTextFile(path, context);
if (!result.ok) {
	// result.error is available; result.value is not
	return `could not read: ${result.error.message}`;
}
// result.value is available; result.error is not
console.log(result.value.length);
```

**Why not exceptions?** TypeScript has `throw` and `try`/`catch`, and pi uses them. But it cannot type them. There is no
`throws` clause. A function's signature says nothing about what it might raise, and `catch (e)` gives you `e: unknown` —
not even `Error`, because JavaScript permits throwing any value at all, including a string or a number.

Compare:

```python
def read_file(path: str) -> str:   # might raise FileNotFoundError, PermissionError, ...
    ...
```

```ts
function readFile(path: string): Result<string, FileError>   // the failures are in the signature
```

The `Result` version puts failures in the type. You cannot reach `.value` without handling `.ok`, because the compiler
will not let you. Python has no equivalent enforcement — an uncaught `FileNotFoundError` type-checks fine.

That is why `toError(error: unknown): Error` exists on line 32 of the same file: it normalizes whatever came out of a
`catch` into an actual `Error` before pi treats it as one. `getOrUndefined` sits between the two, and its doc comment is
worth reading for the reasoning: it only accepts object values, "to avoid truthiness bugs with primitives," because a
successful result holding `0` or `""` would otherwise be indistinguishable from a failure at the call site.

**pi's rule:** `Result` for **expected** failures — file not found, permission denied, provider returned 429. `throw`
for **bugs** — invariant violated, unreachable branch reached. An expected failure is part of the function's contract. A
bug is not.

**`Result` is the clearest case in the module of a pattern worth weighing before you carry it over.** pi needs
`Result` because TypeScript cannot type what a function throws — there is no `throws` clause, and `catch (e)` gives you
`unknown`. Python has typed exceptions, a real hierarchy, `except` clauses that narrow, and tooling that tracks them, so
the limitation pi is working around is not one you have. Raising `FileNotFoundError` is available to you as the
idiomatic answer.

The *distinction* pi is drawing transfers either way, and it is the valuable part: expected failures are part of your
contract and should be documented and handled; bugs should crash loudly. Exception classes express that, and so does a
wrapper type. The case where a `Result`-like value clearly earns its keep is collecting many failures without unwinding
— batch validation, say — so that is the one to weigh it against.

`getOrThrow` is the escape hatch between the two worlds, and its doc comment scopes it honestly: "Intended for tests and
explicit adapter boundaries." `write.ts` uses it on line 32 because a failed write inside a tool should abort the tool,
and the tool-running layer above already catches and converts.

Later modules add `TaggedError`, which gives typed error variants and an exhaustive `matchError`. That is the direct
analogue of a Python exception hierarchy plus `except` clauses — except returned as values, and checked for
exhaustiveness.

## Concept 5: Async, Streams, and Cancellation

This is the other place Python is straightforwardly better, and it is worth being explicit about why: **`asyncio`
cancellation actually raises.** pi hand-writes a cancellation check at every boundary and has to thread cancellation
through every function in the call chain. You get the same behaviour from the language.

Two layers do that threading differently, and it is worth knowing which is which before you read code. `packages/ai` and
the agent loop pass a bare `AbortSignal`. The harness and tool layer passes a `Context` from pi's `chord` package — one
object holding the signal plus scoped values, which is why `write.ts` reads `context.abortSignal` rather than `signal`.
The mechanism underneath is identical; only the number of parameters changed.

The two models map closely otherwise, with two sharp exceptions. Take the mapping first:

| Python | TypeScript |
| --- | --- |
| `async def f()` | `async function f()` |
| `await x` | `await x` |
| `asyncio.gather(a, b)` | `Promise.all([a, b])` |
| `asyncio.sleep(1)` | `new Promise((r) => setTimeout(r, 1000))` |
| `async def f(): yield x` | `async function* f() { yield x; }` |
| `async for x in it:` | `for await (const x of it)` |
| `AsyncIterable` | `AsyncIterable<T>` |
| `__aiter__` | `[Symbol.asyncIterator]()` |
| `asyncio.run(main())` | not needed — top-level `await` |
| `asyncio.Task` | there is no separate task type; a promise is a promise |

`Symbol.asyncIterator` is the dunder. `Symbol` is JavaScript's mechanism for protocol keys that cannot collide with
ordinary string keys — the same role as `__aiter__`'s double underscores, implemented differently. You can see the shape
in [`event-stream.ts`](https://github.com/earendil-works/pi/blob/v0.87.0/packages/ai/src/utils/event-stream.ts#L72-L84):

```ts
async *[Symbol.asyncIterator](): AsyncIterator<T> {
	while (true) {
		if (this.queue.length > 0) {
			yield this.queue.dequeue()!;
		} else if (this.done) {
			return;
		} else {
			const result = await new Promise<IteratorResult<T>>((resolve) => this.waiting.enqueue(resolve));
			if (result.done) return;
			yield result.value;
		}
	}
}
```

Read that as: hand out anything queued; if the producer is finished, stop; otherwise park until someone pushes. The
`async *` prefix plus the `[Symbol.asyncIterator]` name is `async def __aiter__` with `yield` in it. The trailing `!` on
`this.queue.dequeue()!` is a **non-null assertion**: "I know this returns `T | undefined`, but I just checked the length,
so treat it as `T`." Same trust model as `cast`.

**Exception 1: promises are eager.** This is the big one.

```python
coro = fetch_data()      # nothing has happened yet
result = await coro      # NOW it runs
```

```ts
const promise = fetchData();   // ALREADY RUNNING
const result = await promise;  // just waits for the result
```

A Python coroutine is inert until awaited. A JavaScript promise starts the moment it is created. `await` only observes it.

Three practical consequences:

**You can start work and await it later.** This is often what you want:

```ts
const a = slowThing();          // both start now
const b = otherSlowThing();
const [x, y] = [await a, await b];   // total time = max, not sum
```

**An unawaited rejection is an error.** If a promise rejects and nobody is awaiting or catching it, Node prints an
unhandled rejection warning and can exit. Python is more forgiving about a coroutine you never awaited.

**`void promise` is how pi says "on purpose."** Look at
[`agent-loop.ts` lines 43-57](https://github.com/earendil-works/pi/blob/v0.87.0/packages/agent/src/agent-loop.ts#L43-L57):

```ts
const stream = createAgentStream();

void runAgentLoop(
	prompts,
	context,
	config,
	async (event) => {
		stream.push(event);
	},
	signal,
	streamFn,
).then((messages) => {
	stream.end(messages);
});

return stream;
```

`agentLoop` starts the real work and returns the stream **immediately**, without awaiting. The caller iterates the stream
while the loop runs behind it. The `void` operator marks the promise as deliberately not awaited, so linters do not flag
it. This is the shape of every streaming API in pi, and it only works because promises are eager — the loop is already
running by the time `return stream` executes.

**Exception 2: cancellation is cooperative and hand-written.**

```python
task.cancel()            # raises CancelledError at the next await point
```

```ts
controller.abort();      // sets a flag and fires an event. Nothing raises. Nothing stops.
```

`AbortSignal` is a flag plus an event listener. Aborting does not interrupt anything. Every piece of code that should
respond has to check `signal.aborted`, or register a listener, or pass the signal down to something that does.

This is why `write.ts` checks twice. This is why every function in pi's call chain takes a `signal` or a `context`
parameter. Forget to pass it down once, and everything below that point becomes uncancellable — with no warning of any
kind.

Python's `contextvars` removes even the parameter. A `ContextVar` set at the top of a task is readable anywhere below it
without appearing in a single signature, and `asyncio.Task.cancel()` handles the cancellation half. Between the two,
the whole threading problem goes away.

Here is the behaviour, made visible. Save this and run it with `tsx`:

```ts
async function* streamWords(text: string, signal: AbortSignal): AsyncGenerator<string> {
	try {
		for (const word of text.split(" ")) {
			if (signal.aborted) return;
			await new Promise((resolve) => setTimeout(resolve, 100));
			yield word;
		}
	} finally {
		console.log("\n[cleanup ran]");
	}
}

const controller = new AbortController();
setTimeout(() => controller.abort(), 350);

for await (const word of streamWords("one two three four five six", controller.signal)) {
	process.stdout.write(`${word} `);
}
console.log("[loop exited]");
```

Output:

```
one two three four
[cleanup ran]
[loop exited]
```

Look carefully at that. The abort fires at 350 ms. Words are yielded at 100, 200, 300, 400 ms. **"four" is emitted after
the abort, at 400 ms** — because when the abort fired, the generator was parked inside `await setTimeout(...)`, and
nothing interrupted it. It only noticed on the next trip through the loop.

Python would have raised `CancelledError` inside that `await` and stopped at three words. TypeScript does not. Your
cancellation latency is exactly the distance between your checks.

The `finally` block does run, which is the good news: `for await` calls the generator's `return()` when the loop exits
early, and that triggers `finally` for cleanup. That part works like Python.

For the harder case — cancelling something you cannot check inside, like an in-flight HTTP request — pi has
`raceWithAbortSignal` in
[`utils/abort.ts`](https://github.com/earendil-works/pi/blob/v0.87.0/packages/ai/src/utils/abort.ts#L17-L50).
It races the operation against the signal, and note lines 18-21: if the signal has *already* aborted, it still attaches a
`.catch(() => {})` to the abandoned promise. That is the unhandled-rejection problem above, handled deliberately.

## Concept 6: The Twelve Packages

Time for the map. Run this from the repo root:

```bash
ls packages/
```

```
agent   ai      chord   client    coding-agent  durable
evals   protocol  server  session-backends  telemetry  tui
```

Twelve directories. Here is what each holds, and which module of this course builds your version of it:

| Package | Holds | Python tools to consider | Module |
| --- | --- | --- | --- |
| `ai` | Provider adapters, model catalog, streaming, token accounting | `httpx`, `httpx-sse`, pydantic | 1 |
| `agent` | The agent loop, tools, sessions, compaction — the harness core | `asyncio`, pydantic | 2 and 3 |
| `tui` | Terminal UI: differential rendering, editor, autocomplete | Textual | 4 |
| `coding-agent` | The CLI you actually run; extensions, skills, settings | `importlib`, Typer or Click | 5 |
| `protocol` | Typed message schemas for the client/server split | `cbor2`, pydantic | 6 |
| `client` / `server` | The two halves of running the agent out of process | `asyncio` streams | 6 |
| `telemetry` | Vendor-neutral telemetry contracts and typed schemas | — | mentioned in 6 |
| `session-backends` | Pluggable session storage (SQLite) | `sqlite3` | mentioned in 3 |
| `evals` | Benchmarking harness behaviour | — | not covered |
| `chord` | Plugin/facet runtime, services, replicated state, and the `Context` type the tools use | `contextvars` | mentioned in 5 |
| `durable` | Durable conversation, task, and document records | — | not covered |

Two of those, `chord` and `durable`, are newer than the rest and are where pi is currently growing. `chord` is the one
you will actually bump into, because its `Context` is the last parameter of every tool (Part B, File 2). Its README is
explicit that it is not a pi package at all: it depends on nothing else in the repo and is meant to be usable by
unrelated applications.

**The dependency order is the interesting part.** From the `build` script in the root `package.json`:

```
chord -> tui -> telemetry -> ai -> durable -> agent -> session-backends
      -> protocol -> client -> server -> coding-agent
```

Read it as an argument about layering:

- **`chord`, `tui`, and `telemetry` depend on nothing.** A terminal renderer does not need to know what an agent is.
  That independence is what makes it testable, and `chord` is built first for the same reason.
- **`ai` depends on neither of them.** It knows about models and messages, not about loops or terminals. You could build
  a completely different agent on top of `ai`.
- **`agent` depends on `ai`.** The loop needs messages and a way to call a model. It does *not* depend on `tui` — the
  harness core has no idea a terminal exists.
- **`coding-agent` is last and depends on everything.** All the wiring lives in the outermost layer.

That shape — the core knowing nothing about the interface — is why pi can run as a TUI, as a JSON stream, or as a server,
without the loop changing. And it is the reason this course builds packages in that order too: you can finish Module 2
and have a working agent with no UI at all.

**The one number worth remembering:** the agent loop itself, in
[`packages/agent/src/agent-loop.ts`](https://github.com/earendil-works/pi/blob/v0.87.0/packages/agent/src/agent-loop.ts),
is a single file of 898 lines that holds **no state**. Everything difficult — the transcript, compaction, crash recovery,
permissions — lives beside it, not in it. Open the file and skim it now. You will not understand it yet. Notice how small
it is.
