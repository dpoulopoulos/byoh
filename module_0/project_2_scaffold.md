# Project 2: Scaffold Your Harness

This is the project you keep. Every module from here on adds to it. By Module 6 it will be a working coding agent.

Today you build the skeleton and one real thing: pi's `Message` union in pydantic, and a renderer your type checker
proves is exhaustive.

## Step 0: Create the Directories

Build this outside the pi checkout. You are writing your own project.

```bash
mkdir -p ~/myharness/packages/ai/src/myharness_ai
mkdir -p ~/myharness/packages/agent/src/myharness_agent
cd ~/myharness
git init
```

The directory names match pi's — `packages/ai` and `packages/agent` — and that is worth doing **while you are
learning**, for one narrow reason: you will be reading the two trees side by side constantly, and a shared vocabulary
makes "where does pi put this?" a question with an obvious answer.

It is scaffolding, not architecture. Once you have opinions of your own about where things belong, rename freely. A
package boundary you disagree with is worse than an unfamiliar name.

Why a monorepo at all, when one package would do? Because the layering from
[Concept 6](part_c_concepts.md#concept-6-the-ten-packages) only means something if it is enforced. `agent` may import `ai`; `ai` must never
import `agent`. Separate packages make the illegal direction a dependency error instead of a bad habit.

## Step 1: The Workspace Root

`pyproject.toml`:

```toml
[project]
name = "myharness"
version = "0.0.1"
requires-python = ">=3.13"
dependencies = ["myharness-ai", "myharness-agent"]

[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
myharness-ai = { workspace = true }
myharness-agent = { workspace = true }

[dependency-groups]
dev = ["mypy>=1.14", "ruff>=0.9", "pytest>=8"]

[tool.ruff]
line-length = 120

[tool.mypy]
strict = true
```

Three parts matter:

- `[tool.uv.workspace]` with `members = ["packages/*"]` — the direct equivalent of npm's `"workspaces": ["packages/*"]`.
- `[tool.uv.sources]` with `workspace = true` — resolve these from the local tree, not from PyPI. Without this, `uv`
  goes looking for a package called `myharness-ai` on the index and fails.
- `strict = true` for mypy. Same spirit as pi's `strict` in `tsconfig.base.json`, and just as non-negotiable. Turn it on
  now while the project is two files, not later when it is two hundred.

`line-length = 120` matches pi's Biome setting. Handy while you are reading pi side by side with your own code.

## Step 2: The Two Package Manifests

`packages/ai/pyproject.toml`:

```toml
[project]
name = "myharness-ai"
version = "0.0.1"
requires-python = ">=3.13"
dependencies = ["pydantic>=2.10"]

[build-system]
requires = ["uv_build>=0.9,<0.12"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = "myharness_ai"
```

`packages/agent/pyproject.toml`:

```toml
[project]
name = "myharness-agent"
version = "0.0.1"
requires-python = ">=3.13"
dependencies = ["myharness-ai"]

[build-system]
requires = ["uv_build>=0.9,<0.12"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = "myharness_agent"

[tool.uv.sources]
myharness-ai = { workspace = true }
```

The `dependencies` line on `agent` is the layering rule, written down. `agent` declares that it may use `ai`. `ai`
declares only pydantic, so it can never reach back.

`module-name` is needed because the distribution name has a hyphen (`myharness-ai`) and the import name has an
underscore (`myharness_ai`). Python cannot import a hyphen, so the two differ and the build backend needs telling.

Now link them:

```bash
uv sync
```

`uv` creates one `.venv` at the root, installs pydantic, and installs both of your packages in editable mode. This is
the same trick as npm hoisting: one environment, your packages symlinked into it so they can import each other by name.

## Step 3: The Message Union

`packages/ai/src/myharness_ai/types.py`:

```python
"""The vocabulary of a turn. Mirrors pi's packages/ai/src/types.ts."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class TextContent(BaseModel):
    """A block of plain text."""

    type: Literal["text"] = "text"
    text: str


class ToolCall(BaseModel):
    """A request from the model to run a tool."""

    type: Literal["toolCall"] = "toolCall"
    id: str
    name: str
    arguments: dict[str, object]


ContentBlock = Annotated[TextContent | ToolCall, Field(discriminator="type")]


class Usage(BaseModel):
    input: int
    output: int
    total_tokens: int


StopReason = Literal["stop", "length", "toolUse", "error", "aborted"]


class UserMessage(BaseModel):
    role: Literal["user"] = "user"
    content: str | list[TextContent]
    timestamp: int


class AssistantMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: list[ContentBlock]
    model: str
    usage: Usage
    stop_reason: StopReason
    timestamp: int


class ToolResultMessage(BaseModel):
    role: Literal["toolResult"] = "toolResult"
    tool_call_id: str
    tool_name: str
    content: list[TextContent]
    is_error: bool
    timestamp: int


Message = Annotated[
    UserMessage | AssistantMessage | ToolResultMessage,
    Field(discriminator="role"),
]


class Context(BaseModel):
    system_prompt: str | None = None
    messages: list[Message] = Field(default_factory=list)
```

Read that against
[pi's lines 409-455](https://github.com/earendil-works/pi/blob/v0.87.0/packages/ai/src/types.ts#L409-L455)
and notice how close it is. Same three messages, same discriminant, same content-blocks-not-a-string decision.

**Three translation notes.**

**`Field(discriminator="role")` is the whole trick.** It tells pydantic to read `role` first and pick the matching class,
instead of trying all three and reporting a confusing union error. It is the runtime half of what TypeScript's narrowing
does at compile time — and unlike TypeScript, you get both halves from the same declaration.

**The discriminant values keep pi's exact spelling** — `"toolCall"` and `"toolResult"`, camelCase, not snake_case. That
is deliberate. Those strings go on the wire and into session files, so they are a format, not a naming choice. The field
*names* are snake_case because those are yours.

**`dict[str, object]`, not `dict[str, Any]`.** pi writes `Record<string, any>` here. `object` forces you to narrow before
using a value; `Any` switches the checker off. The scaffold uses `object` and pays the narrowing cost, on the grounds
that `Any` should be a decision rather than a default.

`packages/ai/src/myharness_ai/__init__.py`:

```python
from myharness_ai.types import (
    AssistantMessage,
    ContentBlock,
    Context,
    Message,
    StopReason,
    TextContent,
    ToolCall,
    ToolResultMessage,
    Usage,
    UserMessage,
)

__all__ = [
    "AssistantMessage",
    "ContentBlock",
    "Context",
    "Message",
    "StopReason",
    "TextContent",
    "ToolCall",
    "ToolResultMessage",
    "Usage",
    "UserMessage",
]
```

This is the package's public surface — the same job as pi's `index.ts` re-export block from Pass 1. `__all__` is what
makes it explicit.

## Step 4: The Exhaustive Renderer

`packages/agent/src/myharness_agent/render.py`:

```python
from typing import assert_never

from myharness_ai import AssistantMessage, Message, ToolResultMessage, UserMessage


def render_message(message: Message) -> str:
    """Collapse a message to one line. Every branch of Message must be handled."""
    match message:
        case UserMessage():
            text = message.content if isinstance(message.content, str) else "".join(c.text for c in message.content)
            return f"user> {text}"
        case AssistantMessage():
            parts = [b.text if b.type == "text" else f"[call {b.name}({b.arguments})]" for b in message.content]
            return f"model> {' '.join(parts)} ({message.usage.total_tokens} tokens, {message.stop_reason})"
        case ToolResultMessage():
            text = "".join(c.text for c in message.content)
            label = "error" if message.is_error else "tool"
            return f"{label}> {message.tool_name}: {text}"
        case _:
            assert_never(message)
```

**`assert_never(message)` in the final case is the whole point of this step.**

By the time control reaches `case _`, the checker has narrowed `message` past all three classes. If the `match` covered
every member of the union, the only type left is `Never` — the empty type — and passing `Never` to `assert_never` is
fine. If a case is *missing*, the leftover type is that class, and passing it to `assert_never` is an error.

This is the exact equivalent of the `const unreachable: never = message` trick pi uses in its `switch` statements. Same
proof, different spelling. Python got the better syntax here.

Note also that `b.type == "text"` narrows `b` from `TextContent | ToolCall` down to `TextContent`, so `b.text` is
allowed and `b.name` would not be. That is the same discriminant narrowing from Pass 3, and your type checker does it
just as TypeScript's does.

`packages/agent/src/myharness_agent/__init__.py`:

```python
from myharness_agent.render import render_message

__all__ = ["render_message"]
```

## Step 5: Run It

`packages/agent/src/myharness_agent/main.py`:

```python
from myharness_ai import (
    AssistantMessage,
    Message,
    TextContent,
    ToolCall,
    ToolResultMessage,
    Usage,
    UserMessage,
)
from myharness_agent.render import render_message

transcript: list[Message] = [
    UserMessage(content="What files are here?", timestamp=1),
    AssistantMessage(
        content=[
            TextContent(text="Let me look."),
            ToolCall(id="call_1", name="ls", arguments={"path": "."}),
        ],
        model="qwen3-coder",
        usage=Usage(input=412, output=28, total_tokens=440),
        stop_reason="toolUse",
        timestamp=2,
    ),
    ToolResultMessage(
        tool_call_id="call_1",
        tool_name="ls",
        content=[TextContent(text="README.md  src/")],
        is_error=False,
        timestamp=3,
    ),
]

for message in transcript:
    print(render_message(message))
```

That list is a complete agent turn, hand-written: the user asks, the model answers and calls a tool, the tool returns.
Exactly the sequence you watched in Project 1, Step 5.

**The annotation on `transcript` is load-bearing.** Write it as a bare `transcript = [...]` and mypy infers
`list[BaseModel]` — the nearest common ancestor of the three classes — and then rejects every call to `render_message`:

```
error: Argument 1 to "render_message" has incompatible type "BaseModel"; expected "UserMessage | ..."
```

You have to say `list[Message]`. TypeScript infers the union here and Python does not, and this is the most common way
this project fails to type-check on the first attempt.

Check and run:

```bash
uv run mypy packages
uv run ruff check packages
uv run python -m myharness_agent.main
```

Expected output:

```
user> What files are here?
model> Let me look. [call ls({'path': '.'})] (440 tokens, toolUse)
tool> ls: README.md  src/
```

If you see those three lines with mypy clean, the workspace works, the union is right, and the renderer is exhaustive.

## Step 6: Break It on Purpose

This step matters more than Step 5. You are checking that the safety net is real. Each break has an exact error; read
it before restoring.

**Break 1 — remove a case.** Delete the whole `case ToolResultMessage():` block from `render.py`, then
`uv run mypy packages`:

```
error: Argument 1 to "assert_never" has incompatible type "ToolResultMessage"; expected "Never"  [arg-type]
```

Read that until it is obvious. It says: "you promised nothing could reach here, but a `ToolResultMessage` can." This is
the Python twin of the `TS2322` error pi's `switch` statements produce. Restore the case.

**Break 2 — a bad discriminant at runtime.** This one has no TypeScript equivalent, and it is the payoff for using
pydantic. Try parsing a message with a role that does not exist:

```python
from pydantic import TypeAdapter
from myharness_ai import Message

adapter = TypeAdapter(Message)
adapter.validate_json('{"role": "wizard", "content": "x", "timestamp": 1}')
```

```
union_tag_invalid
```

pydantic read the `role` tag, found no matching class, and refused. **pi cannot do this.** Its types are erased, so
validating a session file or a provider response needs a separate TypeBox schema carried alongside the type. Your
pydantic model is both at once. That is [Concept 2](part_c_concepts.md#concept-2-types-are-erased) paying you back.

**Break 3 — a missing required field.**

```python
adapter.validate_json('{"role": "assistant", "content": [], "timestamp": 1}')
```

```
missing at ['assistant', 'model']
```

Note the path: it tells you the discriminator picked `assistant`, and then which field was absent. That precision is
what you get from declaring the discriminator explicitly.

**Break 4 — add a fourth message type.** In `types.py`, add:

```python
class SystemMessage(BaseModel):
    role: Literal["system"] = "system"
    content: str
    timestamp: int
```

and extend the union:

```python
Message = Annotated[
    UserMessage | AssistantMessage | ToolResultMessage | SystemMessage,
    Field(discriminator="role"),
]
```

Run `uv run mypy packages`. `render.py` fails at the `assert_never` line, without you touching that file.

This is the payoff of the pattern: **the type checker found every place that needs updating.** In a real codebase that
is forty files, and it lists all of them.

Now decide what to do about it. pi's answer, from Pass 5, is that there *is* no system message — the system prompt lives
on `Context`, because it is a property of the conversation rather than a turn within it. Revert the change, and note the
reasoning: you just rediscovered a design decision by trying the alternative.

## Bonus Challenges

1. **Round-trip through JSON.** Use `TypeAdapter(Message)` to serialize your transcript to JSON lines and read it back.
   Confirm each line comes back as the right class. This is the mechanism behind pi's session files, and it is Module 3.

2. **The three-state field.** Add pi's `ThinkingLevelMap` idea from [Concept 3](part_c_concepts.md#concept-3-absent-null-and-set--reading-pis-optional-fields):
   a field where absent, `None`, and a value all mean different things. Use `model_fields_set` to tell absent from
   `None`, then write a test proving all three are distinguishable.

3. **Cost accounting.** Extend `Usage` with a nested `cost` model like pi's (Pass 4) and make `render_message` print
   dollars. Then add pi's `reasoning: int | None` and write a comment explaining why adding it to `output` would be
   double counting.

4. **Read the TypeScript back.** Open pi's `types.ts` at line 409 next to your `types.py`. For each difference, work out
   which of three things it is: pi solving a TypeScript problem you do not have, pi serving a requirement you do not
   have, or you having missed something. Only the third calls for a change. Write down the first two — that list is the
   beginning of your own design, and it is worth keeping as the course goes on.
