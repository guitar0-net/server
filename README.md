<!--
SPDX-FileCopyrightText: 2025-2026 Andrey Kotlyar <guitar0.app@gmail.com>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Guitar0 backend

[![CI](https://github.com/guitar0-net/server/actions/workflows/ci.yml/badge.svg)](https://github.com/guitar0-net/server/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/guitar0-net/backend/graph/badge.svg?token=O0HFMUOVO6)](https://codecov.io/gh/guitar0-net/backend)
[![Python](https://img.shields.io/badge/python-3.14-blue.svg)](https://python.org)
![Django](https://img.shields.io/badge/django-6-blue)
[![License](https://img.shields.io/badge/license-AGPL--3.0--or--later-green.svg)](./LICENSES/AGPL-3.0-or-later.txt)
[![REUSE status](https://api.reuse.software/badge/github.com/guitar0-net/backend)](https://api.reuse.software/info/github.com/guitar0-net/backend)

REST API backend for the [Guitar0](https://guitar0.net) guitar education platform, serving mobile and web clients.

The service provides user accounts, song and chord libraries, structured guitar courses, and other learning content for mobile and web clients.

## Tech Stack

| Layer     | Technology                       |
| --------- | -------------------------------- |
| Language  | Python 3.14                      |
| Framework | Django 6 · Django REST Framework |
| Database  | PostgreSQL 16                    |
| Server    | Gunicorn                         |
| Packaging | PDM                              |
| Linting   | Ruff · Mypy (strict)             |
| Testing   | pytest · coverage (≥ 90%)        |
| Security  | Bandit · pip-audit               |

## Prerequisites

- Python 3.14+
- [PDM](https://pdm-project.org)
- PostgreSQL 16 — or Docker (see below)

## Quick Start

**Local:**

```bash
cp .env.example .env.development   # fill in DB credentials
pdm install
make migrate
make run
```

**Docker:**

```bash
make docker-up
```

API is available at `http://localhost:8000`.

## Development Commands

```
make help            list all available commands

make lint            ruff + mypy
make test            pytest with coverage report
make ci              lint + test (mirrors CI pipeline)

make migrate         apply migrations
make shell           Django shell

make docker-up       start app + DB via Docker Compose
make docker-down     stop containers
make docker-logs     tail logs
```

## Project Structure

```
apps/
  accounts/       user accounts
  announcements/  news and announcements
  chords/         chord library
  courses/        courses
  lessons/        lessons
  songs/          song library
  schemes/        fretboard schemes
  ops/            metrics, health and readiness endpoints
config/           Django settings and URL routing
infrastructure/   Docker, Ansible, observability
```

## License

[GNU Affero General Public License v3.0 or later](./LICENSES/AGPL-3.0-or-later.txt).
All source files carry SPDX headers and are [REUSE compliant](https://reuse.software).
