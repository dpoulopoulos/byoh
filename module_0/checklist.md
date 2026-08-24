# Self-Assessment Checklist

Before moving to Module 1, make sure you can answer "yes" to all of these.

## Reading TypeScript

- [ ] I can look at a TypeScript function signature and mentally delete the annotations to see the plain code
- [ ] I know what `import type` means and why it tells me which names are real at runtime
- [ ] I can read a discriminated union and say which field is the discriminant
- [ ] I know the difference between `x?: string`, `x: string | undefined`, and `x: string`
- [ ] I can read `x?.y`, `x ?? y`, `x!`, and `x as T` without stopping
- [ ] I know which constructs to skip on a first read, and I skip them
- [ ] I can read [`types.ts`](https://github.com/earendil-works/pi/blob/v0.84.2/packages/ai/src/types.ts)
      and identify interfaces, unions, generics, utility types, and one conditional type

## Why pi Looks the Way It Does

- [ ] I can explain that TypeScript deletes its types before running, and name three consequences
- [ ] I can explain why pi carries a TypeBox schema next to every tool's type, and why I do not need to
- [ ] I can explain why pi's data model is discriminated unions and not class hierarchies
- [ ] I can explain why pi returns `Result` instead of throwing, and decide when a Python exception is the better answer
- [ ] I can explain why `AbortSignal` stops nothing, and why my `asyncio` code does not need those manual checks
- [ ] I can name a pi pattern that exists only because of TypeScript, and say what I would write instead
- [ ] I can state the three fields of `Context` and explain why every feature reduces to one of them

## Building in Python

- [ ] I can set up a `uv` workspace with two packages and a working cross-package import
- [ ] I know why `[tool.uv.sources]` with `workspace = true` is required
- [ ] I can write a pydantic discriminated union and explain what `Field(discriminator=...)` buys me
- [ ] I can prove a `match` is exhaustive with `assert_never`, and I have seen it fail
- [ ] I know why `transcript: list[Message]` needs the annotation
- [ ] I can parse a message from JSON and have pydantic reject a bad tag at runtime
- [ ] I have mypy in `strict` mode and I intend to keep it there

## Honest Check

- [ ] I ran pi, watched a session, and found my own `UserMessage` in a session file on disk
- [ ] I broke my own project four times on purpose and read each error
- [ ] When something in this guide surprised me, I verified it myself instead of taking my word for it
- [ ] I did not copy a pi pattern I could not justify in Python
- [ ] I can name at least one decision where I would go a different way than pi, and say why
