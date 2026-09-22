# Module 0: Ground Floor

Welcome to Module 0. By the end of this module you will have built pi from source, watched a real agent session run end
to end, and scaffolded your own Python harness that type-checks, runs, and prints a conversation.

More importantly, you will be able to **read** TypeScript — the kind that production agents are written in — well enough
to learn from it and judge it.

---

## The Deal

**pi is a reference, not a blueprint.** You are not here to port it.

The goal is to understand what an agent harness *is*: what problems it has to solve, and what the available answers cost.
pi is how you get at that. It is about 140,000 lines of TypeScript, it has been in real use long enough to have met the
hard problems, and its reasoning is legible in the code. That makes it the best worked example available — a place to
watch someone else's decisions, not a specification to satisfy.

You read TypeScript. You write Python. And where pi's answer is one option among several, the course puts the others
next to it.

Every module works in three steps:

1. **Read** the pi code that handles something, and work out what the underlying problem actually is.
2. **Judge** the answer. Why this way? What did it cost them? Does that reasoning hold for you?
3. **Decide and build** your version in Python. Sometimes the same shape. Sometimes not.

Step 2 is where the learning is. If you skip it you get a Python transcription of someone else's architecture, which
teaches you almost nothing — you would be inheriting their constraints without knowing what they were.

Your harness will part company with pi's, probably early. Three situations where it is worth stopping to weigh the
options:

**A pattern exists only because TypeScript erases its types.** Carried into Python it solves a problem you do not have.
You will meet three of these in this module alone, each with the Python alternative set beside it.

**Python has an answer of its own.** Cancellation and schemas are both cases where the language does work pi has to do
by hand. The course shows you both versions and what each one costs. Both are in Part C.

**Your constraints are genuinely different.** pi ships to thousands of users across forty providers and two runtimes.
Generality you do not need is a cost, not a feature. Every module points out where pi is paying for a requirement you
might not have, and what you would get back by dropping it.

The only choice worth avoiding is the one you make by accident, or because something looked like too much work. Every
decision here is yours. The course's job is to have the alternatives in front of you before you make it.

---

## The Module in Order

Work through these in sequence. Parts A and B are reading; the projects are where you build.

```{toctree}
:maxdepth: 2

part_a_types
part_b_files
part_c_concepts
project_1_run_pi
project_2_scaffold
checklist
what_next
```

| Page | What it is | Time |
| --- | --- | --- |
| [Part A](part_a_types.md) | Eight guided passes over pi's `types.ts` | 2-3 h |
| [Part B](part_b_files.md) | Three complete pi files, read line by line | 45-60 min |
| [Part C](part_c_concepts.md) | The six ideas underneath, including how to read TypeScript | 2 h |
| [Project 1](project_1_run_pi.md) | Build pi, run it, watch a real session | 1 h |
| [Project 2](project_2_scaffold.md) | Scaffold your Python harness | 2-3 h |
| [Checklist](checklist.md) | Am I ready for Module 1? | 15 min |

If you are looking for the TypeScript cheat sheet, it is
[Concept 1](part_c_concepts.md#concept-1-how-to-read-typescript). You will come back to it.

Also on this page: [Who This Is For](#who-this-is-for), [What You Will Learn](#what-you-will-learn),
[Why This Matters](#why-this-matters), [How to Use This Guide](#how-to-use-this-guide), and a
[Time Estimate](#time-estimate).

---

## Who This Is For

You are a Python engineer. You write `async def` without thinking about it. You have used pydantic to validate a
payload. You know what a `Protocol` is. But when you open a `.ts` file, you see braces, `interface`, and a lot of
`?` marks, and you are not sure which parts are real code and which parts are decoration.

This guide assumes:

- Strong Python skills (`asyncio`, type hints, pydantic, `match`)
- Python 3.13 or newer, and [uv](https://docs.astral.sh/uv/)
- You have used a coding agent at least once, so the words "tool call" and "context window" mean something
- Node.js 22.19 or newer — used **only** to build and run pi itself, never for your own code
- No prior TypeScript experience

## What You Will Learn

After completing this module, you will be able to:

1. **Read a TypeScript module** — Know what `import type`, `export`, `interface`, `type`, and `?` mean, and which parts
   of a line are erased before it runs
2. **Explain why pi looks the way it does** — TypeScript deletes its types before execution, and three of pi's most
   distinctive habits fall directly out of that one fact
3. **Read a discriminated union** — pi's single most used pattern, and the reason it has almost no classes
4. **Model the same thing in Python** — a pydantic discriminated union that round-trips through JSON
5. **Prove a `match` is exhaustive** — `assert_never`, and what your type checker does with it
6. **Read pi's async streaming code** — `async function*`, `for await`, `AsyncIterable`, and the two places Python's
   model does not transfer
7. **Know where Python wins** — `asyncio` cancellation and pydantic both remove work pi has to do by hand
8. **Name the parts of a harness** — point at where pi keeps the loop, the tools, the transcript, and the terminal
9. **Set up a Python monorepo** — `uv` workspaces, cross-package imports, ruff, and a strict type checker
10. **Tell a real constraint from an inherited one** — recognize when pi is solving a TypeScript problem, or serving a
    requirement you do not have, and say so before writing any code

## Why This Matters

Every part of this course rests on one idea: **a harness is a loop, a set of tools, and a context you keep editing.**
Everything else is comfort.

That sounds simple enough to build in an afternoon. It is not, and the reason is worth understanding before you write
any code. A real harness has to answer questions like: what happens when the user presses Ctrl-C halfway through a tool
call? What happens when the transcript outgrows the context window? What happens when the model returns malformed JSON
for a tool call? What happens when the process dies mid-edit?

pi has an answer to every one of those, arrived at under real use. Reading those answers is far faster than
rediscovering the questions — which is the actual value here. Knowing that a problem exists is most of the work; you can
then decide how *you* want to handle it, and you will sometimes decide differently.

The reason this module spends its time on reading rather than building is simple: you cannot learn from a codebase you
cannot read, and you certainly cannot judge it. Once pi is legible to you, the remaining six modules are about
architecture and trade-offs — which is the part worth having.

## How to Use This Guide

For every concept in this module, you will:

1. **Read** — Open the actual source file and read it. Not a tutorial. Real code from pi.
2. **Ask what problem it solves.** Before wondering how to write it in Python, be able to say what would break without
   it. If you cannot, you are not ready to decide whether you need it.
3. **Judge it.** Does pi's reason apply to you? Say yes or no, and why.
4. **Build** — Write your Python. Same shape or different, but on purpose.
5. **Debug** — When your code does not work (it won't, at first), read the error and fix it.

The single most useful habit in this course: **when a claim in this guide surprises you, verify it.** Open a file, make
the change, run the checker. Both languages have unusually good error messages. They are the best teacher here.

## Time Estimate

- Part A (reading [`types.ts`](https://github.com/earendil-works/pi/blob/v0.87.0/packages/ai/src/types.ts)): 2-3 hours
- Part B (three small complete files): 45-60 minutes
- Part C (concepts deep dive): 2 hours
- Project 1 (build and run pi): 1 hour
- Project 2 (scaffold your harness): 2-3 hours

Total: roughly 8-11 hours, spread across several sessions. Part A is the long pole and the one that pays off; do not rush
it.
