# Trend Analysis — agents for Claude Code

A set of agents that answers two questions about any product:
**what works in this niche right now** and **what your buyers complain
about, in their own words**.

The output is ready material for short-video scripts: other people's
hooks taken apart, real quotes from real people, and concrete ideas
of what to film.

**Languages:** [Русский](README.md) · [Հայերեն](README.hy.md) · English
**One-page overview:** [docs/scheme.html](docs/scheme.html)

---

## The main thing to understand first

**You don't need to code, and you barely need to touch a file.**
Claude does the work. You give it a task in plain words — it downloads,
installs, fills in files, searches, analyses and files the result away.

Your part shows up in three places:

1. open a Virlo account and paste the key (five minutes, once);
2. **tell Claude about your product in your own words** — it writes
   the files;
3. read the result and decide what to film.

Everything else is the agents' job.

---

## Before you start

| What | Why | Cost |
|---|---|---|
| **Claude subscription** | the agents won't run without it | Anthropic pricing |
| **Claude Code** | where the agents live | included |
| **Virlo account** | the source of video data | ~$12/month |
| Python, ffmpeg | downloading clips and transcribing speech | free |

**Claude Code:** https://claude.com/product/claude-code
**Virlo:** https://virlo.ai

---

## Step 1 · The Virlo key — everything starts here

Without a key there is nothing to analyse: no source of clips.

1. Open **https://virlo.ai** and sign up with your email.
2. Confirm the email and log in.
3. Top up the balance — a month of work costs about **$12**.
4. Find the **API** section (sometimes called Developers, Integrations
   or API Keys) and create a key.
5. **Copy it right away** — it usually isn't shown twice. It looks like
   `virlo_tkn_` followed by letters and digits.

Then hand the key to Claude:

> Connect Virlo as an MCP server in my .claude.json. URL
> https://dev.virlo.ai/api/mcp/mcp, http transport, Authorization
> header set to "Bearer MY_KEY". Then remind me to restart Claude Code.

Restart Claude Code and check:

> Check my Virlo balance

A number means it works. The check is free.

> **The key is access to money on your balance.** Don't post it in chats,
> screenshots or repositories.

---

## Step 2 · Install — one task for Claude

Tell Claude:

> Clone https://github.com/<YOUR-NAME>/trend-analysis into
> C:\Ferma\trend-analysis. Copy every file from the agents folder into
> my Claude Code agents folder. Then install the nightly build of yt-dlp
> and faster-whisper, check that ffmpeg is available, and lay out config
> and lib in the working folder. Tell me what's missing.

To verify:

```
python doctor.py
```

The script reports each item as ready or missing, with the command to
fix it. If the output isn't clear, show it to Claude and ask it to fix
things.

---

## Step 3 · Tell it about your product

This part needs you: the agent doesn't know your product.

**Don't fill in files by hand.** Just describe the product to Claude the
way you'd describe it to a friend. The more detail, the better the
analysis.

> Add a new product: <name>. Here's what it is: <talk freely — what it
> does, what it's made of, what it costs, where it sells, what the pack
> looks like, who it's for, what it does better, what it can't do>.
> Here's the store link: <link>. Fill in the product card, the claim
> restrictions and the pain-search topics using the templates folder.

Claude creates four files:

| File | What's in it |
|---|---|
| `card.md` | everything about the product: uses, contents, price, packaging |
| `claims.md` | what must never be promised in this category |
| `pain-topics.md` | topics to search people's complaints by |
| `trend-keys.md` | keywords for finding clips (English only) |

Read what it wrote and correct anything that's off. **This is the single
most important spot in the whole process:** a thin product description
produces a weak analysis.

---

## Step 4 · Run the analysis

> Analyse <product>

That's it. The agent works on its own for an hour and a half to two
hours and brings back the result. The first analysis of a new product
takes about a day.

---

## What you get

### One-off — the report for this run

Folder `runs\<date>\<product>\`:

| File | For whom |
|---|---|
| **`ПАКЕТ-<product>.md`** | **the main one.** For whoever writes scripts: niche mechanics, competitors' hooks verbatim, pains with quotes, ready ideas |
| `АНАЛИЗ-НЕДЕЛИ-<product>.md` | for you. The niche in five minutes of reading |
| `боли-<product>.json` | machine file for other agents |
| `refs\` | downloaded clips, frames, speech transcripts |

### Cumulative — the product's own property

Folder `products\<product>\banks\` — six files that grow with every
analysis: hooks, developments, endings, filming techniques, failures,
and combinations confirmed by your own measurements.

> **The package is today's newspaper:** read it and throw it away.
> **The banks are a library:** they grow with every run and last for years.

---

## How to use it

**1. Read `АНАЛИЗ-НЕДЕЛИ`** — five minutes. You'll see what actually
works in your niche.

**2. Hand `ПАКЕТ` to whoever writes the scripts** — yourself, an
employee, or another agent.

**3. Film from bank parts.** Take the hook from one clip, the
development from another, the ending from a third — that's not a copy,
it's your own build from proven parts.

**4. Measure and come back.** Once clips are published and counted, tell
Claude what worked: it marks hook statuses and records the winning
combinations. Over time the bank stops being someone else's experience
and becomes yours.

---

## Repository layout

```
trend-analysis/
  README.md          full documentation (Russian)
  РУКОВОДСТВО.md     the long guide: terms, install, the nine steps
                     of a run, troubleshooting, acceptance checklist
  agents/            19 agents — copied into the Claude Code agents folder
  config/            rules: selection thresholds, where to look for ideas,
                     what can't be claimed, output formats
  lib/               download a clip, transcribe speech, measure shot rhythm
  doctor.py          environment check in one command
  templates/         empty files for a new product
  examples/          two real analyses in full
```

Note: agent instructions, config and examples are written in Russian —
that's the working language of this system. The agents understand
English tasks fine, but the documents they produce follow the Russian
formats above.

---

## Honest limits

**What it does well:** finds what works in a niche right now, brings
back the actual words people use, and breaks other people's successful
clips into parts you can rebuild from.

**What it doesn't do:**

- it doesn't write scripts or film — it delivers material, not a video;
- it doesn't know what will work **for you** until you publish and
  measure. Every selection rule here comes from other people's results:
  a sensible starting point, not a guarantee;
- it searches for pains in Russian — other languages need their own
  sources;
- it depends on Virlo: no key or no balance means no fresh data.

---

## Requirements

Claude Code · Python 3.10+ · ffmpeg · a funded Virlo account · Windows

License: [MIT](LICENSE)
