# Part A: Guided Reading of types.ts

Open [`packages/ai/src/types.ts`](https://github.com/earendil-works/pi/blob/v0.84.2/packages/ai/src/types.ts)
in your editor. This is the vocabulary file. Every other package in pi speaks the language defined here: what a message
is, what a tool is, what a model is, what a token costs.

It is 830 lines, and you are not going to read all of it. You will make eight focused passes, each targeting one
TypeScript concept. Pass 8 is a preview you are allowed to not understand yet.

A note on line numbers: they are accurate for the pinned commit and will drift as pi changes. The file paths are the
durable part. If a line number looks wrong, search for the name instead.

## Pass 1: The Import Block (Lines 1-15)

Read the first fifteen lines:

```ts
import type { TelemetryContext } from "@earendil-works/pi-telemetry";
import type { AnthropicOptions } from "./api/anthropic-messages.ts";
import type { AzureOpenAIResponsesOptions } from "./api/azure-openai-responses.ts";
// ... ten more like it ...
import type { AssistantMessageEventStream } from "./utils/event-stream.ts";

export type { AssistantMessageEventStream } from "./utils/event-stream.ts";
```

Four things are happening here, and three of them will surprise you.

**1. There is no `__init__.py`.** A TypeScript file is a module the moment it uses `import` or `export`. There is no
marker file that turns a directory into a package. A file that has neither keyword is not a module at all; its top-level
variables leak into the global scope. This is why every file in pi has at least one `export`.

**2. The file extension is required.** `"./api/anthropic-messages.ts"` includes `.ts`. Python writes
`from .api.anthropic_messages import AnthropicOptions` with no extension and no leading dot for the file type. ES modules
require the extension, because the runtime resolves the path literally instead of searching a set of candidate names.

Note that pi imports `.ts` even though what eventually runs is `.js`. That is a compiler setting, not the default; we
come back to it in [Concept 1](part_c_concepts.md#concept-1-how-to-read-typescript).

**3. `import type` is not the same as `import`.** This is the first genuinely new idea. `import type` imports *only the
type*, and the entire statement is deleted before the code runs. `import` (without `type`) imports a real runtime value.

Look at what that means in practice. `TelemetryContext` on line 1 is used to describe the shape of an argument, so it is
imported as a type and vanishes. Compare with line 9 of
[`agent-loop.ts`](https://github.com/earendil-works/pi/blob/v0.84.2/packages/agent/src/agent-loop.ts#L6-L12):

```ts
import {
	type AssistantMessage,
	type Context,
	EventStream,
	type ToolResultMessage,
	validateToolArguments,
} from "@earendil-works/pi-ai";
```

`EventStream` and `validateToolArguments` are real things at runtime: a class you can call `new` on, and a function you
can call. `AssistantMessage`, `Context`, and `ToolResultMessage` are types, marked with an inline `type` keyword, and
they are gone by the time the program starts.

**Python parallel:** This is `if TYPE_CHECKING:` — but mandatory, per-symbol, and enforced. In Python you write:

```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .api.anthropic_messages import AnthropicOptions
```

...to avoid a circular import or a slow import at runtime. In TypeScript, `import type` does that job with one keyword,
and the compiler will tell you if you got it wrong.

**4. A file can re-export.** Line 15 re-exports `AssistantMessageEventStream` so consumers can get it from
`types.ts` without knowing it lives in `utils/event-stream.ts`. This is `from .utils.event_stream import X as X` in an
`__init__.py`, and it serves the same purpose: a stable public surface over a private layout.

**Questions to answer before moving on:**

- Why does pi bother marking imports as `type` instead of just importing everything normally?

:::{dropdown} Answer
Three reasons, in order of how much they matter.

First, **circular imports**. Types can be mutually recursive without any problem, because they do not exist at runtime.
Values cannot. `types.ts` imports from `./api/anthropic-messages.ts`, and that file almost certainly needs types from
`types.ts`. With `import type`, both directions are free. With value imports, you get a cycle that either crashes or
produces `undefined`.

Second, **honesty about cost**. A value import means the module is loaded and its top-level code runs. A type import
costs nothing. Marking them differently makes the runtime cost of a file visible in its import block.

Third, **the compiler can enforce it**. With the `verbatimModuleSyntax` family of settings, TypeScript errors if you
value-import something that is only a type. That turns a subtle startup-time bug into a compile error.
:::

- What happens to a `.ts` file that contains no `import` and no `export`?

:::{dropdown} Answer
It is treated as a **script**, not a module. Its top-level declarations go into the global scope, where they can collide
with declarations from any other script file in the project. Two such files each declaring `const config = ...` is a
duplicate-identifier error.

This is the opposite of Python, where every `.py` file has its own namespace automatically and there is no way to
accidentally leak into a global one. In TypeScript the module namespace is opt-in, and `export` is how you opt in.

In practice you never hit this, because every real file exports something. But it explains why you sometimes see a lone
`export {};` at the top of a file that has nothing to export: it is a declaration that says "this is a module."
:::

---

## Pass 2: The Open Union Trick (Lines 17-33)

Read lines 17-33:

```ts
export type KnownApi =
	| "openai-completions"
	| "mistral-conversations"
	| "openai-responses"
	| "azure-openai-responses"
	| "openai-codex-responses"
	| "anthropic-messages"
	| "bedrock-converse-stream"
	| "google-generative-ai"
	| "google-vertex"
	| "pi-messages";

export type Api = KnownApi | (string & {});
```

**What `KnownApi` is:** a **string literal union**. The type `"openai-completions"` is a type with exactly one value: the
string `"openai-completions"`. Union ten of those together with `|` and you have a type that accepts exactly those ten
strings and nothing else.

**Python parallel:** `Literal["openai-completions", "anthropic-messages", ...]`. Identical idea. TypeScript just uses it
about a hundred times more often, because it is the default way to model a closed set instead of a fallback for when
`Enum` feels too heavy.

Notice there is no `enum` here. pi has no enums anywhere, on purpose. We will see why in
[Concept 2](part_c_concepts.md#concept-2-types-are-erased).

**What `Api` is:** this one is a trick, and it is worth understanding because it appears throughout pi.

The goal is a type that means: "one of these ten strings, but any other string is also allowed." The obvious spelling is
`KnownApi | string`. That does not work. TypeScript **collapses** it: since every member of `KnownApi` is also a
`string`, the union simplifies to plain `string`, and your editor loses the ten suggestions. The type is still correct,
but the autocomplete is gone, which was the whole point.

`string & {}` is the workaround. It means "a `string`, intersected with the empty object type." Semantically that is
still just `string`. But it is not *literally* the type `string`, so TypeScript cannot collapse the union, and the ten
literals survive as autocomplete suggestions.

The practical effect, in an editor:

```ts
const a: Api = "anthropic-messages";  // suggested by autocomplete
const b: Api = "my-weird-local-proxy"; // accepted, no error
```

**Why pi needs this:** `Api` names a *wire format* — the request and response shape of an HTTP API. pi ships ten of them.
But the whole point of the package is that you can point it at a server it has never heard of, including one running on
your laptop. A closed union would make that impossible. Plain `string` would make it undiscoverable. The trick gives you
both.

You will see the same pattern for providers on line 76: `ProviderId = KnownProvider | string`. Read that line and notice
it is spelled *differently* — plain `string`, no `& {}`.

**Questions to answer:**

- Why does `KnownApi | string` collapse to `string`, but `KnownApi | (string & {})` does not?

:::{dropdown} Answer
TypeScript simplifies unions by removing members that are **subtypes** of another member. `"anthropic-messages"` is a
subtype of `string` — every value of the first type is a valid value of the second — so in the union `"anthropic-messages"
| string`, the literal is redundant and gets dropped. Do that for all ten and nothing is left but `string`.

`string & {}` is an **intersection**: a value must satisfy both `string` and `{}`. Since every non-null string already
satisfies `{}`, the set of values is the same as `string`. But the compiler's simplification step works on type
*structure*, not on the set of values it denotes. It does not recognize `string & {}` as identical to `string`, so it
cannot use it to absorb the literals, and all ten survive.

This is a deliberate exploit of an implementation detail. It is widely used, has a nickname
(the "open enum" or "literal union with autocomplete" pattern), and is stable in practice — but it is a trick, not a
language feature.
:::

- Line 76 is `export type ProviderId = KnownProvider | string;` — plain `string`, without the `& {}`. What does that
  type actually equal, and is it a bug?

:::{dropdown} Answer
It equals exactly `string`. The union collapses, and the 41 provider literals are gone as far as the compiler and your
autocomplete are concerned.

Is it a bug? Not a correctness bug — the type still accepts every value it should accept, and rejects nothing it should
accept. `ProviderId` is used to *record* which provider produced a message, so anything a config file names is legal, and
`string` is honest about that.

It is a small loss of editor help. Someone typing `provider: ` at a `ProviderId` position gets no suggestions where they
could have gotten 41. Whether that is worth a `& {}` is a judgment call, and pi made a different call for `Api` (line 29)
than for `ProviderId` (line 76).

The reason this question is worth asking: it is very easy to write `Known | string` believing you preserved the literals.
You did not. If you want them, you have to write the trick.
:::

---

## Pass 3: Content Blocks — The Discriminated Union (Lines 332-368)

This is the most important pass in the module. Read lines 338-368:

```ts
export interface TextContent {
	type: "text";
	text: string;
	textSignature?: string;
}

export interface ThinkingContent {
	type: "thinking";
	thinking: string;
	thinkingSignature?: string;
	redacted?: boolean;
}

export interface ImageContent {
	type: "image";
	data: string;      // base64 encoded image data
	mimeType: string;  // e.g., "image/jpeg", "image/png"
}

export interface ToolCall {
	type: "toolCall";
	id: string;
	name: string;
	arguments: Record<string, any>;
	thoughtSignature?: string;
	namespace?: string;
}
```

Four interfaces. Each has a `type` field whose type is a **single string literal**. That is the whole pattern, and it is
the backbone of pi.

**What a discriminated union is:** a union of object types where every member has a common field holding a distinct
literal value. That field is the **discriminant**. Once you check it, TypeScript *narrows* the type to the matching
member, and you get access to that member's fields and no others.

```ts
function describe(block: TextContent | ThinkingContent | ImageContent | ToolCall): string {
	if (block.type === "text") {
		return block.text;      // OK: narrowed to TextContent
	}
	if (block.type === "toolCall") {
		return block.name;      // OK: narrowed to ToolCall
	}
	// return block.text;       // Error: `text` does not exist on ThinkingContent | ImageContent
	return "(other)";
}
```

That narrowing is the payoff. You did not cast anything. You did not call `isinstance`. You compared a string, and the
compiler followed along.

**Python parallel:** This is a tagged union, and Python can express it:

```python
class TextContent(BaseModel):
    type: Literal["text"]
    text: str

class ToolCall(BaseModel):
    type: Literal["toolCall"]
    id: str
    name: str
    arguments: dict[str, Any]

Content = Annotated[TextContent | ToolCall, Field(discriminator="type")]
```

You have probably written exactly this with pydantic. The difference is which one is the *default*. In Python, the
instinct for "four kinds of content block" is a base class and four subclasses; the tagged union is the thing you reach
for when you need pydantic to parse it. In TypeScript, the tagged union *is* the instinct, and inheritance is rare.

Count the classes in pi's core types file: zero. Count the interfaces: about forty. That ratio is not an accident, and it
is not because TypeScript lacks classes. It has them, with inheritance, abstract methods, and access modifiers. pi mostly
does not use them for data.

**Why not?** Because the data has to cross a wire. Every message in pi gets serialized to JSON, written to a session
file, or sent to an HTTP API. A class instance loses its identity the moment you `JSON.stringify` it — what comes back is
a plain object with the same fields and no methods, and no `instanceof` will recognize it. A discriminated union survives
the round trip perfectly, because the discriminant is *data*. It is a field in the JSON.

**Optional properties:** notice `textSignature?: string`. The `?` makes the property optional. It means the field may be
absent entirely.

This is a real distinction that Python blurs, and it matters:

| Spelling | Absent allowed? | Explicit `undefined` allowed? | Python analogue |
| --- | --- | --- | --- |
| `x: string` | no | no | `x: str` |
| `x?: string` | yes | yes | `x: str = None`, roughly |
| `x: string \| undefined` | **no** | yes | `x: str \| None`, required |
| `x?: string \| undefined` | yes | yes | — |

The third row is the one that surprises people. `x: string | undefined` means the key **must be present**, and its value
may be `undefined`. You have to write `{ x: undefined }`, not `{}`. pi uses the `?` form nearly everywhere, which is why
optional fields in pi can simply be left out.

**Questions to answer:**

- Why does `ImageContent` store `data: string` instead of raw bytes?

:::{dropdown} Answer
Because the value has to survive `JSON.stringify`, and JSON has no byte type. The comment says it: base64.

TypeScript does have real binary types (`Uint8Array`, `ArrayBuffer`). pi uses them where bytes stay in memory. But an
`ImageContent` block goes into a `Message`, which goes into a `Context`, which gets serialized both to a provider's HTTP
API and to a session file on disk. Anything in that path has to be JSON-representable, so images are base64 text and
`mimeType` carries what the bytes actually are.

This is the same reason `arguments: Record<string, any>` on `ToolCall` is a plain object and not a parsed, typed
structure: the wire format is JSON, so the in-memory shape mirrors JSON.
:::

- `ToolCall` has `type: "toolCall"` — camelCase — while `TextContent` has `type: "text"`. Why does the exact string
  matter at all, given they are just labels?

:::{dropdown} Answer
Because the string **is** the runtime representation. It is not a label the compiler invents for its own bookkeeping; it
is a literal value that gets written into JSON, sent to a provider, saved in a session file, and read back later.

That has two consequences. First, changing `"toolCall"` to `"tool_call"` is a **wire format change**, not a rename. Old
session files on disk still contain the old string, and code that switches on the new one will silently fail to match
them. Second, the compiler cannot help you find every place the string appears in data — only in code.

So the discriminant values are effectively frozen once anything has been persisted. That is the trade you accept for
using data as the type tag. It is also why `Api` and `ProviderId` values look like slugs: they are stored, not just
compared.
:::

---

## Pass 4: Usage, and Why a Harness Counts Tokens (Lines 370-393)

Read lines 370-393:

```ts
export interface Usage {
	input: number;
	output: number;
	cacheRead: number;
	cacheWrite: number;
	cacheWrite1h?: number;
	reasoning?: number;
	totalTokens: number;
	cost: {
		input: number;
		output: number;
		cacheRead: number;
		cacheWrite: number;
		total: number;
	};
}

export type StopReason = "pending" | "stop" | "length" | "toolUse" | "error" | "aborted" | "deferred";
```

Two small things to notice about the TypeScript, and one big thing to notice about the design.

**TypeScript, first.** `cost` is an **inline object type**. There is no named `Cost` interface; the shape is written
directly where it is used. This is normal and idiomatic. In Python you would almost always define a separate
`class Cost(BaseModel)`, because there is no syntax for an anonymous structured type. TypeScript has one, so small
one-use shapes stay inline.

Also: `number` is the only numeric type here. TypeScript has no `int` and no `float`. `number` is an IEEE-754 double,
exactly Python's `float`. Token counts are integers by convention, not by type. (There is a `bigint`, for arbitrary
precision integers, and pi does not use it.)

**Now the design.** Look at what `Usage` distinguishes: input tokens, output tokens, tokens read from cache, tokens
written to cache, and — separately — a one-hour-retention subset of the cache writes. Then a parallel breakdown of cost
in dollars.

That is a lot of structure for "how many tokens did that cost." It is there because these numbers have different prices.
A cached input token can cost a tenth of a fresh one. An output token can cost five times an input token. A harness that
tracks a single `total_tokens` number cannot tell you why your bill looks the way it does, and cannot make decisions
based on it.

And `reasoning?: number` carries a documented subtlety worth reading the comment for: reasoning tokens are a **subset**
of `output`, already included in it. Adding them would double count. The `?` is doing real work — it is `undefined` for
providers that do not report the breakdown, which is different from `0`.

**`StopReason`** is another string literal union, and it is worth reading as a list of everything that can end a model's
turn: it finished (`stop`), it hit the token limit (`length`), it wants to call a tool (`toolUse`), something broke
(`error`), the user cancelled (`aborted`), it has not finished yet (`pending`), or the result will arrive later
(`deferred`).

`toolUse` is the one that makes an agent an agent. That value is what the loop checks to decide whether to go around
again. We build that loop in Module 2.

**Questions to answer:**

- Why is `cacheWrite1h` optional while `cacheWrite` is required?

:::{dropdown} Answer
Because only one provider reports the split. The comment says so: "Only Anthropic reports this split."

`cacheWrite` is required because pi can always produce a number for it — zero if there were no cache writes. But
`cacheWrite1h` is a *subset* of that number, and for a provider that does not break it down, pi genuinely does not know
what it is. `0` would be a lie: it would claim there were no 1-hour cache writes, when the truth is that the information
is unavailable.

This is the distinction between "zero" and "unknown," and it is exactly what optional properties are for. Same reasoning
applies to `reasoning?`.
:::

- Python's `int` and `float` are separate types. TypeScript has only `number`. Where could that bite a harness?

:::{dropdown} Answer
Anywhere an integer is required and arithmetic can produce a fraction. Three realistic spots in a harness:

**Token budgets.** Divide a context window to decide how much to keep during compaction — `contextWindow * 0.7` — and you
get `137011.19999999999`. Pass that to something expecting a count and you may get a rejected request. The fix is
explicit: `Math.floor(...)`.

**Array indexing.** `messages[i / 2]` with an odd `i` is `undefined` at runtime, with no error, because a non-integer
index simply does not match a key. Python raises `TypeError` here.

**Float precision on costs.** `0.1 + 0.2` is `0.30000000000000004` in both languages, but Python at least offers
`Decimal`. TypeScript's usual answer is to compute in the smallest unit (or accept the noise, which pi does — these are
display values, not billing).

The type checker will not warn you about any of these. `number` is `number`.
:::

---

## Pass 5: The Three Messages (Lines 409-455)

Read lines 409-455. This is the center of the file. Stripped of comments:

```ts
export interface UserMessage {
	role: "user";
	content: string | (TextContent | ImageContent)[];
	timestamp: number;
}

export interface AssistantMessage {
	role: "assistant";
	content: (TextContent | ThinkingContent | ToolCall)[];
	api: Api;
	provider: ProviderId;
	model: string;
	responseModel?: string;
	responseId?: string;
	diagnostics?: AssistantMessageDiagnostic[];
	usage: Usage;
	stopReason: StopReason;
	deferred?: DeferredHandle;
	errorMessage?: string;
	rawStopReason?: string;
	endTurn?: boolean;
	timestamp: number;
}

export interface ToolResultMessage<TDetails = any> {
	role: "toolResult";
	toolCallId: string;
	toolName: string;
	content: (TextContent | ImageContent)[];
	details?: TDetails;
	usage?: Usage;
	addedToolNames?: string[];
	isError: boolean;
	timestamp: number;
}

export type Message = UserMessage | AssistantMessage | ToolResultMessage;
```

**Read line 455 first.** `Message` is a union of three, discriminated on `role`. That single line is the data model of
every agent conversation in pi. A session is a `Message[]`. Compaction rewrites a `Message[]`. The TUI renders a
`Message[]`. The provider adapters translate a `Message[]` into somebody's JSON.

Now notice what the three members are *not*. There is no `SystemMessage`. The system prompt lives on `Context`, which we
read in the next pass — it is a property of the conversation, not a message in it. And there is no base
`Message` interface that the three extend. The union is the abstraction.

**Three observations worth internalizing:**

**1. Content is a list of blocks, never a string** (except for the convenience case on `UserMessage`, which allows a bare
`string`). An assistant turn is a *sequence*: some text, then some thinking, then two tool calls. That is why streaming a
response means emitting events about *blocks at an index*, which is exactly what Pass 7 shows.

**2. `AssistantMessage` carries its own provenance.** `api`, `provider`, `model`, `usage`, `stopReason`. The message
records which model produced it and what it cost. This is not decoration. If you switch models mid-conversation — pi lets
you — the transcript still knows which turn came from where, and the running cost stays correct. A design that kept
"current model" outside the messages would lose that.

**3. `ToolResultMessage` is a message, not a return value.** A tool result goes into the transcript as a first-class turn,
alongside the user's words and the model's. This is the structural reason a harness is a *loop* rather than a function
call: the result of running a tool is more conversation.

**The generic:** `ToolResultMessage<TDetails = any>`.

`<TDetails>` is a **type parameter**, and `= any` is its **default**. This is Python's `TypeVar` plus `Generic`:

```python
TDetails = TypeVar("TDetails", default=Any)

class ToolResultMessage(BaseModel, Generic[TDetails]):
    details: TDetails | None = None
```

The purpose: `content` is what the *model* sees — text and images. `details` is what *your application* sees — the
structured result. When the `read` tool runs, `content` holds the file text for the model, and `details` holds something
like the line count and truncation flag for your UI. Different consumers, different shapes.

The default matters for ergonomics. Because of `= any`, code that does not care can write `ToolResultMessage` with no
angle brackets, which is why line 455 can say `| ToolResultMessage` plainly. Code that does care writes
`ToolResultMessage<ReadToolDetails>` and gets a typed `details`.

**Questions to answer:**

- `UserMessage.content` is `string | (TextContent | ImageContent)[]`. Why allow both?

:::{dropdown} Answer
Ergonomics at the boundary where humans write code. The common case is a plain text prompt, and
`{ role: "user", content: "hello" }` is much nicer to write than
`{ role: "user", content: [{ type: "text", text: "hello" }] }`.

The cost is that every consumer must handle both shapes, and this narrowing appears all over pi:

```ts
const text = typeof message.content === "string" ? message.content : message.content.map((c) => c.text).join("");
```

Note `typeof message.content === "string"` — that is TypeScript narrowing on a union of a primitive and an array, using
`typeof` rather than a discriminant field. Primitives do not have a `type` field to check, so `typeof` is the tool.

You will face the same choice in Project 2, and the Python is the same shape:

```python
text = message.content if isinstance(message.content, str) else "".join(c.text for c in message.content)
```

Whether the convenience is worth the branch is a real design question. pi decided yes for `UserMessage` — the one
application code constructs by hand — and no for `AssistantMessage`, which pi itself builds from a stream and where the
list is always the right shape.
:::

- `AssistantMessage` has both `stopReason: StopReason` and `rawStopReason?: string`. Why keep both?

:::{dropdown} Answer
`stopReason` is pi's normalized vocabulary — one of seven known values that the agent loop can branch on. `rawStopReason`
is whatever the provider actually said.

You need the normalized one because the loop must make a decision, and it cannot have a branch for every string that
forty providers might invent. You need the raw one because normalization loses information, and when a provider stops for
a reason pi has never seen, `stopReason: "stop"` plus `rawStopReason: "content_filter"` is debuggable while `"stop"` alone
is not.

This is a general pattern for adapter layers: normalize for control flow, keep the original for diagnosis. You will see
it again in Module 1, when we write the provider adapters that do the normalizing.
:::

---

## Pass 6: Tool and Context — The Whole Interface to a Model (Lines 478-513)

Read lines 478-513. First, notice something odd on line 478:

```ts
import type { TSchema } from "typebox";
```

An `import` statement, 478 lines into the file. This is legal: ES module imports are **hoisted**, so their position in
the file has no effect. It is unusual style, but it is not a bug, and it tells you something useful — imports in
TypeScript are declarations, not statements that execute in order.

(Do not confuse this with what pi's `AGENTS.md` forbids. The banned thing is a *dynamic* import — `await import("pkg")`
inside a function — which is a runtime call with real consequences for load order. A top-level import halfway down a file
is still a top-level import.)

Now the two interfaces:

```ts
export interface Tool<TParameters extends TSchema = TSchema> {
	name: string;
	description: string;
	parameters: TParameters;
	constrainedSampling?: false | ConstrainedSamplingConfig;
}

export interface Context {
	systemPrompt?: string;
	messages: Message[];
	tools?: Tool[];
}
```

**`Context` is the entire input to a model.** Three fields. A system prompt, a list of messages, a list of tools. That is
everything a harness sends. Every feature you have ever used in a coding agent — file reading, memory, skills, subagents,
plan mode — ends up as text in one of those three fields. There is no fourth channel.

Sit with that for a moment, because it is the most useful thing in this module. When you later wonder "how does feature X
work," the answer is always "it puts something in the system prompt, adds a message, or adds a tool." The rest is
plumbing.

**`Tool` is where types stop being enough.** Look at `parameters: TParameters`, constrained by `extends TSchema`.

`TSchema` comes from **TypeBox**, a library for building JSON Schema objects that also produces TypeScript types from
them. Why does pi need a schema library at all, when it has a type system?

Because the model needs the parameter shape **at runtime**. pi has to serialize the tool's parameters into JSON Schema
and put it in the HTTP request, so the model knows what arguments to produce. A TypeScript `interface` cannot do that. It
is erased. There is nothing left at runtime to serialize.

So a tool carries its schema as a **value**:

```ts
const writeSchema = Type.Object({
	path: Type.String({ description: "Path to the file to write (relative or absolute)" }),
	content: Type.String({ description: "Content to write to the file" }),
});

export type WriteToolInput = Static<typeof writeSchema>;
```

Those two lines are from [`write.ts`](https://github.com/earendil-works/pi/blob/v0.84.2/packages/agent/src/harness/tools/write.ts#L8-L13),
which we read in Part B. `writeSchema` is a real object that exists at runtime and can be sent to a provider.
`Static<typeof writeSchema>` derives the static type `{ path: string; content: string }` from it.

**Python parallel:** this is pydantic, and the parallel is unusually exact.

| | Python | TypeScript |
| --- | --- | --- |
| Define once | `class WriteInput(BaseModel)` | `Type.Object({ ... })` |
| Get the runtime schema | `WriteInput.model_json_schema()` | the object itself |
| Get the static type | the class is the type | `Static<typeof writeSchema>` |
| Validate a payload | `WriteInput(**data)` | `Value.Check(schema, data)` |

The direction is what differs. In Python you write a class and *ask* it for a schema. In TypeScript you write a schema
and *derive* a type from it. Same information, opposite starting point — because in Python the class survives to runtime,
and in TypeScript only the schema does.

`typeof writeSchema` in a type position is the operator that crosses the boundary: it takes a *value* and gives you its
*type*. There is no Python equivalent because Python does not need one.

**Questions to answer:**

- Everything a harness can do reduces to three fields on `Context`. So how could a "memory" feature work?

:::{dropdown} Answer
It has to be one of the three, and in practice it is a combination:

**As system prompt text.** Read a `MEMORY.md` at startup and append its contents to `systemPrompt`. Cheap, always
present, costs tokens on every single request.

**As a tool.** Give the model `remember(fact)` and `recall(query)` tools. Costs nothing until used, but the model has to
decide to use them, and it often will not.

**As messages.** Inject prior facts as a synthetic user or tool-result message near the start of the transcript.

Real harnesses use all three for different things, and the trade is always the same: system prompt is reliable but always
paid for; tools are cheap but only work if the model reaches for them.

The point of the exercise is that once you accept there are only three channels, the design space for any feature becomes
small and concrete.
:::

- `constrainedSampling?: false | ConstrainedSamplingConfig`. Why is `false` a valid value, when the property is already
  optional?

:::{dropdown} Answer
Because absent and `false` mean different things. Absent means "no preference, do whatever the default is." `false` means
"explicitly off, do not do this."

That distinction only matters if something else can supply a default — and it can. A provider or model entry can turn
constrained sampling on for all its tools, and a single tool needs a way to opt out. `undefined` would be
indistinguishable from "not configured," and would inherit the default. `false` overrides it.

This three-state pattern — absent, explicitly off, explicitly configured — shows up all over pi's config types. Python
often reaches for a sentinel object to get the same effect, because `None` is usually already spoken for.

The feature itself, constrained sampling, is how you force a weak model to emit valid tool-call JSON by restricting what
tokens it may produce. It matters most for small local models. We use it in Module 1.
:::

---

## Pass 7: The Event Union, and `Extract` (Lines 515-539)

Read lines 523-539:

```ts
export type AssistantMessageEvent =
	| { type: "start"; partial: AssistantMessage }
	| { type: "text_start"; contentIndex: number; partial: AssistantMessage }
	| { type: "text_delta"; contentIndex: number; delta: string; partial: AssistantMessage }
	| { type: "text_end"; contentIndex: number; content: string; partial: AssistantMessage }
	| { type: "thinking_start"; contentIndex: number; partial: AssistantMessage }
	| { type: "thinking_delta"; contentIndex: number; delta: string; partial: AssistantMessage }
	| { type: "thinking_end"; contentIndex: number; content: string; partial: AssistantMessage }
	| { type: "toolcall_start"; contentIndex: number; partial: AssistantMessage }
	| { type: "toolcall_delta"; contentIndex: number; delta: string; partial: AssistantMessage }
	| { type: "toolcall_end"; contentIndex: number; toolCall: ToolCall; partial: AssistantMessage }
	| {
			type: "done";
			reason: Extract<StopReason, "stop" | "length" | "toolUse" | "deferred">;
			message: AssistantMessage;
	  }
	| { type: "error"; reason: Extract<StopReason, "aborted" | "error">; error: AssistantMessage };
```

Twelve members, written as **inline object types** rather than named interfaces. Same discriminated union pattern as
Pass 3, spelled compactly because none of these shapes is needed by name elsewhere.

**Read the doc comment above it (lines 515-522).** It states a protocol: emit `start` first, then partial updates, then
terminate with exactly one of `done` or `error`. That contract is not expressible in the type — nothing stops you from
pushing two `done` events — so it is written in prose and enforced by the code that produces the stream. Worth noticing
how often the interesting invariant is the one the type system cannot hold.

**The shape of the protocol** is three-phase per block: `*_start`, then many `*_delta`, then `*_end`. Repeated for text,
thinking, and tool calls. Every event carries `contentIndex`, saying which block of `AssistantMessage.content` it is
about — that is why content is a list (Pass 5).

Every event also carries `partial: AssistantMessage`: the whole message as it stands so far. That is redundant with the
deltas, and deliberately so. A consumer that wants to re-render everything (a TUI) uses `partial`. A consumer that wants
to append (writing to stdout) uses `delta`. Neither has to keep its own copy.

Redundant, but not free — `partial` grows with the message, and it is attached to every event. pi strips it before events
go over a wire, in [`json-event.ts`](https://github.com/earendil-works/pi/blob/v0.84.2/packages/coding-agent/src/modes/json-event.ts),
which is the third file we read in Part B.

**Now the new TypeScript.** Look at the `done` member:

```ts
reason: Extract<StopReason, "stop" | "length" | "toolUse" | "deferred">;
```

`Extract<T, U>` is a **utility type**: given a union `T`, it keeps only the members assignable to `U`. So this evaluates
to `"stop" | "length" | "toolUse" | "deferred"` — the subset of `StopReason` that counts as a successful ending. The
`error` member uses it to take `"aborted" | "error"` instead.

Why not just write the four literals directly? Because `Extract` creates a **dependency**. If someone removes `"deferred"`
from `StopReason`, this line becomes an error — `Extract` cannot find it. Hardcoded literals would silently disagree with
`StopReason` forever.

There is a family of these built in. The ones you will meet in pi:

| Utility | Meaning | Rough Python analogue |
| --- | --- | --- |
| `Extract<T, U>` | union members of `T` assignable to `U` | — |
| `Exclude<T, U>` | union members of `T` *not* assignable to `U` | — |
| `Omit<T, K>` | object type `T` without keys `K` | — |
| `Pick<T, K>` | object type `T` with only keys `K` | — |
| `Partial<T>` | all properties of `T` made optional | `total=False` TypedDict |
| `Record<K, V>` | object with keys `K` and values `V` | `dict[K, V]` |

Only the last two have Python counterparts, and that is the honest summary: **this is new muscle.** Python has no way to
compute a type by filtering another type's members. Do not look for an analogy; there isn't one. Read
`Extract<StopReason, "stop" | ...>` as a small expression evaluated by the compiler, whose result is a type.

You can see both used in anger. `Extract` pulls one member out of a union, in
[`json-event.ts`](https://github.com/earendil-works/pi/blob/v0.84.2/packages/coding-agent/src/modes/json-event.ts#L20-L21):

```ts
type MessageUpdateEvent = Extract<AgentSessionEvent, { type: "message_update" }>;
type JsonMessageUpdateEvent = Extract<JsonAgentSessionEvent, { type: "message_update" }>;
```

`Exclude` does the opposite, and pi uses it to *replace* a union member. This is where `AgentSessionEvent` — the very
type those two lines filter — gets built, in
[`agent-session.ts`](https://github.com/earendil-works/pi/blob/v0.84.2/packages/coding-agent/src/core/agent-session.ts#L140-L148):

```ts
/** Session-specific events that extend the core AgentEvent */
export type AgentSessionEvent =
	| Exclude<AgentEvent, { type: "agent_end" }>
	| {
			type: "agent_end";
			messages: AgentMessage[];
			willRetry: boolean;
	  }
	| { type: "agent_settled" }
```

Read the `Exclude` line together with the `agent_end` block under it as one sentence: "every core agent event except
`agent_end`, plus my extended version of `agent_end`." That is a type-level `replace`, and it stays correct as events are
added.

**Questions to answer:**

- Every event carries `partial: AssistantMessage`. What is the cost, and why is it worth paying anyway?

:::{dropdown} Answer
The cost is quadratic in message size. Each event holds the full message so far, so streaming a 10,000-token reply one
delta at a time means the sum of all `partial` snapshots is enormous. In-process this is cheap — `partial` is the *same
object* by reference, not a copy, so it costs one pointer per event. That is the key detail.

It becomes expensive the moment events cross a process boundary, because serialization copies. That is exactly why
`json-event.ts` exists: it strips `partial` for the wire, keeping only the constant-size pieces (usage, tool-call ids,
names). Its doc comment spells out the reasoning.

So the answer is: in-process it is nearly free and saves every consumer from maintaining its own accumulator; across a
wire it is unaffordable and gets removed. The design pays the cost only where it is cheap.
:::

- What breaks if a stream emits `done` and then keeps pushing `text_delta` events?

:::{dropdown} Answer
Nothing in the type system — the union permits any sequence. The breakage is at runtime, and it depends on the consumer.

In pi it is handled structurally rather than defended against. `EventStream` (Part B of Module 0's Concept 5, and read in
full there) has a `done` flag: `push()` returns immediately once a terminal event has arrived. So late events are silently
dropped rather than corrupting anything.

That is the general shape of the answer for protocols a type system cannot express: you cannot make the illegal state
unrepresentable, so you make it harmless. Either ignore it, or throw loudly. Choosing to ignore is only safe when the
sender is code you control.
:::

---

## Pass 8: `Model.compat` — A Conditional Type (Lines 794-823)

This pass is a **preview**, and the one construct in this module you will never write. Read it to recognize it, and to
understand the problem it solves — you will solve the same problem far more simply in Module 1. Do not try to reproduce
it in Python; there is no way to, and no reason to.

```ts
export interface Model<TApi extends Api> {
	id: string;
	name: string;
	api: TApi;
	provider: ProviderId;
	baseUrl: string;
	reasoning: boolean;
	thinkingLevelMap?: ThinkingLevelMap;
	input: ("text" | "image")[];
	cost: ModelCost;
	contextWindow: number;
	maxTokens: number;
	samplingParams?: Record<string, unknown>;
	headers?: Record<string, string>;
	compat?: TApi extends "openai-completions"
		? OpenAICompletionsCompat
		: TApi extends "openai-responses" | "azure-openai-responses" | "openai-codex-responses"
			? OpenAIResponsesCompat
			: TApi extends "anthropic-messages"
				? AnthropicMessagesCompat
				: TApi extends "bedrock-converse-stream"
					? BedrockCompat
					: never;
}
```

Ignore everything except `compat`. That is a **conditional type**: a chain of `T extends X ? A : B` at the type level. It
reads as a ladder of if/else, evaluated by the compiler:

```
if    TApi is "openai-completions"                    -> compat is OpenAICompletionsCompat
elif  TApi is one of the three responses APIs         -> compat is OpenAIResponsesCompat
elif  TApi is "anthropic-messages"                    -> compat is AnthropicMessagesCompat
elif  TApi is "bedrock-converse-stream"               -> compat is BedrockCompat
else                                                  -> compat is never
```

`never` is the empty type: no value inhabits it. Landing on `never` means the property cannot be given any value at all.
So for a model whose `api` is anything else, `compat` is unusable — which is the intended message: there are no
compatibility flags defined for that wire format.

**Python has no counterpart.** Not `Union`, not `overload`, not `TypeVar` bounds. A type whose *shape* is computed from
another type's *value* is genuinely absent from Python. Flag this as new, do not analogize it.

**Why it is here** is the interesting part, and it is the thread that runs through Module 1.

`Model<TApi>` describes one model you can talk to. `compat` holds the flags for "this server is *almost*
OpenAI-compatible, but it differs in these ways." Read the fields of `OpenAICompletionsCompat` (lines 545-605) — there are
dozens: `supportsStore`, `supportsDeveloperRole`, `supportsReasoningEffort`, and so on.

Those flags are what make a harness work against a server it has never seen. A local Ollama or vLLM instance speaks
something *close* to the OpenAI completions API, and diverges in small ways. Each divergence is a flag. From pi's
[models doc](https://github.com/earendil-works/pi/blob/v0.84.2/packages/coding-agent/docs/models.md):

```json
{
  "providers": {
    "ollama": {
      "baseUrl": "http://localhost:11434/v1",
      "api": "openai-completions",
      "apiKey": "ollama",
      "compat": { "supportsDeveloperRole": false, "supportsReasoningEffort": false },
      "models": [{ "id": "gpt-oss:20b", "reasoning": true }]
    }
  }
}
```

The conditional type is what makes that config typo-proof. Because `api` is `"openai-completions"`, `TApi` is that
literal, and `compat` resolves to `OpenAICompletionsCompat` — so an Anthropic-only flag in that block is a compile error,
not a silently ignored key.

**One question to answer:**

- What is the practical benefit over just making `compat` a big optional object with every provider's flags in it?

:::{dropdown} Answer
A single flat object would type-check a config that mixes flags from different wire formats. You could write an
Anthropic-specific flag on an OpenAI model, and nothing would complain — it would just be ignored at runtime, silently,
and you would spend an hour wondering why your setting has no effect.

The conditional type moves that from a silent runtime no-op to a compile error, and it does it without pi having to write
a separate `OpenAIModel` / `AnthropicModel` / `BedrockModel` interface for every wire format. One interface, one type
parameter, and each instantiation gets exactly the right flag set.

That is the real argument for conditional types in general: they let one generic definition stand in for what would
otherwise be N hand-written variants that drift apart.
:::
