# One-page setup (your live URLs)

You do **not** need to hunt through Vercel/Railway settings — use these direct links.

## Your live URLs

| Service | URL |
|---------|-----|
| **App (use this)** | https://marketing-agent-alpha-five.vercel.app |
| **Railway API** | https://web-production-d1b50.up.railway.app |
| **Wiring test** | https://marketing-agent-alpha-five.vercel.app/api/diagnostic |

> Do **not** use long preview URLs (`marketing-agent-xxxxx-michael-sourcy-projects.vercel.app`) for sharing — they often require Vercel login.

---

## Already done for you

- Vercel env vars `NEXT_PUBLIC_BACKEND_URL` and `NEXT_PUBLIC_BACKEND_WS_URL` → Railway (set 21h ago)
- Vercel project linked: `michael-sourcy-projects/marketing-agent`
- Code fix: Railway auto-enables public API when running on Railway (commit `4f63ad5`)

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
