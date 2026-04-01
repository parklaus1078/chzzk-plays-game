# Chzzk Plays Gamedev (치지직 플레이즈 게임개발)

> AI-Powered Live Game Development Broadcasting System

[![Python](https://img.shields.io/badge/Python-3.12+-3776ab.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61dafb.svg?logo=react&logoColor=white)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178c6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Viewer donation-based AI live streaming system where viewers pay to send prompts to Claude Code, which develops a Unity game in real-time. The Twitch Plays Pokémon of game development.

---

## Overview

**Chzzk Plays Gamedev** is an interactive streaming platform that combines AI-powered development with audience participation. Viewers on Chzzk (Korean streaming platform) can donate to submit prompts that are executed by Claude Code, which modifies a Unity game project live on stream.

The system manages a donation-based prompt queue with 4 pricing tiers, each offering different levels of AI capabilities. All code changes are committed to git, builds are validated automatically, and the entire process is displayed in real-time on an OBS overlay.

### Key Features

- **Real-time AI Development**: Claude Agent SDK executes viewer prompts against a Unity project
- **Tiered Donation System**: 4 pricing tiers (₩1,000 - ₩30,000) with varying AI capabilities
- **Priority Queue Management**: Higher donations get priority, same-tier donations are FIFO
- **3-Layer Security**: Pre-filtering, runtime hooks, and OS-level sandboxing
- **Git Integration**: Auto-commit after every prompt, auto-rollback on build failures
- **Cost Tracking**: Real-time API cost monitoring with daily budget limits
- **OBS Overlay**: React-based WebSocket queue display for broadcasting
- **PIPA Compliance**: Korean privacy law compliance with data export/deletion APIs
- **Health Monitoring**: Comprehensive health checks for all system components

---

## Features

### Core Functionality
- **Donation Queue System**: Prioritized queue with 4 tiers based on donation amount
- **AI Agent Execution**: Claude Agent SDK integration with configurable tools and turn limits
- **Real-time Updates**: WebSocket-based queue state broadcasting to OBS overlay
- **Security Filtering**: Multi-layer security to prevent malicious prompts
- **Automatic Git Management**: WIP commits per prompt, rollback on failures
- **Build Validation**: Unity project validation after code changes

### User Management
- **Ban System**: Admin can ban users who violate security policies
- **Cooldown Management**: Per-user cooldown periods to prevent queue spam (60s to 600s)
- **Privacy Controls**: PIPA-compliant data export and deletion

### Monitoring & Analytics
- **Cost Tracking**: Track API costs per prompt, tier, and session
- **Statistics Dashboard**: Session stats, daily breakdowns, success/failure rates
- **Health Monitoring**: Database, queue, listener, and budget status checks
- **Audit Logging**: Complete access log for privacy compliance

### Frontend
- **OBS Browser Overlay**: Transparent React overlay showing current prompt and queue
- **Tier-based Visual Design**: Color-coded badges and animations per tier
- **Real-time Alerts**: Ban notifications and completion alerts with animations

---

## Tech Stack

### Backend
- **Language**: Python 3.12+
- **Framework**: FastAPI 0.135.2 with uvicorn
- **AI**: Claude Agent SDK 0.1.53
- **AI Model**: Claude Sonnet 4.6 (`claude-sonnet-4-6-20250514`)
- **Donation API**: chzzkpy 2.1.5 (Chzzk Official API v2)
- **Database**: SQLite via aiosqlite (WAL mode)
- **Logging**: structlog (JSON structured logging)
- **Testing**: pytest 8.3+, pytest-asyncio, httpx
- **Dev Tools**: ruff 0.8+ (linter/formatter), mypy 1.13+ (type checker)

### Frontend (OBS Overlay)
- **Framework**: React 19 with TypeScript 5+
- **Build Tool**: Vite 8
- **Styling**: TailwindCSS 4.x (CSS-first config)
- **Animations**: framer-motion 11+
- **Testing**: Vitest 2.1+, React Testing Library 16+
- **Package Manager**: npm

### External Dependencies
- **Game Engine**: Unity 6 LTS (6000.3.x) — Claude's workspace, not in this repo
- **Streaming**: OBS Studio (browser source for overlay)
- **Version Control**: Git with GitHub
- **Package Management**: uv (Python)

---

## Prerequisites

Before you can run this project, you need:

- **Python 3.12+** — Backend runtime ([download](https://www.python.org/downloads/))
- **Node.js 18+** — Frontend build tooling ([download](https://nodejs.org/))
- **uv** — Python package manager ([install](https://github.com/astral-sh/uv#installation))
- **npm** — Node package manager (comes with Node.js)
- **Unity 6 LTS** — Game engine (6000.3.x) for the workspace
- **OBS Studio** — For broadcasting with overlay (optional for development)
- **Git** — Version control system

### API Keys & Credentials

- **Anthropic API Key** — [Get from Anthropic Console](https://console.anthropic.com/)
- **Chzzk Developer Credentials** — Register at [Chzzk Developer Center](https://chzzk.gitbook.io/chzzk)

---

## Getting Started

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/yourusername/chzzk-plays-gamedev.git
cd chzzk-plays-gamedev
```

**2. Set up the backend**

```bash
cd backend
uv sync  # Install all dependencies including dev tools
cd ..
```

**3. Set up the overlay**

```bash
cd overlay
npm install
npm run build
cd ..
```

**4. Create Unity project**

Create a Unity 6 LTS project at a path of your choice. This will be the workspace where Claude Code operates. Note the absolute path for configuration.

**5. Configure environment variables**

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys and paths
```

### Environment Variables

Create a `.env` file in the `backend/` directory with the following variables:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude access | ✅ Yes | — |
| `CLAUDE_MODEL` | Claude model ID to use | No | `claude-sonnet-4-6-20250514` |
| `CHZZK_CLIENT_ID` | Chzzk Developer Center client ID | ✅ Yes | — |
| `CHZZK_CLIENT_SECRET` | Chzzk Developer Center client secret | ✅ Yes | — |
| `UNITY_PROJECT_PATH` | Absolute path to Unity project directory | ✅ Yes | — |
| `DB_PATH` | Path to SQLite database file | No | `data/chzzk_plays.db` |
| `DAILY_BUDGET_USD` | Maximum daily API spend in USD | No | `50.0` |
| `MAX_QUEUE_SIZE` | Maximum queue capacity | No | `50` |
| `HOST` | Server bind address | No | `0.0.0.0` |
| `PORT` | Server port | No | `8080` |
| `DISCORD_WEBHOOK_URL` | Discord webhook for alerts (optional) | No | — |

**Example `.env` file:**

```bash
# Anthropic
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
CLAUDE_MODEL=claude-sonnet-4-6-20250514

# Chzzk Developer Center credentials
CHZZK_CLIENT_ID=your_client_id_here
CHZZK_CLIENT_SECRET=your_client_secret_here

# Paths
UNITY_PROJECT_PATH=/home/user/unity-projects/my-game
DB_PATH=data/chzzk_plays.db

# Limits
DAILY_BUDGET_USD=50.0
MAX_QUEUE_SIZE=50

# Server
HOST=0.0.0.0
PORT=8080

# Discord alerts (optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url
```

### Running the Project

#### Development Mode

**Start backend server:**

```bash
cd backend
source .venv/bin/activate
python run.py
```

**Or use the startup script:**

```bash
./scripts/start.sh
```

The backend will start on `http://localhost:8080`.

**Overlay Development:**

For live development of the overlay with hot reload:

```bash
cd overlay
npm run dev  # Starts dev server on http://localhost:5173
```

Use `http://localhost:5173` as the browser source URL in OBS while developing.

#### Production Mode

**1. Build the overlay:**

```bash
cd overlay
npm run build
```

**2. Run the backend:**

```bash
cd backend
source .venv/bin/activate
python run.py
```

> **Note**: For production, you may want to disable reload mode by editing `run.py` and setting `reload=False`.

**3. Add overlay to OBS:**

1. In OBS, add a **Browser Source**
2. Set URL to: `file:///absolute/path/to/overlay/dist/index.html`
3. Set dimensions to match your layout (e.g., 800x600 or 1920x1080)
4. Set background transparency: `body { background-color: rgba(0, 0, 0, 0); margin: 0px auto; overflow: hidden; }`
5. Enable "Shutdown source when not visible" for better performance

---

## Usage

### Donation Tier System

The system supports 4 donation tiers with increasing capabilities:

| Tier | Amount (KRW) | Max Turns | Allowed Tools | Timeout | Cooldown | Example Prompt |
|------|--------------|-----------|---------------|---------|----------|----------------|
| **한 줄 수정** (One Line) | ₩1,000 | 1 | Read, Edit | 60s | 1 min | "점프 높이 2배로" (Double jump height) |
| **기능 추가** (Feature) | ₩5,000 | 3 | Read, Edit, Write, Bash | 120s | 3 min | "체력바 UI 추가" (Add health bar UI) |
| **대규모 변경** (Major) | ₩10,000 | 8 | Read, Edit, Write, Bash, Glob | 180s | 5 min | "인벤토리 시스템" (Inventory system) |
| **카오스 모드** (Chaos) | ₩30,000 | 15 | Read, Edit, Write, Bash, Glob, Grep | 300s | 10 min | "멀티플레이어 추가" (Add multiplayer) |

### For Streamers

**Starting a Stream:**

1. Start the backend server (`./scripts/start.sh`)
2. Add the overlay as an OBS browser source
3. Configure your OBS scene layout (terminal, overlay, game, chat)
4. Start streaming on Chzzk
5. Donations will automatically be processed from the queue

**Monitoring the System:**

- **Queue Status**: `GET http://localhost:8080/api/queue`
- **Session Stats**: `GET http://localhost:8080/api/stats`
- **Health Check**: `GET http://localhost:8080/api/health`
- **Interactive Docs**: http://localhost:8080/docs

### For Viewers (Testing Donations Manually)

Test donation submission without Chzzk:

```bash
curl -X POST "http://localhost:8080/api/donation" \
  -H "Content-Type: application/json" \
  -d '{
    "donor_name": "테스터",
    "donor_id": "test_user_123",
    "amount": 5000,
    "message": "캐릭터 점프 높이 2배로 증가"
  }'
```

### For Administrators

**Banning a User:**

```bash
curl -X POST "http://localhost:8080/api/admin/ban/USER_ID?reason=Security%20violation"
```

**Unbanning a User:**

```bash
curl -X DELETE "http://localhost:8080/api/admin/ban/USER_ID"
```

**Listing All Bans:**

```bash
curl "http://localhost:8080/api/admin/bans"
```

**Exporting User Data (PIPA Compliance):**

```bash
curl "http://localhost:8080/admin/privacy/export/USER_ID"
```

**Deleting User Data (PIPA Compliance):**

```bash
curl -X DELETE "http://localhost:8080/admin/privacy/delete/USER_ID"
```

---

## Project Structure

```
chzzk-plays-gamedev/
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── api/                  # API endpoints
│   │   │   ├── admin.py          # Ban management
│   │   │   ├── donation.py       # Donation webhook
│   │   │   ├── health.py         # Health monitoring
│   │   │   ├── privacy.py        # PIPA compliance APIs
│   │   │   ├── queue.py          # Queue state + WebSocket
│   │   │   ├── router.py         # Main router
│   │   │   └── stats.py          # Statistics
│   │   ├── core/                 # Core utilities
│   │   │   ├── constants.py      # Tier configs
│   │   │   ├── exceptions.py     # Custom exceptions
│   │   │   └── logging.py        # Structured logging
│   │   ├── db/                   # Database layer
│   │   │   ├── connection.py     # DB init + migrations
│   │   │   ├── migrations/       # SQL migrations
│   │   │   │   └── 001_initial.sql
│   │   │   └── repositories/     # Data access layer
│   │   │       ├── access_log_repo.py
│   │   │       ├── ban_repo.py
│   │   │       ├── donation_repo.py
│   │   │       └── stats_repo.py
│   │   ├── models/               # Pydantic models
│   │   │   ├── donation.py       # Donation + tier
│   │   │   ├── prompt.py         # Prompt request/result
│   │   │   ├── queue.py          # Queue items
│   │   │   └── stats.py          # Statistics models
│   │   ├── services/             # Business logic
│   │   │   ├── agent_runner.py   # Claude Agent SDK
│   │   │   ├── ban.py            # Ban service
│   │   │   ├── connection_manager.py  # WebSocket manager
│   │   │   ├── cooldown.py       # Cooldown tracker
│   │   │   ├── cost_tracker.py   # API cost tracking
│   │   │   ├── donation_listener.py   # chzzkpy listener
│   │   │   ├── git_manager.py    # Git operations
│   │   │   ├── health.py         # Health checks
│   │   │   ├── orchestrator.py   # Main coordinator
│   │   │   ├── privacy.py        # PIPA compliance
│   │   │   └── security.py       # Security filters
│   │   ├── config.py             # Settings (pydantic-settings)
│   │   ├── dependencies.py       # FastAPI dependencies
│   │   └── main.py               # FastAPI app + lifespan
│   ├── tests/                    # Test suite
│   │   ├── integration/          # Integration tests (6 files)
│   │   │   ├── test_api.py
│   │   │   ├── test_ban_flow.py
│   │   │   ├── test_donation_flow.py
│   │   │   ├── test_privacy_e2e.py
│   │   │   ├── test_security_e2e.py
│   │   │   └── test_websocket.py
│   │   ├── unit/                 # Unit tests (17 files)
│   │   │   ├── test_agent_runner.py
│   │   │   ├── test_compliance.py
│   │   │   ├── test_cooldown.py
│   │   │   ├── test_cost_tracker.py
│   │   │   ├── test_donation_listener.py
│   │   │   ├── test_git_manager.py
│   │   │   ├── test_models.py
│   │   │   ├── test_orchestrator.py
│   │   │   ├── test_privacy.py
│   │   │   ├── test_repositories.py
│   │   │   ├── test_security.py
│   │   │   ├── test_tier.py
│   │   │   └── ...
│   │   └── conftest.py           # Shared fixtures
│   ├── data/                     # SQLite database files (gitignored)
│   ├── .env.example              # Environment template
│   ├── .python-version           # Python version (3.12)
│   ├── pyproject.toml            # Python dependencies (uv)
│   ├── COMPLIANCE_CHECKLIST.md   # PIPA/tax compliance checklist
│   └── PRIVACY_POLICY_TEMPLATE.md
├── overlay/                      # React OBS overlay
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── BanAlert.tsx      # Ban notification
│   │   │   ├── CompletionAlert.tsx  # Completion notification
│   │   │   ├── CurrentPrompt.tsx # Current executing prompt
│   │   │   ├── QueueDisplay.tsx  # Main queue display
│   │   │   ├── QueueItem.tsx     # Individual queue item
│   │   │   └── TierBadge.tsx     # Tier badge component
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts   # WebSocket hook
│   │   ├── types/
│   │   │   └── queue.ts          # TypeScript types
│   │   ├── utils/
│   │   │   └── formatters.ts     # Format helpers
│   │   ├── __tests__/            # Component tests
│   │   ├── App.tsx               # Root component
│   │   ├── index.css             # TailwindCSS imports
│   │   └── main.tsx              # Entry point
│   ├── dist/                     # Built overlay (gitignored)
│   ├── public/                   # Static assets
│   ├── index.html
│   ├── package.json              # Node dependencies
│   ├── vite.config.ts            # Vite config
│   ├── tsconfig.json
│   └── vitest.config.ts
├── scripts/                      # Utility scripts
│   ├── health_check.py           # Health check script
│   └── start.sh                  # Startup script
├── .env.example                  # Root env template
├── .gitignore                    # Git ignore rules
├── plan-rough-draft.md           # Project planning doc (Korean)
└── README.md                     # This file
```

---

## Testing

The project includes comprehensive test coverage for both backend and frontend.

### Backend Tests

**Run all tests:**

```bash
cd backend
uv run pytest
```

**Run with coverage:**

```bash
uv run pytest --cov=app --cov-report=html --cov-report=term-missing
```

**Run specific test categories:**

```bash
# Unit tests only
uv run pytest tests/unit/

# Integration tests only
uv run pytest tests/integration/

# Specific test file
uv run pytest tests/unit/test_orchestrator.py -v

# Run tests matching a pattern
uv run pytest -k "test_tier" -v
```

**Test Categories:**

- **Unit Tests** (17 files):
  - Models: Tier classification, queue ordering, validation
  - Services: Orchestrator, agent runner, security, git manager, cost tracker
  - Repositories: Database operations
  - Business Logic: Cooldown, ban system, privacy compliance

- **Integration Tests** (6 files):
  - API endpoints (REST + WebSocket)
  - End-to-end donation flow
  - End-to-end ban flow
  - PIPA compliance workflows
  - Security filtering end-to-end

### Frontend Tests

**Run all tests:**

```bash
cd overlay
npm test
```

**Run in watch mode:**

```bash
npm run test:watch
```

**Test Coverage:**

- Components: `QueueDisplay`, `TierBadge`, `CompletionAlert`, `BanAlert`
- Utilities: Date/time formatters, currency formatters
- Integration: WebSocket connection behavior

### Linting & Code Quality

**Backend (Python):**

```bash
cd backend
uv run ruff check .        # Run linter
uv run ruff format .       # Format code
uv run mypy app/           # Type checking
```

**Frontend (TypeScript):**

```bash
cd overlay
npm run lint               # ESLint
npm run build              # TypeScript compilation check
```

### Health Check Script

Check system health from the command line:

```bash
python scripts/health_check.py
```

This script verifies:
- Database connectivity
- Queue status
- Daily budget consumption
- Listener connection status
- Overall system health

---

## API Documentation

**Interactive API Docs:** Once the server is running, visit:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

### Queue Endpoints

#### `GET /api/queue`

Get current queue state.

**Response:**
```json
{
  "current": {
    "donor_name": "username",
    "prompt": "Add jump mechanic",
    "tier": "feature",
    "state": "running",
    "elapsed_ms": 45000
  },
  "pending": [
    {
      "donor_name": "user2",
      "prompt": "Add health bar",
      "tier": "one_line",
      "position": 1
    }
  ],
  "queue_size": 1
}
```

#### `WS /api/ws/queue`

WebSocket endpoint for real-time queue updates.

**Connection:** `ws://localhost:8080/api/ws/queue`

**Message Format:** Same as `GET /api/queue` response, sent on every state change.

**JavaScript Example:**
```javascript
const ws = new WebSocket('ws://localhost:8080/api/ws/queue');
ws.onmessage = (event) => {
  const queueState = JSON.parse(event.data);
  console.log('Current:', queueState.current);
  console.log('Pending:', queueState.pending);
};
```

### Donation Endpoints

#### `POST /api/donation`

Receive donation event (internal/testing endpoint).

**Request Body:**
```json
{
  "donor_name": "홍길동",
  "donor_id": "user_12345",
  "amount": 5000,
  "message": "캐릭터에 이중 점프 기능 추가"
}
```

**Response:**
```json
{
  "status": "queued",
  "prompt_id": null
}
```

### Statistics Endpoints

#### `GET /api/stats`

Get session statistics.

**Response:**
```json
{
  "total_donations": 42,
  "total_revenue_krw": 210000,
  "total_cost_usd": 12.50,
  "success_count": 38,
  "failure_count": 4,
  "margin_percent": 91.2
}
```

#### `GET /api/stats/daily`

Get daily statistics breakdown.

**Response:**
```json
{
  "cost_by_tier": {
    "one_line": 2.30,
    "feature": 5.20,
    "major": 3.80,
    "chaos": 1.20
  }
}
```

### Admin Endpoints

#### `POST /api/admin/ban/{user_id}`

Ban a user.

**Query Parameters:**
- `reason` (required): Reason for ban

**Response:**
```json
{
  "status": "banned",
  "user_id": "user123",
  "reason": "Security violation"
}
```

#### `DELETE /api/admin/ban/{user_id}`

Unban a user.

**Response:**
```json
{
  "status": "unbanned",
  "user_id": "user123"
}
```

#### `GET /api/admin/bans`

List all banned users.

**Response:**
```json
{
  "bans": [
    {
      "user_id": "user123",
      "reason": "Security violation",
      "banned_at": "2026-03-31T12:00:00"
    }
  ],
  "count": 1
}
```

### Privacy Endpoints (PIPA Compliance)

#### `GET /admin/privacy/export/{user_id}`

Export all data for a user (PIPA Article 35).

**Response:**
```json
{
  "user_id": "user123",
  "donations": [...],
  "ban_info": {...},
  "cost_records": [...],
  "exported_at": "2026-03-31T12:00:00"
}
```

#### `DELETE /admin/privacy/delete/{user_id}`

Delete/anonymize user data (PIPA Article 36).

**Response:**
```json
{
  "status": "success",
  "message": "User user123 data anonymized/deleted"
}
```

**Note:** This anonymizes PII (name/ID) while preserving financial records for 5-year tax compliance.

#### `GET /admin/privacy/audit-log?limit=100`

Get access audit log.

**Query Parameters:**
- `limit` (optional): Number of records to return (default: 100)

**Response:**
```json
{
  "logs": [
    {
      "action": "export_user_data",
      "actor": "admin",
      "target_user_id": "user123",
      "created_at": "2026-03-31T12:00:00"
    }
  ],
  "count": 1
}
```

### Health Endpoint

#### `GET /api/health`

Comprehensive health check.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "listener": "connected",
  "queue_size": 3,
  "daily_cost_usd": 12.50,
  "budget_remaining_usd": 37.50,
  "budget_status": "ok"
}
```

**Status Values:**
- `healthy` — All systems operational
- `degraded` — Some non-critical issues
- `unhealthy` — Critical failures

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Follow the existing code style** (use `ruff` for Python, `eslint` for TypeScript)
3. **Write tests** for new features (maintain >80% coverage)
4. **Update documentation** if adding/changing APIs
5. **Run tests** before submitting (`pytest` and `npm test`)
6. **Create a pull request** with a clear description

### Code Style

- **Python**: Follow PEP 8, enforced by `ruff` (100 char line length)
- **TypeScript**: Follow project ESLint config
- **Commit Messages**: Use conventional commits format (e.g., `feat:`, `fix:`, `docs:`)

### Running Linters

```bash
# Backend
cd backend
uv run ruff check .
uv run mypy app/

# Frontend
cd overlay
npm run lint
```

### Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes and write tests
3. Run linters and tests locally
4. Commit with descriptive messages
5. Push and create a pull request

---

## License

MIT License

Copyright (c) 2026 Kay (박근우)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Acknowledgments

- **Claude Agent SDK** — Anthropic's official Python SDK for Claude Code
- **chzzkpy** — Community library for Chzzk API integration
- **FastAPI** — Modern, fast web framework for Python
- **React** — UI library for the OBS overlay
- **Twitch Plays Pokémon** — Original inspiration for crowd-sourced interaction

---

## Roadmap

See [plan-rough-draft.md](./plan-rough-draft.md) for detailed implementation phases (Korean).

**Completed (Phase 1-2):**
- ✅ Core backend architecture with FastAPI
- ✅ Donation tier classification system
- ✅ Priority queue management with asyncio
- ✅ Claude Agent SDK integration with hooks
- ✅ WebSocket real-time queue updates
- ✅ 3-layer security filtering (pre-filter, runtime hooks, sandbox)
- ✅ Ban system with automatic security violation detection
- ✅ Git auto-commit/revert functionality
- ✅ OBS overlay (React 19 + TailwindCSS 4)
- ✅ PIPA compliance endpoints (export, deletion, audit logging)
- ✅ Cost tracking with daily budget enforcement
- ✅ Health monitoring with Discord webhook alerts
- ✅ Comprehensive test suite (23 test files, unit + integration)

**Planned (Phase 3+):**
- 🔜 Vote system (chat votes influence prompt priority)
- 🔜 "Revert" donation tier (undo last change via special donation)
- 🔜 Model routing (use Claude Haiku for simple tasks to reduce costs)
- 🔜 Multi-game project support (switch between different Unity projects)
- 🔜 24-hour full automation mode
- 🔜 Highlight clip auto-generation for YouTube

---

## Support

- **Documentation**: [plan-rough-draft.md](./plan-rough-draft.md) (Korean)
- **Compliance**: [backend/COMPLIANCE_CHECKLIST.md](./backend/COMPLIANCE_CHECKLIST.md)
- **Privacy Policy**: [backend/PRIVACY_POLICY_TEMPLATE.md](./backend/PRIVACY_POLICY_TEMPLATE.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/chzzk-plays-gamedev/issues)
- **Chzzk Platform**: [https://chzzk.naver.com](https://chzzk.naver.com)

---

**Built with Claude Sonnet 4.6** 🤖 | **Powered by Claude Agent SDK**
