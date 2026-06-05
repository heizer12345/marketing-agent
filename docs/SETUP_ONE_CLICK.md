# One-page setup (prototype)

**Recommended:** [Render frontend + Railway API](DEPLOY_RENDER.md) — no Vercel git/team issues.

## Your live URLs

| Service | URL |
|---------|-----|
| **Railway API** | https://web-production-d1b50.up.railway.app |
| **Render app** | *create via Blueprint — see below* |
| **Vercel (optional)** | https://marketing-agent-alpha-five.vercel.app |

---

## Render (fastest path)

1. [render.com](https://render.com) → **New** → **Blueprint**
2. Repo: `heizer12345/marketing-agent` → **Apply** (uses `render.yaml`)
3. Share the `*.onrender.com` URL with reviewers

Full steps: [DEPLOY_RENDER.md](DEPLOY_RENDER.md)

---

## Already in the repo

- `render.yaml` — one-click Render frontend with Railway env vars pre-filled
- GitHub: `heizer12345/marketing-agent`
- Railway auto-enables `V2_PUBLIC_ACCESS` when deployed on Railway

---

## One thing you must click on Railway

Railway must **redeploy** the latest GitHub code so the API allows Vercel.

1. Open: https://railway.com/project/6ff065a1-98d2-4e68-bf80-8200de639683/service/52bea659-8503-40df-b2ad-0155ac696ff8
2. Click **Deployments** tab
3. Click **Deploy** (or wait for auto-deploy from GitHub `main`)
4. Wait until status = **Active** (green)

Optional variable (only if still 401 after redeploy):

- **Variables** tab → **New Variable** → `V2_PUBLIC_ACCESS` = `1` → Redeploy

---

## Verify (30 seconds)

1. Open https://web-production-d1b50.up.railway.app/api/v2/memory/state  
   → should return JSON (not `Unauthorized`)

2. Open https://marketing-agent-alpha-five.vercel.app/api/diagnostic  
   → should show `"ok": true`

3. Open https://marketing-agent-alpha-five.vercel.app/home  
   → red error banner should be gone

---

## Chat (WebSocket)

Vercel env already has `NEXT_PUBLIC_BACKEND_WS_URL=wss://web-production-d1b50.up.railway.app`  
After Railway redeploy, test **Chat** tab on the production URL above.
