# Deploy: Railway (API) + Vercel (UI)

Use this for the **compassionate fascination** Railway project (or any new Railway backend) wired to your Vercel frontend.

## Architecture

```
Browser → Vercel (frontend/)     → UI only
Browser → Railway (repo root)    → REST via Vercel proxy + WebSocket direct (wss://)
```

---

## Part 1 — Railway backend

### 1. Create / use project

1. Open [Railway](https://railway.app) → project **compassionate fascination** (or create one).
2. **New Service** → **GitHub Repo** → `heizer12345/marketing-agent`.
3. **Important:** Service root = **repository root** (where `main.py` and `requirements.txt` live).  
   **Do not** set root to `frontend/` — that is only for Vercel.

### 2. Settings (Railway → Service → Settings)

| Setting | Value |
|--------|--------|
| **Source → Root Directory** | *(empty — repo root, NOT `frontend/`)* |
| **Build → Builder** | **Dockerfile** *(not Railpack / Nixpacks)* |
| **Build → Dockerfile path** | `Dockerfile` |
| Start Command | `python main.py` *(or leave empty — uses Dockerfile CMD)* |
| Health Check Path | `/_health` |

If you still see `pip: command not found`, Railway is using **Railpack/Nixpacks** instead of Docker. Fix the **Builder** setting above, add variable `NO_CACHE=1`, and redeploy.

Optional variable: `RAILWAY_DOCKERFILE_PATH=Dockerfile`

### 3. Variables (Railway → Variables)

**Required for prototype:**

```env
OPENAI_API_KEY=sk-...
V2_PUBLIC_ACCESS=1
SESSION_SECRET=generate-a-long-random-string
```

**Recommended:**

```env
DEV_MODE=0
PORT=8000
```

Railway sets `PORT` automatically; `main.py` already reads it.

**Optional** (app works without these; features degrade):

```env
GA4_PROPERTY_ID=...
SEARCH_CONSOLE_SITE_URL=sc-domain:sourcy.ai
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}
META_ACCESS_TOKEN=...
```

**Only if you use cross-origin API calls** (not needed when Vercel uses rewrites):

```env
CORS_ORIGINS=https://your-app.vercel.app
```

### 4. Deploy & copy public URL

1. Deploy → wait until **Active**.
2. **Settings → Networking → Generate Domain** (e.g. `marketing-agent-production.up.railway.app`).
3. Test in browser: `https://YOUR-RAILWAY-DOMAIN/_health` → should show `{"ok":true,...}`.

---

## Part 2 — Vercel frontend

### 1. Project settings

| Setting | Value |
|--------|--------|
| Root Directory | `frontend` |
| Framework | Next.js |

### 2. Environment variables

Set for **Production** and **Preview**, then **Redeploy**:

```env
NEXT_PUBLIC_BACKEND_URL=https://YOUR-RAILWAY-DOMAIN
NEXT_PUBLIC_BACKEND_WS_URL=wss://YOUR-RAILWAY-DOMAIN
```

No trailing slash. Use `https` / `wss` (Railway provides HTTPS).

### 3. Redeploy

Deployments → latest → **Redeploy** (env vars apply at **build** time for rewrites).

---

## Part 3 — Verify

| Test | Expected |
|------|----------|
| `https://RAILWAY/_health` | `ok: true` |
| Vercel `/home` | No red error banner; briefing loads or “No snapshot yet” |
| Vercel `/chat` | Send message; WebSocket connects (not stuck on “Reconnecting…”) |

---

## Troubleshooting

| Symptom | Fix |
|--------|-----|
| Railway build `pip: command not found` | Fixed in repo via `Dockerfile` — redeploy from latest `main` |
| Vercel “Failed to fetch” | Set `NEXT_PUBLIC_BACKEND_URL`, redeploy Vercel |
| Chat “Reconnecting…” | Set `NEXT_PUBLIC_BACKEND_WS_URL=wss://...` |
| 401 on API | Railway: `V2_PUBLIC_ACCESS=1`, restart service |
| Home spins “Refreshing…” | First briefing runs 1–2 min on Railway; wait or check Railway logs |

---

## Repo config files (already in git)

- `railway.toml` / `railway.json` — start command + health check
- `nixpacks.toml` — Python-only build for monorepo
- `Procfile` — `web: python main.py`
- `frontend/.env.example` — Vercel variable template
