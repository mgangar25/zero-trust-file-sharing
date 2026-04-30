# Zero-Trust File Sharing System

A full-stack secure file-sharing portfolio project built with FastAPI, Next.js,
Supabase PostgreSQL, and Cloudflare R2. Users can register, log in, upload files,
download owner-owned files, create temporary public share links, and review audit
logs for share-link access attempts.

The main security goal is simple: object storage should not need to be trusted
with plaintext files. The backend encrypts file bytes before upload, stores only
wrapped file keys in metadata, and enforces ownership and share-link rules before
any download.

## Tech Stack

- Frontend: Next.js, TypeScript, Tailwind CSS, App Router.
- Backend: FastAPI, SQLAlchemy, Pydantic.
- Database: Supabase PostgreSQL.
- Storage: Cloudflare R2 through S3-compatible `boto3`.
- Auth: JWT with `python-jose`, bcrypt hashing with `passlib`.
- Encryption: AES-GCM with `cryptography`.
- Tests: Pytest, FastAPI TestClient, SQLite test database, mocked storage.

## Features

- JWT registration and login.
- Protected dashboard for authenticated users.
- AES-GCM encrypted file uploads.
- Owner-only file listing, download, and delete.
- Temporary share links for individual files.
- Optional share-link passwords.
- Share-link expiration, revocation, and download limits.
- One-time raw share token display.
- Audit logs for successful and failed public download attempts.

## Architecture

```text
Next.js frontend
    |
    | Bearer JWT or public share token
    v
FastAPI backend
    |
    +-- Supabase PostgreSQL
    |      users, file metadata, wrapped file keys,
    |      share-link hashes, password hashes, audit logs
    |
    +-- Cloudflare R2
           encrypted file bytes only
```

## Demo Flow

1. Register or log in.
2. Upload a file from the dashboard.
3. Download the owner-owned file.
4. Create a secure share link with expiration, optional password, and optional
   download limit.
5. Open the public share URL and download the file without logging in.
6. View audit logs showing successful and blocked access attempts.

## Security Highlights

- Files are encrypted before Cloudflare R2 upload.
- R2 stores encrypted bytes, not readable file contents.
- Every file receives a unique random AES-256 file key.
- File keys are wrapped by `MASTER_ENCRYPTION_KEY` before storage in metadata.
- User passwords and optional share passwords are hashed.
- Raw share tokens are shown once; only token hashes are stored.
- Public share links support expiration, revocation, and max download counts.
- Audit logs record public download outcomes and failure reasons.

## Screenshots

Screenshots are intended to live in `docs/screenshots/`.

Planned recruiter-demo captures:

- `docs/screenshots/landing.png`
- `docs/screenshots/dashboard.png`
- `docs/screenshots/share-link-created.png`
- `docs/screenshots/public-share-download.png`
- `docs/screenshots/audit-logs.png`
- `docs/screenshots/security-page.png`

## Local Setup

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open the app at `http://localhost:5173` and the API docs at
`http://localhost:8000/docs`.

## Deployment

Backend on Render:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Render environment variable names:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_ENDPOINT_URL`
- `MASTER_ENCRYPTION_KEY`
- `FRONTEND_ORIGIN`

`FRONTEND_ORIGIN` should be the final deployed Vercel origin once the frontend
URL exists. Local development still allows `http://localhost:5173` and
`http://localhost:3000`.

Frontend on Vercel:

- Root Directory: `frontend`
- Build Command: `npm run build`
- Output: handled automatically by Next.js/Vercel

Vercel environment variable:

```bash
NEXT_PUBLIC_API_URL=<Render backend URL>
```

## Environment Variables

Backend variables belong in `backend/.env` and should never be committed:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `FRONTEND_ORIGIN`
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_ENDPOINT_URL`
- `MASTER_ENCRYPTION_KEY`

Frontend variables belong in `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Only browser-safe values should use `NEXT_PUBLIC_`.

## Testing

Backend automated tests:

```bash
cd backend
pytest
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

Manual checklist:

- Register and log in.
- Upload, list, download, and delete an owner-owned file.
- Create a share link and download from the public share page.
- Test password protection, revocation, expiration, and download limits.
- Confirm `/audit` shows expected success and failure reasons.
- Review `/security` for the project security explanation.

## Resume Bullet Options

- Built a full-stack zero-trust file-sharing system with FastAPI, Next.js,
  Supabase PostgreSQL, Cloudflare R2, JWT auth, AES-GCM encryption, and audit
  logging.
- Implemented encrypted file storage with per-file AES-256 keys, master-key
  wrapping, owner-scoped authorization, and secure temporary share links.
- Developed a recruiter-friendly Next.js dashboard for encrypted uploads,
  revocable public sharing, download limits, password-protected links, and audit
  log review.

## Future Improvements

- Move production JWT storage to secure, SameSite, httpOnly cookies.
- Add Alembic migrations for production-grade schema changes.
- Add pagination/search for files, share links, and audit logs.
- Add frontend component tests and end-to-end browser tests.
- Add deployment documentation for frontend, backend, database, and R2.

## Portfolio Warning

This is a portfolio project. Do not upload real sensitive files.
