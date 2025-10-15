# ClickSafe — API Documentation (polished)

This document is a reference for the ClickSafe backend API (FastAPI).

Base URL (development): `http://localhost:8000`

## Quick links

- Overview
- Authentication
- Endpoints
  - Root
  - /auth
  - /api/qr
  - /api/cert
  - /dashboard, /scans
- Data models & schemas
- Environment variables
- Run locally
- Examples

---

## Overview

ClickSafe exposes REST endpoints for:

- User authentication (email/password + OAuth)
- QR image uploads and URL safety analysis
- CERT reporting (email reports for high-risk URLs)
- User scan history, dashboard summaries, and admin views

The backend uses FastAPI with SQLAlchemy models stored in SQLite by default.

## Authentication

- JWT-based tokens (access + refresh). Access tokens are used in the `Authorization: Bearer <token>` header.
- Key endpoints: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`.

# ClickSafe — API Documentation (Academic Submission)

## Abstract

This document provides a concise, academic-style reference for the ClickSafe backend API (FastAPI). It describes the system purpose, primary endpoints, request/response examples, core data models, configuration, and how to run and test the service locally.

## Project summary

- Purpose: Detect and evaluate safety of QR-encoded URLs, provide user scan history and CERT reporting for suspected phishing.
- Backend: FastAPI, SQLAlchemy (SQLite default), Python ML artifacts stored as pickle files.
- Frontend: React (Vite) -- camera capture → image upload → backend decoding/analysis.

Base URL (development): `http://localhost:8000`

1. High-level API summary

---

Table of core endpoints (method | path | auth | short description)

| Method | Path                 |     Auth | Purpose                                      |
| ------ | -------------------- | -------: | -------------------------------------------- |
| GET    | /                    |       No | Service info / version                       |
| POST   | /auth/register       |       No | Create user account                          |
| POST   | /auth/login          |       No | Login → returns access/refresh tokens        |
| POST   | /auth/refresh        |       No | Swap refresh token for new access token      |
| POST   | /api/qr/scan/image   | Optional | Upload image with QR code → decode + analyze |
| POST   | /api/qr/scan/url     | Optional | Analyze URL (no image)                       |
| GET    | /api/qr/scan/history |      Yes | List authenticated user's scans (paginated)  |
| POST   | /api/qr/report/cert  |      Yes | Submit a CERT report (high-risk URLs)        |
| POST   | /api/cert/report     |      Yes | CERT report endpoint (alternative router)    |
| GET    | /dashboard/          |      Yes | User dashboard summary                       |
| POST   | /scans/              |      Yes | Free-form scan (simple detector)             |

2. Authentication

---

- Scheme: JWT access token (Bearer). A refresh token is issued at login for renewing access.
- Header: Authorization: Bearer <access_token>

3. Representative request / response examples

---

3.1 Register (create user)

Request (POST /auth/register)

```json
{
  "email": "alice@example.com",
  "username": "alice",
  "full_name": "Alice Example",
  "password": "Str0ngP@ss!"
}
```

Successful response (201)

```json
{
  "id": 1,
  "email": "alice@example.com",
  "username": "alice",
  "is_active": true
}
```

3.2 Login

Request (POST /auth/login)

```json
{
  "email": "alice@example.com",
  "password": "Str0ngP@ss!"
}
```

Response (200)

```json
{
  "access_token": "ey...",
  "refresh_token": "ey...",
  "token_type": "bearer",
  "user": { "id": 1, "email": "alice@example.com", "username": "alice" }
}
```

3.3 Upload QR image (scan)

Request (POST /api/qr/scan/image) — multipart/form-data

- Field: `file` — image file containing QR code.
- Optional: Authorization header to save to user history.

Example successful response (200)

```json
{
  "qr_detection": { "raw_data": "https://example.com", "type": "QRCODE" },
  "safety_analysis": {
    "virustotal": { "positives": 0 },
    "heuristics": { "has_ip": false }
  },
  "combined_assessment": { "risk_score": 23, "risk_level": "low" },
  "scan_id": 123,
  "processed_at": "2025-10-15T12:34:56Z"
}
```

