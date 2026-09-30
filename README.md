# Auth API — Login & Protected Routes (Supabase Edition)

A secure authentication and protected routes RESTful API built using **FastAPI** and **Supabase Auth** as the Identity Provider (IdP).

This project implements the modern authentication architecture:
- Offloading user credentials, password hashing, and token issuance to a trusted Identity Provider (**Supabase Auth**).
- Issuing cryptographically signed **JSON Web Tokens (JWTs)** upon successful login.
- Guarding private endpoints using a reusable **FastAPI dependency / auth middleware** that extracts and verifies Bearer access tokens via Supabase.
- Documenting interactive endpoints with **Swagger UI** including the HTTPBearer security scheme and `Authorize` padlock.

---

## The One Command to Run Everything

To start the FastAPI server on localhost:

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at:
```
http://localhost:8000
```

Interactive Swagger UI documentation is available at:
```
http://localhost:8000/docs
```

---

## Environment Variables & Configuration

Secrets and project configuration are managed via environment variables and loaded using `python-dotenv`.

> **Security Note:** Secrets like your Supabase keys must never be committed to source control. The `.env` file is excluded from Git tracking via [`.gitignore`](.gitignore). A template [`.env.example`](.env.example) is committed to guide setup with placeholder values.

### Setting up `.env`:

1. Copy the example configuration template:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in your Supabase project credentials:
   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your_supabase_anon_public_key
   PORT=8000
   ```

### Configuration Variables:

| Variable | Description | Safe for Git? |
|---|---|:---:|
| `SUPABASE_URL` | Your Supabase project URL (found in Project Settings → API) | No |
| `SUPABASE_KEY` | Your Supabase `anon` public key (safe for client/backend SDK usage) | No |
| `PORT` | Local server port (default: `8000`) | Yes |

> **Supabase Configuration Tip:** In your Supabase Dashboard under **Authentication → Providers → Email**, turn off **"Confirm email"** for testing so new signups can immediately log in without requiring inbox verification.

---

## API Reference

| Method | Endpoint | Description | Auth Header | Request Body | Success Status | Error Status |
|:---:|---|---|:---:|---|:---:|:---:|
| `GET` | `/` | Root API health status | None | None | `200 OK` | — |
| `POST` | `/auth/signup` | Register a new user | None | `{"email": "string", "password": "string"}` | `201 Created` | `400 Bad Request` |
| `POST` | `/auth/login` | Authenticate user & return JWT tokens | None | `{"email": "string", "password": "string"}` | `200 OK` | `400 Bad Request`, `401 Unauthorized` |
| `POST` | `/auth/logout` | Terminate user session | `Authorization: Bearer <token>` | None | `204 No Content` | `401 Unauthorized` |
| `GET` | `/public/info` | Public open data endpoint | None | None | `200 OK` | — |
| `GET` | `/protected/profile` | Read authenticated user safe metadata | `Authorization: Bearer <token>` | None | `200 OK` | `401 Unauthorized` |
| `GET` | `/protected/dashboard` | Protected dashboard data (middleware reuse) | `Authorization: Bearer <token>` | None | `200 OK` | `401 Unauthorized` |

---

## Error Handling & Status Codes

All errors return a structured JSON response with an informative message:

| Status Code | Reason | JSON Response Format |
|---|---|---|
| `201 Created` | Successful user signup | `{ "id": "...", "email": "..." }` |
| `200 OK` | Successful login or protected resource read | `{ "access_token": "...", ... }` or resource data |
| `204 No Content` | Successful logout | *Empty Body* |
| `400 Bad Request` | Missing/empty email or password, invalid JSON | `{ "error": "Email and password are required" }` |
| `401 Unauthorized` | Missing token or malformed header | `{ "error": "Access token required" }` |
| `401 Unauthorized` | Invalid credentials upon login | `{ "error": "Invalid login credentials" }` |
| `401 Unauthorized` | Tampered, invalid, or expired JWT | `{ "error": "Invalid or expired token" }` |

---

## Testing via `curl -i` (Step-by-Step Flow)

### 1. Sign Up a New User
```bash
curl -i -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@example.com","password":"securepassword123"}'
```
*Response:* `201 Created` with user details.

### 2. Log In & Receive JWT Access Token
```bash
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@example.com","password":"securepassword123"}'
```
*Response:* `200 OK` containing `access_token` and `refresh_token`.

### 3. Access Public Route (No Token Required)
```bash
curl -i http://localhost:8000/public/info
```
*Response:* `200 OK` with `{"message": "Welcome stranger! This info is public."}`.

### 4. Access Protected Route (Valid Token)
```bash
curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer <PASTE_YOUR_ACCESS_TOKEN_HERE>"
```
*Response:* `200 OK` returning safe metadata (`id`, `email`, `created_at`).

### 5. Attempt Access with a Tampered/Bad Token
Change a single character of the token and run again:
```bash
curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer invalid_or_tampered_token_string"
```
*Response:* `401 Unauthorized` with `{"error": "Invalid or expired token"}`.

### 6. Verify Auth Middleware Reuse on Dashboard
```bash
curl -i http://localhost:8000/protected/dashboard \
  -H "Authorization: Bearer <PASTE_YOUR_ACCESS_TOKEN_HERE>"
```
*Response:* `200 OK` with authenticated dashboard payload.

### 7. Log Out
```bash
curl -i -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer <PASTE_YOUR_ACCESS_TOKEN_HERE>"
```
*Response:* `204 No Content`.

---

## Interactive Documentation (Swagger UI)

FastAPI automatically generates OpenAPI documentation at `http://localhost:8000/docs`.

With the `HTTPBearer` security scheme configured:
1. Click the **Authorize** button (padlock icon) at the top right of the Swagger UI page.
2. Enter your JWT `access_token` received from `/auth/login`.
3. Test protected endpoints directly from your browser with **Try it out**.

![Swagger UI](images/swagger-ui.png)

---

## Quickstart for Strangers (Round-Trip Test)

To clone and run this project on any machine:

```bash
git clone https://github.com/ehrishi2007-ui/4_AUTH.git
cd 4_AUTH
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Supabase credentials
uvicorn main:app --reload --port 8000
```

---

DISCLAIMER : THIS ASSIGNMENT IS A PART OF flyrankAI INTERNSHIP
