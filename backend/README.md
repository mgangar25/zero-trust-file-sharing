# Zero-Trust File Sharing System Backend

This is the backend foundation for a portfolio project: a secure file-sharing
web app with custom authentication, encrypted file storage, temporary share
links, revocation, download limits, optional password-protected links, and audit
logs.

This first version focuses on the backend structure and starter code. File
sharing links, migrations, tests, and deployment will be added in later steps.

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- Supabase PostgreSQL
- JWT authentication with `python-jose`
- bcrypt password hashing with `passlib`
- AES-GCM file encryption with `cryptography`
- Cloudflare R2 storage through `boto3`
- Pytest planned

## Important Security Note

This is still a portfolio and learning project, so avoid uploading real
sensitive files. The backend now encrypts file bytes before R2 storage, but
production systems need more hardening, monitoring, key rotation, and audits.

## Backend Setup

Run these commands from the project root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and fill in real values. The file should contain:

```bash
DATABASE_URL=your-supabase-postgres-connection-string
JWT_SECRET_KEY=use-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
FRONTEND_URL=http://localhost:5173
R2_ACCOUNT_ID=your-cloudflare-account-id
R2_ACCESS_KEY_ID=your-r2-access-key-id
R2_SECRET_ACCESS_KEY=your-r2-secret-access-key
R2_BUCKET_NAME=zero-trust-files
R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
MASTER_ENCRYPTION_KEY=your-base64-encoded-32-byte-master-key
```

Secrets like `DATABASE_URL`, `JWT_SECRET_KEY`, and R2 access keys should stay in
`.env` and should not be committed to GitHub. `MASTER_ENCRYPTION_KEY` is also a
secret: if it leaks alongside database access, encrypted file keys could be
decrypted.

The app validates required environment variables at startup. If `DATABASE_URL`
or `JWT_SECRET_KEY` is missing or blank, or if `MASTER_ENCRYPTION_KEY` is not a
valid base64-encoded 32-byte key, the server will stop with a clear error
instead of silently running in an unsafe state.

## Generate the Master Encryption Key

For local development, generate a random 32-byte AES-256 master key with:

```bash
python3 -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
```

Copy the printed value into `.env`:

```bash
MASTER_ENCRYPTION_KEY=paste-generated-value-here
```

This local development key wraps, or encrypts, each per-file key before that
per-file key is saved in the database. Do not commit it. In production, a real
key management service such as AWS KMS, GCP KMS, or a Cloudflare-managed key
system would be safer because it can protect, audit, and rotate keys.

## Run the Backend

From inside the `backend` folder:

```bash
uvicorn app.main:app --reload
```

Then visit:

- `http://localhost:8000/`
- `http://localhost:8000/health`
- `http://localhost:8000/docs`
- `http://localhost:8000/health/db`

FastAPI automatically creates interactive API docs at `/docs`.

During this early development stage, the backend automatically creates database
tables on startup using SQLAlchemy's `Base.metadata.create_all(...)`. This is
helpful while learning and building the first version. Later, the project should
move to Alembic migrations so every database schema change is versioned.

## Current Endpoints

- `POST /auth/register` creates a user with a bcrypt password hash.
- `POST /auth/login` returns a JWT access token from a JSON email/password body.
- `POST /auth/token` returns a JWT access token from OAuth2 form data for Swagger.
- `POST /files/upload` uploads a file to R2 and saves metadata for the logged-in user.
- `GET /files` lists the logged-in user's file metadata.
- `GET /files/{file_id}` returns one file metadata record owned by the user.
- `GET /files/{file_id}/download` downloads one owned file from R2.
- `DELETE /files/{file_id}` soft-deletes one file metadata record.
- `POST /share/files/{file_id}` creates a temporary share link for one owned file.
- `GET /share` lists share links owned by the logged-in user.
- `DELETE /share/{share_id}` revokes one owned share link.
- `POST /share/{token}/download` downloads a shared file without login if the link is valid.
- `GET /audit` lists audit logs for the logged-in user's files.

The protected endpoints require this header:

```text
Authorization: Bearer your-jwt-token
```

## Test Register/Login in `/docs`

1. Start the server with `uvicorn app.main:app --reload`.
2. Open `http://localhost:8000/docs`.
3. Run `POST /auth/register` with an email and password.
4. Click the **Authorize** button in `/docs`.
5. Enter the registered email in the `username` field and the password in the
   `password` field.
6. Click **Authorize**. Swagger sends those values to `POST /auth/token`.
7. Run `GET /files`. A new user should get an empty list, which proves the JWT
   was accepted even though uploads are not built yet.

