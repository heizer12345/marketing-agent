# Deploy prototype on Render (frontend) + Railway (API)

Use this instead of Vercel for a **temporary team prototype**. Render free tier is enough for feedback sessions.

## Architecture

```
Browser → Render (frontend/)     → Next.js UI + API proxy
Browser → Railway (repo root)    → Python API + WebSocket (wss://) for Chat
```

REST calls use **same-origin** paths on Render (`/api/v2/...`), so you do **not** need CORS for Home/Library/Memory.

---

## Part 1 — Railway API (one-time, ~2 min)

Your API is already on Railway. It must allow public prototype access:

1. Open your Railway service → **Variables**
2. Ensure:
   ```env
   V2_PUBLIC_ACCESS=1
   OPENAI_API_KEY=sk-...
   SESSION_SECRET=any-long-random-string
   ```
3. **Deployments** → **Deploy** (or wait for auto-deploy from `main`)
4. Test: `https://web-production-d1b50.up.railway.app/api/v2/memory/state`  
   → JSON, **not** `Unauthorized`

If `/_health` is 404, redeploy — latest `main` includes it.

---

## Part 2 — Render frontend (one-click Blueprint)

### Option A — Blueprint (recommended)

1. Sign in at [render.com](https://render.com) (free account; GitHub login works).
2. **New** → **Blueprint**.
3. Connect repo **`heizer12345/marketing-agent`**.
4. Render reads **`render.yaml`** at repo root and creates `marketing-agent-frontend`.
5. Click **Apply** → wait until status is **Live** (~5–8 min first build).

Your app URL will look like:

`https://marketing-agent-frontend.onrender.com`

### Option B — Manual web service

| Setting | Value |
|--------|--------|
| **Type** | Web Service |
| **Repo** | `heizer12345/marketing-agent` |
| **Root Directory** | `frontend` |
| **Runtime** | Node |
| **Build Command** | `npm install && npm run build` |
| **Start Command** | `npm start` |
| **Plan** | Free |

**Environment variables** (required at build + runtime):

```env
NODE_VERSION=20
NEXT_PUBLIC_BACKEND_URL=https://web-production-d1b50.up.railway.app
NEXT_PUBLIC_BACKEND_WS_URL=wss://web-production-d1b50.up.railway.app
```

---

## Verify (30 seconds)

1. `https://YOUR-RENDER-URL.onrender.com/api/diagnostic` → `"ok": true`
2. `https://YOUR-RENDER-URL.onrender.com/home` → no red error banner
3. **Chat** tab → send a test message (WebSocket to Railway)

---

## Free tier notes

- **Cold start:** first visit after ~15 min idle can take **30–60 seconds** (Render spins down free services).
- **Prototype use:** fine for a few reviewers; tell them to wait on first load.
- **Upgrade:** Hobby plan ($7/mo) removes spin-down if you need always-on.

---

## Troubleshooting

| Symptom | Fix |
|--------|-----|
| Red banner “Backend not configured” | Set `NEXT_PUBLIC_BACKEND_URL` on Render, then **Manual Deploy** |
| Red banner “Cannot reach Railway” | Railway down or wrong URL; test `/_health` and `/api/v2/memory/state` |
| Chat fails, Home works | Set `NEXT_PUBLIC_BACKEND_WS_URL=wss://...` (not `https://`) |
| Railway `Unauthorized` | `V2_PUBLIC_ACCESS=1` on Railway + redeploy |
| Build fails on Render | Check build logs; run `cd frontend && npm run build` locally |

---

## Share with reviewers

Send the **Render URL** only (e.g. `https://marketing-agent-frontend.onrender.com`).  
No Vercel login, no git author checks.
