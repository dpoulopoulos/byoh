# Part B: Guided Reading of Three Complete Files

Part A read one big file in slices. Now read three small files end to end. Each is complete, real, and short enough to
hold in your head at once.

## File 1: system-prompt.ts (34 lines)

Open [`packages/agent/src/harness/system-prompt.ts`](https://github.com/earendil-works/pi/blob/v0.84.2/packages/agent/src/harness/system-prompt.ts).
This file turns a list of skills into a block of text for the system prompt. It is the simplest complete module in pi, and
it contains six pieces of JavaScript you need.

```ts
import type { Skill } from "./types.ts";

export function formatSkillsForSystemPrompt(skills: Skill[]): string {
	const visibleSkills = skills.filter((skill) => !skill.disableModelInvocation);
	if (visibleSkills.length === 0) return "";

	const lines = [
		"The following skills provide specialized instructions for specific tasks.",
		"Read the full skill file when the task matches its description.",
		"When a skill file references a relative path, resolve it against the skill directory (parent of SKILL.md / dirname of the path) and use that absolute path in tool commands.",
		"",
		"<available_skills>",
	];

	for (const skill of visibleSkills) {
		lines.push("  <skill>");
		lines.push(`    <name>${escapeXml(skill.name)}</name>`);
		lines.push(`    <description>${escapeXml(skill.description)}</description>`);
		lines.push(`    <location>${escapeXml(skill.filePath)}</location>`);
		lines.push("  </skill>");
	}

	lines.push("</available_skills>");
	return lines.join("\n");
}

function escapeXml(value: string): string {
	return value
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&apos;");
}
```

**1. Two functions, one exported.** `formatSkillsForSystemPrompt` has `export`; `escapeXml` does not. Without `export`, a
name is private to the file — genuinely inaccessible from outside, not private-by-convention. There is no `_` prefix
needed, and no way to reach in.

**2. `Skill[]` is an array type.** `Skill[]` is `list[Skill]`. The alternative spelling `Array<Skill>` means the same
thing; pi uses the bracket form.

**3. `.filter((skill) => !skill.disableModelInvocation)`.** An **arrow function** — `(x) => expr` is `lambda x: expr`.
Unlike Python's `lambda`, it can hold a full body in braces and can be `async`.

`.filter` is a method on arrays, not a builtin taking a callable, so it reads left to right:

| Python | TypeScript |
| --- | --- |
| `[s for s in skills if not s.disabled]` | `skills.filter((s) => !s.disabled)` |
| `[s.name for s in skills]` | `skills.map((s) => s.name)` |
| `any(s.disabled for s in skills)` | `skills.some((s) => s.disabled)` |
| `all(s.disabled for s in skills)` | `skills.every((s) => s.disabled)` |
| `next((s for s in skills if p(s)), None)` | `skills.find((s) => p(s))` |
| `len(skills)` | `skills.length` |

TypeScript has no comprehension syntax. `.map` and `.filter` chains are the idiom, and they chain well.

Also note `!skill.disableModelInvocation` on an optional boolean. When the field is absent it is `undefined`, and `!undefined`
is `true`. So a skill that never mentions the flag is visible. That is the intended default, achieved by relying on
falsiness — idiomatic here, and a trap in general (see [Concept 3](part_c_concepts.md#concept-3-absent-null-and-set--reading-pis-optional-fields)).

**4. Build a list of lines, then `join`.** `lines.join("\n")` is `"\n".join(lines)`. Same operation, receiver and argument
swapped. String concatenation in a loop would work too; this is the conventional form in both languages, for the same
reason.

**5. Template literals.** `` `    <name>${escapeXml(skill.name)}</name>` `` uses backticks, and `${...}` interpolates any
expression. This is an f-string. Backticks also allow real newlines inside the literal, which makes them the only
multi-line string syntax — there is no `"""`.

**6. `.replace(/&/g, "&amp;")`.** Regex literals are written between slashes: `/&/g`. No quotes, no `re.compile`. The
trailing `g` is the **global** flag, meaning replace every match. Without it, `.replace` replaces only the first — which is
a classic bug, because `"a&b&c".replace(/&/, "+")` gives `"a+b&c"` and looks almost right.

Note the order of the five replacements: `&` is escaped **first**. Reverse it and `<` becomes `&lt;`, then the `&` in
`&lt;` gets escaped to `&amp;lt;`. Double-escaping is a real bug and this ordering is the fix.

**Why this file exists at all:** it is the concrete answer to "how do skills work." A skill is a markdown file. Its name,
description, and path get formatted into an XML block. That block goes into `Context.systemPrompt`. The model reads the
descriptions and decides to `read` the file when relevant.

That is the whole mechanism. No new channel, no special protocol — just text in the system prompt, exactly as
[Pass 6](part_a_types.md#pass-6-tool-and-context--the-whole-interface-to-a-model-lines-478-513) predicted.

**Questions to answer:**

- `escapeXml` is not exported. What would change if it were?

:::{dropdown} Answer
Functionally nothing, immediately. What changes is the file's contract.

An exported name is something other code can depend on, which means it cannot be renamed or removed without checking
every caller. A non-exported name can be rewritten freely, because the compiler can see every use of it — they are all in
this file.

pi's `AGENTS.md` pushes further in that direction: "Inline single-line helpers that have only one call site." The
guideline is that a helper should exist because it is used more than once or because naming it makes the code clearer, not
by default.
:::

- Why escape `&` before `<`, and what exactly goes wrong if you swap them?

:::{dropdown} Answer
Because the replacement text for the others *contains* `&`, so escaping `&` last would escape the escapes.

Trace `"<b>"` with the order reversed — `<` first, then `&`:

1. `.replace(/</g, "&lt;")` gives `"&lt;b>"`
2. `.replace(/&/g, "&amp;")` now finds the `&` that step 1 introduced, giving `"&amp;lt;b>"`

The model receives `&amp;lt;b>` and reads the literal text `&lt;b>` instead of `<b>`. With `&` first, its own escape is
already done before any `&`-containing replacement is introduced, and nothing is escaped twice.

This ordering rule applies to every escaping function you will ever write: **escape the escape character first.**
:::

---

## File 2: write.ts (39 lines)

Open [`packages/agent/src/harness/tools/write.ts`](https://github.com/earendil-works/pi/blob/v0.84.2/packages/agent/src/harness/tools/write.ts).
This is a complete tool — one of the things the model can actually invoke. Every tool in pi has this shape.

```ts
import { type Static, Type } from "typebox";
import type { AgentHarnessTool } from "../types.ts";
import { getOrThrow } from "../types.ts";
import { withFileMutationQueue } from "./file-mutation-queue.ts";
import { resolveToolPath } from "./path-utils.ts";
import type { ExecutionToolContext } from "./tool-context.ts";

const writeSchema = Type.Object({
	path: Type.String({ description: "Path to the file to write (relative or absolute)" }),
	content: Type.String({ description: "Content to write to the file" }),
});

export type WriteToolInput = Static<typeof writeSchema>;

export function createWriteTool<TContext extends ExecutionToolContext = ExecutionToolContext>(): AgentHarnessTool<
	TContext,
	typeof writeSchema,
	undefined
> {
	return {
		name: "write",
		label: "write",
		description:
			"Write content to a file. Creates the file if it doesn't exist, overwrites if it does. Automatically creates parent directories.",
		parameters: writeSchema,
		async execute(_toolCallId, { path, content }, signal, _onUpdate, { env }) {
			const absolutePath = await resolveToolPath(env, path, signal);
			return withFileMutationQueue(env, absolutePath, async () => {
				if (signal?.aborted) throw new Error("Operation aborted");
				getOrThrow(await env.writeFile(absolutePath, content, signal));
				if (signal?.aborted) throw new Error("Operation aborted");
				return {
					content: [{ type: "text", text: `Successfully wrote ${content.length} bytes to ${path}` }],
					details: undefined,
				};
			});
		},
	};
}
```

**Line 1: a mixed import.** `import { type Static, Type }` brings in one type and one value from the same statement.
`Type` is a real runtime object with methods; `Static` is a type-level helper. Both come from `typebox`, and the inline
`type` keyword marks which is which.

**Lines 8-13: schema first, type second.** `writeSchema` is a runtime value describing two required string fields, each
with a description that the model will read. `Static<typeof writeSchema>` derives `{ path: string; content: string }`
from it.

Write the schema, derive the type. Never the other way round, and never both by hand — if you declare the interface
separately, the two can drift, and the compiler cannot tell you.

**The descriptions are prompt engineering.** `"Path to the file to write (relative or absolute)"` is sent to the model in
the tool definition. It is the only guidance the model gets about that argument. A vague description here produces wrong
tool calls, and no amount of code quality compensates.

**Lines 15-19: a factory function returning a tool object.** Not a class implementing an interface. `createWriteTool()` is
called once and returns a plain object with a `name`, a `description`, a `parameters` schema, and an `execute` method.

The generic `<TContext extends ExecutionToolContext = ExecutionToolContext>` reads as: "a type parameter `TContext`,
which must be at least an `ExecutionToolContext`, defaulting to exactly that." `extends` here is a **bound**, the same
idea as Python's `TypeVar("TContext", bound=ExecutionToolContext)`. It lets an application pass a richer context and get
it back with its own fields intact, instead of widened away.

**Line 26: destructuring in the parameter list.** Look at the second parameter: `{ path, content }`. The argument is one
object; this pulls out two fields and binds them as local names. Python 3 has no equivalent for dicts — the closest is
`def execute(_id, args, ...)` followed by `path, content = args["path"], args["content"]`.

Destructuring appears again in the fifth parameter, `{ env }`, taking one field from the tool context and ignoring the
rest.

**The `_` prefix on `_toolCallId` and `_onUpdate`** marks parameters that are deliberately unused. The linter is
configured to accept it, exactly like Python's `_`. The parameters must still be listed because position determines
identity.

**Lines 29-31: cancellation is a manual check.** Two separate `if (signal?.aborted) throw new Error(...)` lines, before
and after the write.

This is the single most important thing in the file, and the biggest departure from Python. In `asyncio`, cancelling a
task raises `CancelledError` *at* the await point — the exception finds you. Here, nothing happens. `AbortSignal` is a
flag with an event; a signal that fires while `env.writeFile` is in flight does not interrupt it. Someone has to *look*.

So pi looks, twice: once before starting so an already-cancelled call does no work, and once after so a cancellation that
arrived during the write is reported instead of returning success. Both checks are hand-written. If you forget them, your
tool is uncancellable and nothing warns you.

`signal?.aborted` uses **optional chaining**: if `signal` is `null` or `undefined`, the whole expression is `undefined`
(falsy) instead of throwing. It is Python's `signal.aborted if signal is not None else None`, in one character.

**Line 30: `getOrThrow(await env.writeFile(...))`.** `env.writeFile` does not throw on failure. It returns a
`Result<T, E>` — a value that is either success or error. `getOrThrow` unwraps it, throwing if it holds an error.
[Concept 4](part_c_concepts.md#concept-4-result-instead-of-exceptions) covers why.

**Also on line 30: `env.writeFile`, not `fs.writeFile`.** This file never imports `node:fs`. It writes through `env`, an
abstraction passed in. That is what makes the tool testable without a filesystem, and sandboxable by swapping the
implementation. Module 2 builds this properly.

**Line 33: the return shape.** `content` is what the model sees — a `TextContent` block, exactly the type from
[Pass 3](part_a_types.md#pass-3-content-blocks--the-discriminated-union-lines-332-368). `details` is `undefined` here because this tool has no
structured result for the application. That is the `TDetails` parameter from
[Pass 5](part_a_types.md#pass-5-the-three-messages-lines-409-455), instantiated as `undefined`.

Notice the message text: `Successfully wrote ${content.length} bytes to ${path}`. Confirming an action back to the model
is deliberate — it needs to know the write happened.

**Questions to answer:**

- Why check `signal?.aborted` twice instead of once?

:::{dropdown} Answer
The two checks defend different windows.

The **first** covers the gap between the loop deciding to run this tool and the tool actually starting. Cancellation may
already have happened during path resolution or while queued behind another file mutation. Checking first means an
already-cancelled operation performs no write at all.

The **second** covers the write itself. `await env.writeFile(...)` can take real time. If the user hit Ctrl-C during it,
the write may have completed, but returning a cheerful success message would put a misleading tool result into the
transcript. The check converts it into an error instead.

What neither check can do is *stop* the write mid-flight. That is the nature of cooperative cancellation: you get to
notice at boundaries you choose. The `signal` is also passed *into* `env.writeFile`, so the implementation can abort
internally — but that is the implementation's job, not this file's.
:::

- The tool never imports `node:fs`. What does that buy, concretely?

:::{dropdown} Answer
Four things, and they are the reason this indirection is worth the extra layer:

**Tests without a filesystem.** Pass an in-memory `env` and assert on what the tool tried to write. No temp directories,
no cleanup, no flakiness.

**Sandboxing.** Swap in an `env` that routes writes into a container or micro-VM, and every tool is sandboxed at once
without any tool changing. pi's Gondolin extension does exactly this.

**Remote execution.** An `env` whose `writeFile` sends an RPC lets the agent operate on a machine it is not running on.

**One place for policy.** Path restrictions, audit logging, and permission prompts live in one implementation rather than
being re-implemented in every tool.

The general name for this is **dependency inversion**: the tool declares what it needs (`env`), and the caller decides
what supplies it. Python's `Protocol` is the same idea, and `ExecutionEnv` is exactly a Protocol — a structural interface
with no inheritance involved.
:::

---

## File 3: 01-minimal.ts (26 lines)

Open [`packages/coding-agent/examples/sdk/01-minimal.ts`](https://github.com/earendil-works/pi/blob/v0.84.2/packages/coding-agent/examples/sdk/01-minimal.ts).
This is a complete, working coding agent.

```ts
import { createAgentSession } from "@earendil-works/pi-coding-agent";

const { session } = await createAgentSession();

try {
	session.subscribe((event) => {
		if (event.type === "message_update" && event.assistantMessageEvent.type === "text_delta") {
			process.stdout.write(event.assistantMessageEvent.delta);
		}
	});

	await session.prompt("What files are in the current directory?");
	session.state.messages.forEach((msg) => {
		console.log(msg);
	});
	console.log();
} finally {
	session.dispose();
}
```

Twenty-six lines, and it reads files, runs commands, and edits code. That is the destination of this course: by Module 6
you will have written the thing behind this import.

**Line 3: top-level `await`.** `await createAgentSession()` sits at the top level of the file, not inside a function.

This has no Python equivalent. Python requires `asyncio.run(main())`, or an `async def main()` wrapper, because the event
loop must be started explicitly. In an ES module, `await` at the top level just works — the module itself becomes
asynchronous, and whatever imports it waits.

There is no `asyncio.run` in this course. There is no event loop to start. It is always already running.

**Line 3, again: destructuring a return value.** `const { session } = await createAgentSession()` pulls the `session`
field out of the returned object and discards the rest. Same operation as the parameter destructuring in `write.ts`,
applied to an assignment.

**Lines 6-10: a callback with narrowing.**

```ts
session.subscribe((event) => {
	if (event.type === "message_update" && event.assistantMessageEvent.type === "text_delta") {
		process.stdout.write(event.assistantMessageEvent.delta);
	}
});
```

Two discriminant checks joined by `&&`, and after both, `.delta` is accessible. Before them it is not — most event types
have no `delta` field. This is the union narrowing from Pass 3 and Pass 7, doing real work in real code: no cast, no
`isinstance`, just two string comparisons.

`process.stdout.write` is `sys.stdout.write` — no trailing newline, unlike `console.log`.

**Line 12: `await session.prompt(...)` is the whole loop.** One call. Inside it: build the context, call the model, stream
the response, parse tool calls, run the tools, append the results, call the model again, repeat until the model stops
asking for tools.

That is the inner loop, and Module 2 builds it. The fact that it hides behind one `await` is the point of a harness.

**Lines 16-18: `try` / `finally` and `dispose()`.** There is no `with` statement and no context manager protocol.
Cleanup is `try`/`finally` by hand, and the resource exposes a `dispose()` method by convention.

| Python | TypeScript |
| --- | --- |
| `with open(p) as f:` | `try { ... } finally { f.close(); }` |
| `async with session:` | `try { ... } finally { session.dispose(); }` |
| `__enter__` / `__exit__` | convention: a `dispose()` method |

(Newer JavaScript has `using` and `Symbol.dispose`, which is a real context-manager equivalent. pi does not use it, and
neither will we.)

**Questions to answer:**

- `session.subscribe(...)` is called *before* `session.prompt(...)`. What happens if you swap them?

:::{dropdown} Answer
You lose the streamed output.

`prompt()` is awaited, so by the time it returns, every event it was going to emit has already been emitted. Subscribing
after that registers a callback for a stream that has finished. `session.state.messages` still holds the full
conversation, so the `forEach` on line 13 prints everything — but the token-by-token output is gone.

This is the eagerness point from [Concept 5](part_c_concepts.md#concept-5-async-streams-and-cancellation), in a form you can trip over.
There is no "replay from the start" for subscribers, so subscribe first.
:::

- Where is the model configured? Nothing in this file names one.

:::{dropdown} Answer
Nowhere in this file, on purpose. The doc comment at the top says it: "Uses all defaults: discovers skills, extensions,
tools, context files from cwd and `~/.pi/agent`. Model chosen from settings or first available."

`createAgentSession()` with no arguments reads the environment — settings files, `~/.pi/agent/models.json`, environment
variables holding API keys — and picks the first model it can actually reach. So the same 26 lines run against a hosted
API or a local Ollama server depending only on configuration.

The other SDK examples in that directory take over each default in turn: `02-custom-model.ts` for the model,
`05-tools.ts` for the tool list, `12-full-control.ts` for everything. Read them in order after finishing this module —
they are a ladder from "all defaults" to "no defaults," and they preview the whole course.
:::
