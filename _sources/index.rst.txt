.. title:: Home

Build Your Own Harness
======================

Hey there! Welcome to **Build Your Own Harness**. Over seven modules you write an AI agent harness in Python, and come to
understand every piece of machinery inside it.

Along the way you read `pi <https://github.com/earendil-works/pi>`_, a production harness, as a worked example — pinned to
the `v0.87.0 <https://github.com/earendil-works/pi/tree/v0.87.0>`_ tag, so every line number quoted here still points at
the code it describes.

If you are a Python engineer who has used a coding agent and wondered what is actually happening between your prompt and
the model, you are in the right place. No toy examples. Every concept starts from a real problem, shown in real code, and
ends with you deciding how your harness will handle it. 🚀

You **read** TypeScript and you **write** Python. pi is a reference, not a blueprint. It shows you which problems a
harness has to solve and one team's answers, with the reasoning visible. Where a problem has more than one reasonable
answer, the course puts the alternatives side by side with what each one costs. Which one goes into your harness is
your call.

.. note::

   This course is in early access. The curriculum is finalized, but modules are still being written.
   Subscribe for updates!

.. important::

   The course has only been tested on macOS. Everything should work on Linux and WSL, but paths and
   shell commands assume a Unix-like system.

What Is a Harness?
------------------

A model is a function. Text in, text out. It cannot read your files, run your tests, or remember yesterday.

A **harness** is everything around that function which turns it into an agent: the loop that calls the model repeatedly,
the tools it can invoke, the transcript it carries, and the terminal you type into. `pi <https://github.com/earendil-works/pi>`_
is one of the best open-source examples, at about 190,000 lines of TypeScript. Big enough to have met the hard problems,
and readable enough to learn from.

What You'll Learn
-----------------

The course is organized into 7 modules. Each module takes on one problem a harness has to solve, shows you how pi solves
it and why, and then has you solve it in Python.

0. **Ground Floor** -- Reading TypeScript, why erased types shape pi's design, discriminated unions, and the vocabulary of a turn
1. **Talking to Any Model** -- Provider adapters, SSE parsing, one interface over hosted APIs and local servers
2. **The Loop and Its Tools** -- The agent loop, tool schemas, dependency inversion, and permission
3. **State That Survives** -- Append-only sessions, the conversation tree, compaction, and crash recovery
4. **The Terminal** -- Differential rendering, the editor, autocomplete, and a real TUI with Textual
5. **Making It Yours** -- Extensions, skills, slash commands, and settings
6. **Two Processes** -- The wire protocol, the client/server split, and testing without spending tokens

Projects
--------

Each module ends with something that runs. These are the problems, not a checklist of pi features to reproduce:

- Scaffold a ``uv`` workspace, model a conversation with pydantic, and render a transcript
- Stream tokens from a hosted API and from a local server through one interface
- A working agent loop that reads files, edits them, and runs commands
- Sessions that survive a crash, and a transcript that compacts itself
- A terminal UI with a real text editor and autocomplete
- Extensions, skills, and slash commands loaded from disk
- **Capstone:** split your harness into a client and a server over a typed protocol

Who This Is For
---------------

- Python engineers comfortable with ``asyncio``, type hints, and pydantic, who want to read a real TypeScript codebase
  without adopting it
- Anyone who uses coding agents and wants to know how they actually work
- Developers who learn better by reading real code than by reading tutorials

Prerequisites
-------------

- Solid programming experience, ideally Python
- Python 3.13 or newer, `uv <https://docs.astral.sh/uv/>`_, and ``git``
- Node.js 22.19 or newer, only to build and run pi itself
- Access to at least one model. A hosted API key works. So does `Ollama <https://ollama.com>`_ or
  `LM Studio <https://lmstudio.ai>`_ on your own machine.
- No TypeScript or JavaScript experience required. You will learn to read it, not write it.

Ready? Let's dive in! 👇

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   module_0/index
