# Zero-Trust File Sharing System

A full-stack secure file-sharing portfolio project. Users can register, log in,
upload encrypted files, download owner-owned files, create temporary share links,
revoke access, require optional share passwords, limit downloads, and review
audit logs for public access attempts.

The project is intentionally built around practical backend security concerns:
authentication, authorization, encryption, object storage, token handling,
password hashing, and observable access decisions.

## Tech Stack

- Frontend: Next.js, TypeScript, Tailwind CSS, App Router.
- Backend: FastAPI, SQLAlchemy, Pydantic.
- Database: Supabase PostgreSQL.
- Object storage: Cloudflare R2 through the S3-compatible `boto3` API.
- Auth: JWT with `python-jose`, bcrypt password hashing with `passlib`.
- Encryption: AES-GCM with `cryptography`.
- Testing: Pytest, FastAPI TestClient, SQLite test database, mocked storage.

## Features

- User registration and login with JWT bearer tokens.
- Protected dashboard route in the frontend.
- Encrypted file upload through `POST /files/upload`.
- Owner-only file listing, metadata, download, and delete.
- Temporary public share links for individual files.
- Share-link expiration, revocation, and max download limits.
- Optional share-link passwords.
- One-time raw share token display.
- Audit logs for successful and failed public download attempts.
- Polished demo UI for recruiter walkthroughs.

## Architecture Summary

```text
Next.js frontend
    |
    | Bearer JWT / public share token
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

The backend owns the security decisions. The frontend is a demo-friendly client
for calling the API, while FastAPI verifies users, checks file ownership,
encrypts and decrypts file bytes, enforces share-link rules, and writes audit
logs.

## Security Model

- Files are encrypted before object storage, so Cloudflare R2 stores ciphertext.
- Every file receives a unique random AES-256 file key.
- File keys are wrapped by `MASTER_ENCRYPTION_KEY` before metadata is saved.
- User passwords are hashed with bcrypt.
- Optional share-link passwords are hashed with bcrypt.
- Raw share tokens are shown only once; the database stores token hashes.
- Public share links can expire, be revoked, and enforce max download counts.
- Audit logs record successful and failed public download attempts, including
  reasons such as `success`, `invalid_password`, `revoked`, `expired`, and
  `max_downloads_reached`.
- Deleted files are soft-deleted in metadata after the R2 object is removed.

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `backend/.env` with your own local development settings. Never commit
real secrets.

Run the backend:

```bash
uvicorn app.main:app --reload
```

Open Swagger:

```text
http://localhost:8000/docs
```

## Frontend Setup

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The frontend intentionally runs on port `5173` because the backend CORS default
allows that local origin.

## Environment Variables

Backend variables live in `backend/.env` and should never be committed:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `FRONTEND_URL`
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_ENDPOINT_URL`
- `MASTER_ENCRYPTION_KEY`

Frontend variables live in `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Only public browser-safe values belong in the frontend. Anything prefixed with
`NEXT_PUBLIC_` is readable by the browser.

## Manual Test Checklist

- Register a new user.
- Log in with the new user.
- Confirm the dashboard is protected when logged out.
- Upload a small file.
- Confirm the file list refreshes.
- Download the uploaded file.
- Create a share link.
- Open the public share URL in a logged-out or private browser session.
- Download through the public share page.
- Create a password-protected share link and test missing/invalid passwords.
- Create a share link with a low download limit and confirm it is enforced.
- Revoke a share link and confirm future downloads are blocked.
- Open `/audit` and confirm success/failure reasons appear.
- Open `/security` and review the security model explanation.

## Automated Tests

Backend tests use SQLite and mocked storage, so they do not require real
Supabase or Cloudflare R2 credentials.

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

## Screenshots

Screenshots can be added under `docs/screenshots/`.

Suggested recruiter-demo captures:

- Landing page
- Login/register flow
- Dashboard with uploaded files
- Share-link creation result
- Public share download page
- Audit logs page
- Security model page

## Future Improvements

- Move production JWT storage to secure, SameSite, httpOnly cookies.
- Add refresh tokens or short-lived access-token rotation.
- Add Alembic migrations for production-grade schema changes.
- Add file preview support for safe MIME types.
- Add pagination and search for files, share links, and audit logs.
- Add frontend component tests and end-to-end browser tests.
- Add deployment docs for the frontend, backend, database, and R2 bucket.
- Add object lifecycle cleanup for expired links or old soft-deleted metadata.

## Portfolio Warning

This is a portfolio project. Do not upload real sensitive files.