3.4 Analyze URL directly

Request (POST /api/qr/scan/url)

```json
{
  "url": "https://example.com/suspicious",
  "save_to_history": false
}
```

Response (200)

```json
{
  "url_analysis": {
    "domain": "example.com",
    "features": {
      /* feature vector */
    }
  },
  "combined_assessment": { "risk_score": 78, "risk_level": "high" },
  "scan_id": 124
}
```

3.5 Submit CERT report (example)

Request (POST /api/cert/report) — requires Authorization

```json
{
  "url": "https://bad.example.com",
  "content": "Phishing page screenshots and description",
  "risk_score": 80,
  "classification": "phishing",
  "confidence": 0.9
}
```

Response (200)

```json
{
  "success": true,
  "message": "Submitted",
  "report_id": "CERT-2025-0001",
  "submitted_at": "2025-10-15T12:35:00Z"
}
```

4. Core data models (summary tables)

---

Below are abbreviated model field lists (see `models.py` for full SQLAlchemy definitions).

4.1 users (User)

| field                   | type         | notes                |
| ----------------------- | ------------ | -------------------- |
| id                      | integer (PK) | primary key          |
| email                   | string       | unique               |
| username                | string       | unique               |
| hashed_password         | string       | stored password hash |
| is_active               | boolean      | account enabled      |
| is_admin                | boolean      | admin flag           |
| google_id / facebook_id | string       | optional OAuth ids   |
| created_at / updated_at | datetime     | timestamps           |

4.2 user_scans (UserScan)

| field            | type         | notes                              |
| ---------------- | ------------ | ---------------------------------- |
| id               | integer (PK) | primary key                        |
| user_id          | integer (FK) | nullable for anonymous scans       |
| scan_type        | string       | e.g., "qr_image", "url"            |
| content          | text         | processed content                  |
| original_content | text         | raw input (image->url or URL text) |
| classification   | string       | classifier label                   |
| risk_score       | numeric      | 0-100 combined score               |
| suspicious_terms | JSON         | extracted suspicious tokens        |
| explanation      | text         | human-readable explanation         |
| created_at       | datetime     | timestamp                          |

5. Environment variables (configuration)

---

- DATABASE_URL — default `sqlite:///./clicksafe.db` (use a production DB in deployment)
- VIRUSTOTAL_API_KEY — optional; enables VirusTotal URL lookups
- MODEL_PATH — path to ML model (default `qr_url_safety_model.pkl`)
- DEBUG — `true`/`false` (controls debug logging)
- UPLOAD_MAX_SIZE — maximum upload size in bytes (default ≈ 10_000_000)
- SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, CERT_RECIPIENT — used by CERT reporter (recommend using env vars, not hard-coded values)

6. How to run locally (Windows, cmd.exe)

---

Backend (clicksafe-api)

```cmd
cd clicksafe-api
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
set MODEL_PATH=qr_url_safety_model.pkl
set DEBUG=true
python main.py
```

Notes:

- Activate the created `venv` before installing or running.
- On Windows, `pyzbar` requires the native `zbar` library. Options:
  - Install a prebuilt wheel (pipwin) or
  - Use WSL or conda where binary packages are easier to install.

Frontend (ClickSafe)

```cmd
cd ClickSafe
npm install
npm run dev
```

7. Testing and OpenAPI

---

- When the backend runs it exposes Swagger UI at `/docs` and `/redoc` and an OpenAPI JSON at `/openapi.json`.
- Use those endpoints to generate a Postman collection or automated tests.
- Recommended quick tests:
  - Smoke: GET `/api/qr/status`
  - Auth: POST `/auth/register` → POST `/auth/login` → use returned token
  - QR scan: upload a known QR image to `/api/qr/scan/image` and verify `combined_assessment`

8. Caveats, limitations and recommended next steps

---

- The provided ML model (`qr_url_safety_model.pkl`) is a small placeholder. Re-train with production data before relying on scores.
- Some SMTP and CERT destination settings are hard-coded in service files — migrate them to environment variables for security and configuration management.
- The `/api/qr/scan/{scan_id}` detail endpoint may return 404 if not fully implemented; rely on history listing for scan access.

