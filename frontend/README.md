# Zero-Trust File Sharing Frontend

Next.js frontend for the FastAPI zero-trust file-sharing backend.

## Stack

- Next.js App Router
- TypeScript
- Tailwind CSS
- `lucide-react` icons

## Local Setup

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

The dev server intentionally uses port `5173` because the backend CORS default
allows that local frontend origin.

## Environment

Only public browser configuration belongs in this frontend environment file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Do not put database URLs, JWT secrets, R2 keys, or encryption keys in the
frontend. Anything prefixed with `NEXT_PUBLIC_` is readable by the browser.

## Routes

- `/` polished project overview
- `/login` JWT login
- `/register` account creation
- `/dashboard` upload, file list, downloads, deletes, and share links
- `/audit` share-link access logs
- `/security` security model explanation
- `/share/[token]` public share-link download page

## Useful Commands

```bash
npm run lint
npm run build
npm run dev
```

## Vercel Deployment

- Root Directory: `frontend`
- Build Command: `npm run build`
- Output: handled automatically by Next.js/Vercel

Set this Vercel environment variable after the Render backend URL exists:

```bash
NEXT_PUBLIC_API_URL=<Render backend URL>
```
