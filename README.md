# QuietDrop

QuietDrop is a local-first file intake and staging tool for watched folders, review queues, and controlled archive actions.

## What It Is

QuietDrop is a Python project with two operator surfaces:

- a CLI for setup, scanning, review, archive, rename, reject, and tagging
- a local web UI and JSON API for browsing and processing queued files

It watches one or more folders, records file metadata in a local database, and keeps the operator in control of what happens next.

## Why It Exists

QuietDrop exists for workflows where files arrive locally but should not be moved, archived, or renamed automatically without review.

## Problem It Solves

Many file-drop workflows are either too manual or too automatic. QuietDrop creates a local intake queue between those two extremes, making it easier to see what arrived, inspect it, and deliberately move it forward.

## Features

- initialize local config and database
- watch folders continuously or scan on demand
- keep a queue of new, reviewed, archived, and rejected items
- archive files into a local destination folder
- rename files and persist updated paths
- tag queued items
- expose a local web UI and JSON API
- include tests for intake, archive behavior, and rename behavior

## Tech Stack

- Python 3.11+
- Typer
- Rich
- FastAPI
- Uvicorn
- Jinja2
- watchdog
- local SQLite storage
- pytest

## Quick Start

Install the project locally:

```bash
python3 -m pip install -e ".[dev]"
```

Create the default config and database:

```bash
quietdrop init --watch "/path/to/drop" --archive "/path/to/archive"
```

Run a one-shot scan and inspect the queue:

```bash
quietdrop scan
quietdrop list --status new
```

Review and archive an item:

```bash
quietdrop review 1
quietdrop archive 1
```

Run the local watcher:

```bash
quietdrop run
```

Start the local web UI and JSON API:

```bash
quietdrop serve --host 127.0.0.1 --port 8844
```

Then open `http://127.0.0.1:8844/`.

## CLI / API Usage

CLI:

- `quietdrop status`
- `quietdrop scan`
- `quietdrop list --status new`
- `quietdrop review <id>`
- `quietdrop archive <id>`
- `quietdrop reject <id>`
- `quietdrop rename <id> <new_name>`
- `quietdrop tag <id> <tag...>`
- `quietdrop serve --host 127.0.0.1 --port 8844`

Key local routes:

- `GET /`
- `GET /items/{item_id}`
- `GET /api/items`
- `GET /api/items/{item_id}`
- `POST /api/items/{item_id}/review`
- `POST /api/items/{item_id}/reject`
- `POST /api/items/{item_id}/archive`

Configuration is read from `QUIETDROP_CONFIG` if set, otherwise from `~/.config/quietdrop/config.toml` or `XDG_CONFIG_HOME`.

## Screenshots

Screenshots are not published yet. The web UI is present, but the current documentation focus is workflow clarity rather than visual polish.

## Status

Current status: working MVP.

Implemented now:

- folder watch and scan flows
- local intake queue with status tracking
- archive, reject, rename, and tag actions
- local web UI and JSON API
- test coverage around intake and file actions

Not complete yet:

- richer review metadata
- screenshot documentation
- more deployment examples for service-style operation

## Roadmap

- expand tests around watcher and web behavior
- add more operator filters and review context
- document recommended local service setup
- refine archive and intake rules without adding cloud dependencies

## Portfolio Note

QuietDrop is part of the Blackfong portfolio because it shows controlled local automation rather than blind automation. It demonstrates practical workflow design, local persistence, file handling, and a clean split between CLI and browser-based review.