## Next steps I can implement for you

- Expand every endpoint with full request/response schema examples (I can synthesize from `schemas.py`).
- Generate a Postman collection from running OpenAPI JSON (requires starting the server).
- Replace hard-coded SMTP configuration with secure env-var based configuration and add a `.env.example`.

## Contact / last update

This document was prepared for academic submission and last updated: 2025-10-15.

9. Detailed data model tables (from `clicksafe-api/models.py`)

---

Below are explicit field-by-field tables derived from `models.py`. Use these in your appendix or database schema section.

9.1 `users` table

| Column          | Type          | Nullable | Notes                    |
| --------------- | ------------- | :------: | ------------------------ |
| id              | Integer (PK)  |    No    | Primary key, indexed     |
| email           | String(255)   |    No    | Unique, indexed          |
| username        | String(100)   |    No    | Unique, indexed          |
| full_name       | String(255)   |    No    |                          |
| hashed_password | String(255)   |   Yes    | Nullable for OAuth users |
| is_active       | Boolean       |    No    | Default True             |
| is_admin        | Boolean       |    No    | Default False            |
| profile_picture | String(500)   |   Yes    | URL/path to image        |
| phone           | String(20)    |   Yes    | Optional                 |
| location        | String(255)   |   Yes    | Optional                 |
| bio             | Text          |   Yes    | Optional                 |
| website         | String(500)   |   Yes    | Optional                 |
| google_id       | String(100)   |   Yes    | Unique, OAuth            |
| facebook_id     | String(100)   |   Yes    | Unique, OAuth            |
| oauth_provider  | String(50)    |   Yes    | e.g., 'google'           |
| created_at      | DateTime (tz) |    No    | server_default=now()     |
| updated_at      | DateTime (tz) |   Yes    | onupdate=now()           |
| last_login      | DateTime (tz) |   Yes    | Optional                 |

9.2 `user_scans` table

| Column           | Type                  | Nullable | Notes                              |
| ---------------- | --------------------- | :------: | ---------------------------------- |
| id               | Integer (PK)          |    No    | Primary key, indexed               |
| user_id          | Integer (FK→users.id) |    No    | Foreign key to users               |
| scan_type        | String(50)            |    No    | e.g., 'message','url','qr_code'    |
| content          | Text                  |    No    | Processed content                  |
| original_content | Text                  |   Yes    | Raw input (if applicable)          |
| classification   | String(50)            |    No    | 'safe','suspicious','dangerous'    |
| risk_score       | Float                 |    No    | Combined risk score (numeric)      |
| language         | String(50)            |    No    | ISO or label for detected language |
| suspicious_terms | JSON                  |   Yes    | Extracted tokens/terms             |
| explanation      | Text                  |   Yes    | Human-readable explanation         |
| ip_address       | String(45)            |   Yes    | IPv4/IPv6 (optional)               |
| user_agent       | String(500)           |   Yes    | Browser UA (optional)              |
| created_at       | DateTime (tz)         |    No    | server_default=now()               |

9.3 `user_activities` table

| Column        | Type                  | Nullable | Notes                |
| ------------- | --------------------- | :------: | -------------------- |
| id            | Integer (PK)          |    No    | Primary key, indexed |
| user_id       | Integer (FK→users.id) |    No    |                      |
| activity_type | String(100)           |    No    | e.g., 'login','scan' |
| description   | Text                  |   Yes    | Optional             |
| details       | JSON                  |   Yes    | Extra data           |
| ip_address    | String(45)            |   Yes    | Optional             |
| user_agent    | String(500)           |   Yes    | Optional             |
| created_at    | DateTime (tz)         |    No    | server_default=now() |

9.4 `admin_logs` table

| Column         | Type                  | Nullable | Notes                       |
| -------------- | --------------------- | :------: | --------------------------- |
| id             | Integer (PK)          |    No    | Primary key, indexed        |
| admin_user_id  | Integer (FK→users.id) |    No    | Admin that performed action |
| action         | String(100)           |    No    | e.g., 'delete_user'         |
| target_user_id | Integer (FK→users.id) |   Yes    | Affected user               |
| description    | Text                  |   Yes    | Optional                    |
| details        | JSON                  |   Yes    | Optional structured data    |
| ip_address     | String(45)            |   Yes    | Optional                    |
| created_at     | DateTime (tz)         |    No    | server_default=now()        |

