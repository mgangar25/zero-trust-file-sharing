# Zero-Trust File Sharing System

A secure file-sharing web application backend where users can upload encrypted
files, create temporary share links, revoke access, limit downloads, require
optional share passwords, and review audit logs.

This is a resume-level portfolio project focused on practical secure backend
engineering: authentication, encryption, object storage, authorization checks,
and observable access attempts.

## Problem Statement

Normal file-sharing systems often trust the storage provider, expose long-lived
links, or provide limited visibility into failed access attempts. This project
explores a zero-trust-style design where files are encrypted before object
storage, public access is limited by explicit rules, and access attempts are
audited.

## Key Features

- JWT authentication with custom register/login.
- AES-GCM encrypted file storage.
- Cloudflare R2 object storage.
- Supabase PostgreSQL metadata storage.
- Temporary secure share links.
- Optional password-protected links.
- Max download limits.
- Link revocation.
- Audit logs for successful and failed share access attempts.

## Tech Stack

- Backend: Python, FastAPI, SQLAlchemy, Pydantic.
- Database: Supabase PostgreSQL.
- Auth: JWT with `python-jose`, bcrypt password hashing with `passlib`.
- Encryption: AES-GCM with `cryptography`.
- Storage: Cloudflare R2 through the S3-compatible `boto3` API.
- Testing: Pytest, FastAPI TestClient, SQLite test database, mocked storage.
- Frontend: planned later with React, TypeScript, Vite, Tailwind CSS.

## Architecture Overview

```text
Client / Swagger
    |
    v
FastAPI backend
    |
    +-- Supabase PostgreSQL
    |      users, file metadata, share links, audit logs
    |
    +-- Cloudflare R2
           encrypted file bytes only
```

The backend owns all security decisions. Users authenticate with JWTs, file
owners can upload/download their own files, and public share tokens grant limited
access to exactly one file.

## Security Model

- Files are encrypted before Cloudflare R2 upload, so R2 stores ciphertext rather
  than readable file contents.
- Every file gets a random per-file AES-256 key.
- A local development `MASTER_ENCRYPTION_KEY` wraps each per-file key before the
  wrapped key is saved in PostgreSQL.
- Share tokens are shown once, then only a token hash is stored in the database.
- User passwords and optional share-link passwords are hashed with bcrypt.
- Access logs track successful and failed public download attempts, including
  reasons like revoked, invalid password, and max downloads reached.

## Local Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `backend/.env` with your Supabase, JWT, R2, and encryption settings.
Never commit real secrets.

Generate a local development master encryption key with:

```bash
python3 -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
```

Run the backend:

```bash
uvicorn app.main:app --reload
```

Open Swagger:

```text
http://localhost:8000/docs
```

## Backend API Summary

- `POST /auth/register` creates a user.
- `POST /auth/login` logs in with JSON.
- `POST /auth/token` supports Swagger Authorize.
- `POST /files/upload` encrypts and uploads a file.
- `GET /files` lists owned files.
- `GET /files/{file_id}/download` decrypts and downloads an owned file.
- `DELETE /files/{file_id}` deletes the R2 object and soft-deletes metadata.
- `POST /share/files/{file_id}` creates a temporary public share link.
- `GET /share` lists owned share links.
- `DELETE /share/{share_id}` revokes a share link.
- `POST /share/{token}/download` downloads through a valid public share token.
- `GET /audit` lists access logs for owned files.

## Testing

Backend tests use SQLite and mocked storage, so they do not require real
Supabase or Cloudflare R2 secrets.

```bash
cd backend
pytest
```

## Portfolio Warning

This is a portfolio project. Do not upload real sensitive files.
