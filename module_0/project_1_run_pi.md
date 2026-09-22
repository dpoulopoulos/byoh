# Project 1: Build and Run pi

Before writing your own harness, run the one you are studying. This project takes about an hour, most of it waiting for
`npm install`.

## Prerequisites

**Python 3.13 or newer, and `uv`.** For Project 2:

```bash
python3 --version
uv --version
```

If `uv` is missing, install it from [docs.astral.sh/uv](https://docs.astral.sh/uv/).

**Node.js 22.19 or newer.** Only to build and run pi itself — you will not write any JavaScript. Check with:

```bash
node --version
```

pi's root `package.json` declares `"engines": { "node": ">=22.19.0" }`. If you are older, install a newer one — `nvm`,
`fnm`, or Homebrew all work.

**A model you can reach.** Either of these is fine:

- **A hosted API key.** Any of `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`,
  and others. pi reads them from the environment. The full list is in
  [`packages/ai/src/env-api-keys.ts`](https://github.com/earendil-works/pi/blob/v0.87.0/packages/ai/src/env-api-keys.ts),
  and `pi-test.sh --no-env` unsets all of them if you want to test the keyless path.
- **A local server.** [Ollama](https://ollama.com) or [LM Studio](https://lmstudio.ai) with a model pulled. Step 4 below
  covers pointing pi at it.

## Step 1: Clone and Install

```bash
git clone https://github.com/earendil-works/pi.git
cd pi
git checkout v0.87.0
```

Checking out the pinned tag means the line numbers in this guide match what you see. Skip it if you would rather read
current `main`, and expect drift.

```bash
npm install --ignore-scripts
```

`--ignore-scripts` skips dependency lifecycle scripts. pi's own docs use this flag, and it is good practice generally: a
lifecycle script is arbitrary code from a package author running on your machine at install time.

**What to observe:** a single `node_modules` at the repo root, not one per package. That is npm workspaces at work —
dependencies are hoisted and shared, and the `packages/*` entries are symlinked into it so they can import each other by
name.

```bash
ls -la node_modules/@earendil-works/
```

Those symlinks pointing back into `packages/` are the whole trick of a monorepo. `@earendil-works/pi-ai` resolves to
`packages/ai` on disk, so `agent` can import `ai` by its published name while both are still local source.

## Step 2: Type-check

```bash
npm run check
```

This runs Biome (format and lint), a few consistency scripts, and `tsgo --noEmit` for type checking. It does not run
tests and does not emit files.

**What to observe:** it should pass silently. If it does not, your Node version or install is off. This is the command
you will run most often when writing your own harness.

## Step 3: Run pi from Source

You do not need to build. `pi-test.sh` runs the TypeScript directly:

```bash
./pi-test.sh --version
./pi-test.sh --list-models
```

Read the script — it is 57 lines, and the last one is the whole mechanism:

```bash
"$SCRIPT_DIR/node_modules/.bin/tsx" --tsconfig "$SCRIPT_DIR/tsconfig.json" "$SCRIPT_DIR/packages/coding-agent/src/cli.ts"
```

That is [Concept 1](part_c_concepts.md#concept-1-how-to-read-typescript)'s right-hand path: `tsx` strips types and runs `cli.ts` with no build
step and no type checking.

`--list-models` prints every model pi can reach with your current credentials. If the list is empty, pi found no keys and
no local server — fix that before continuing.

## Step 4: Point pi at a Local Model (Optional)

If you want to run against your own hardware, create `~/.pi/agent/models.json`:

```json
{
  "providers": {
    "ollama": {
      "baseUrl": "http://localhost:11434/v1",
      "api": "openai-completions",
      "apiKey": "ollama",
      "compat": {
        "supportsDeveloperRole": false,
        "supportsReasoningEffort": false
      },
      "models": [
        { "id": "qwen2.5-coder:7b" }
      ]
    }
  }
}
```

Every field in that file is something you read in Part A:

- `api: "openai-completions"` is a member of `KnownApi` (Pass 2) — the wire format, not the vendor
- `compat` is the conditional type from Pass 8, resolved to `OpenAICompletionsCompat` because of that `api` value
- `apiKey: "ollama"` is a placeholder; Ollama ignores it, but pi requires *some* credential before a model appears in the
  picker

Then:

```bash
ollama serve                        # in one terminal
ollama pull qwen2.5-coder:7b        # once
./pi-test.sh --list-models          # your model should appear
```

The full reference is
[`packages/coding-agent/docs/models.md`](https://github.com/earendil-works/pi/blob/v0.87.0/packages/coding-agent/docs/models.md).
Read it now — it is the best short document in the repo, and Module 1 works through it properly.

## Step 5: Watch a Session End to End

Start interactive mode:

```bash
./pi-test.sh
```

Then ask it something that forces tool use:

```
How many TypeScript files are in packages/ai/src, and what is the largest one?
```

**What to observe, and this is the actual point of the project:**

1. Your text appears — that is a `UserMessage` (Pass 5), sitting after the leading `SystemMessage` that holds the
   prompt and the tool declarations
2. The model streams a reply token by token — those are `text_delta` events (Pass 7)
3. A tool call appears with its arguments — a `ToolCall` block, arguments validated against a schema (Pass 6)
4. The tool's output comes back — a `ToolResultMessage`, now part of the transcript
5. The model streams again, having seen the result — the loop went around
6. Token counts and cost update — that is `Usage` (Pass 4)

You just watched every type from Part A move through a real system. Steps 3 through 5 repeating is the inner loop.

Now exit and look at what it wrote:

```bash
ls ~/.pi/agent/sessions/
```

Sessions are JSONL — one JSON object per line, appended. Open one and find your `UserMessage`. It is the same shape you
read in Pass 5. That file is what Module 3 is about.

## Step 6: Try the SDK Example

```bash
./node_modules/.bin/tsx packages/coding-agent/examples/sdk/01-minimal.ts
```

This is the 26-line file from Part B. Watch it stream, print its messages, and exit.

Then open `packages/coding-agent/examples/sdk/` and skim the other twelve, in order. They form a ladder from "all
defaults" to "no defaults," and they are a preview of the entire course.

## Experiments to Try

- Run `./pi-test.sh --no-env` and watch what changes. Which models disappear?
- Start a prompt that triggers a long tool call and hit Ctrl-C. Watch cooperative cancellation from
  [Concept 5](part_c_concepts.md#concept-5-async-streams-and-cancellation) in a real system.
- Find an exhaustive `switch` in pi that ends with a `never` assignment. `grep -rn "never = " packages/agent/src` is a
  good start. You are about to write the same proof in Python with `assert_never`, so read one first.
- Open `packages/ai/src/types.ts` and `packages/agent/src/harness/tools/read.ts` side by side. Find the schema and the
  type that comes from it. That duplication is what pydantic removes for you.
- Dump a session file and find the `"role": "system"` entries. There is one at the top, and there may be more further
  down if the tool set changed mid-run. That is Pass 5's `SystemMessage` on disk.