The project also keeps `POST /auth/login` for JSON clients such as React/Axios:

```json
{
  "email": "test@example.com",
  "password": "Test12345"
}
```

If registration succeeds, a new user row should appear in your Supabase
PostgreSQL `users` table. The `password_hash` column should contain a bcrypt
hash, never the plain password.

## Cloudflare R2 Setup

Cloudflare R2 is object storage. A bucket is the private container for uploaded
objects, and an object key is the path-like name of one object inside that
bucket. This project uses keys like:

```text
users/{user_id}/files/{file_id}/{filename}
```

That structure groups files by owner and avoids overwriting when two files share
the same filename. R2 works with `boto3` because R2 supports the S3-compatible
API.

Files are encrypted with AES-GCM before they are uploaded to R2. The original
filename, MIME type, encrypted file key, and encryption nonce are saved in
Supabase as metadata.

## Encryption Flow

Upload flow:

1. The owner uploads plaintext bytes to the API.
2. The API generates a random per-file AES-256 key.
3. The API encrypts file bytes with AES-GCM using that per-file key.
4. The API encrypts, or wraps, the per-file key with `MASTER_ENCRYPTION_KEY`.
5. The API stores encrypted bytes in R2.
6. The API stores metadata, the encrypted file key, and the AES-GCM nonce in
   Supabase.

Download flow:

1. The owner requests `GET /files/{file_id}/download`.
2. The API confirms the JWT user owns the file and the file is not deleted.
3. The API downloads encrypted bytes from R2.
4. The API decrypts the per-file key using `MASTER_ENCRYPTION_KEY`.
5. The API decrypts the file bytes with AES-GCM.
6. The API returns the original readable file bytes to the owner.

## Test Encrypted R2 File Uploads in `/docs`

This checkpoint uploads encrypted file bytes to Cloudflare R2 and saves metadata
in Supabase.

1. Stop the backend if it is already running.
2. Add `MASTER_ENCRYPTION_KEY` to `.env`.
3. Restart the backend with `uvicorn app.main:app --reload`.
4. Open `http://localhost:8000/docs`.
5. Click **Authorize** and log in with a registered email/password such as
   `test@example.com` / `Test12345`.
6. Run `POST /files/upload` with any small test file.
7. Open the Cloudflare dashboard and verify the object appears in the
   `zero-trust-files` bucket.
8. Confirm the API response includes `id`, `owner_id`, `original_filename`,
   `file_size`, `mime_type`, `created_at`, and `deleted_at`.
9. Run `GET /files` and confirm the uploaded file metadata appears.
10. Run `GET /files/{file_id}` using the id from the upload response.
11. Run `GET /files/{file_id}/download` and confirm the downloaded file opens
    normally.
12. Run `DELETE /files/{file_id}` to delete the R2 object and soft-delete the
    metadata row.
13. Run `GET /files` again and confirm the deleted file is hidden.

## Test Secure Share Links in `/docs`

Share links are public download tokens for one encrypted file. The database
stores only `token_hash`, never the raw token. That means the raw token appears
only once in the create response.

1. Authorize in Swagger as a registered user such as `test@example.com`.
2. Upload a small file with `POST /files/upload`.
3. Copy the returned `file_id`.
4. Run `POST /share/files/{file_id}` with a body like:

```json
{
  "expires_in_minutes": 30,
  "max_downloads": 1,
  "password": null
}
```

5. Copy `raw_token` from the create response.
6. Log out in Swagger or leave auth alone; `POST /share/{token}/download` is public.
7. Run `POST /share/{token}/download` with `{}` as the body and confirm the file downloads.
8. Run the same download again when `max_downloads` is `1`; it should fail.
9. Create another share link with a password, for example:

```json
{
  "expires_in_minutes": 30,
  "max_downloads": null,
  "password": "SharePass123"
}
```

10. Test `POST /share/{token}/download` with a wrong password and then the right password:

```json
{
  "password": "SharePass123"
}
```

11. Revoke a link with `DELETE /share/{share_id}`.
12. Try downloading with the revoked token and confirm it fails.
13. Run `GET /audit` as the owner and confirm successful and failed share-link
    attempts are logged.

Public share-link downloads still decrypt the file server-side only after the
token passes expiration, revocation, max-download, optional password, and file
existence checks.

## Run Automated Tests

The test suite uses SQLite and mocked storage helpers, so it does not require
real Supabase or Cloudflare R2 credentials.

```bash
pytest
```

## Planned Features

- Database migrations with Alembic
- Access audit logging
- Rate limiting for login and share-link routes
- Pytest test suite
- Vercel frontend deployment
- Render backend deployment
- GitHub Actions CI