9.5 `recent_scams` table

| Column             | Type          | Nullable | Notes                |
| ------------------ | ------------- | :------: | -------------------- |
| id                 | Integer (PK)  |    No    | Primary key, indexed |
| anonymized_content | Text          |    No    | PII removed          |
| original_language  | String(50)    |    No    |                      |
| risk_score         | Float         |    No    | Numeric score        |
| classification     | String(50)    |    No    |                      |
| scam_type          | String(100)   |   Yes    | e.g., 'phishing'     |
| suspicious_terms   | JSON          |   Yes    | Extracted terms      |
| scan_count         | Integer       |    No    | Default 1            |
| is_verified        | Boolean       |    No    | Default False        |
| is_public          | Boolean       |    No    | Default True         |
| created_at         | DateTime (tz) |    No    | server_default=now() |
| updated_at         | DateTime (tz) |   Yes    | onupdate=now()       |

9.6 `password_reset_tokens` table

| Column     | Type                  | Nullable | Notes                |
| ---------- | --------------------- | :------: | -------------------- |
| id         | Integer (PK)          |    No    | Primary key, indexed |
| user_id    | Integer (FK→users.id) |    No    |                      |
| token      | String(255)           |    No    | Unique token         |
| is_used    | Boolean               |    No    | Default False        |
| expires_at | DateTime (tz)         |    No    | Expiry timestamp     |
| created_at | DateTime (tz)         |    No    | server_default=now() |

10. Dependencies (exact lists)

---

10.1 Python backend (`clicksafe-api/requirements.txt`)

The backend requires the following Python packages (pinned versions):

```
fastapi==0.104.1
uvicorn==0.24.0
pandas==2.1.3
numpy==1.24.3
scikit-learn==1.3.2
pydantic==2.5.0
python-multipart==0.0.6
sqlalchemy==2.0.23
databases==0.8.0
aiosqlite==0.19.0
alembic==1.12.1
passlib==1.7.4
python-jose==3.3.0
bcrypt==4.1.2
httpx==0.25.2
email-validator==2.1.0
aiosmtplib==3.0.1
```

10.2 Frontend (`ClickSafe/package.json`)

Key frontend dependencies (from package.json):

```
react ^19.1.1
react-dom ^19.1.1
vite ^7.1.2
qr-scanner ^1.4.2
jsqr ^1.4.0
tailwindcss ^4.1.13
@react-oauth/google ^0.12.2
```

11. Developer appendix — reproduction & troubleshooting tips

---

These are practical notes to help examiners or graders reproduce results locally and avoid common problems.

11.1 Python environment and venv

- Create and activate a venv in `clicksafe-api` and use the same Python executable for installs and running.

Windows (cmd.exe):

```cmd
cd clicksafe-api
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

11.2 `python-jose` import conflict (Anaconda / local file)

- If you see an ImportError referencing a local `jose.py` or an unexpected module, uninstall conflicting packages and reinstall `python-jose[cryptography]` in the venv:

```cmd
pip uninstall jose
pip install "python-jose[cryptography]"
```

11.3 `pyzbar` / `zbar` on Windows

- `pyzbar` relies on the native `zbar` library. On Windows options include:

  - Use pipwin to install prebuilt wheels: `pip install pipwin && pipwin install pyzbar`
  - Install via conda (easier binary compatibility): `conda install -c conda-forge pyzbar`
  - Use WSL and install zbar via the Linux package manager.

    11.4 Model file

- `qr_url_safety_model.pkl` is a pickle artifact. If model loading fails due to scikit-learn version differences, either re-train via `create_qr_model.py` or use the same scikit-learn version listed in `requirements.txt`.

  11.5 OpenAPI & Postman

- With the backend running, visit `http://localhost:8000/docs` to view the Swagger UI or download `openapi.json` from `/openapi.json`. Use that to generate a Postman collection.
