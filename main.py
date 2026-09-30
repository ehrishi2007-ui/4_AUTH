import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase import create_client, Client
from supabase_auth.errors import AuthApiError
from supabase_auth.types import User

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
PORT = int(os.getenv("PORT", 8000))

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class AuthCredentials(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server running and connected to Supabase")
    yield


app = FastAPI(
    title="Auth API with Supabase",
    description="Authentication and protected routes API using Supabase Auth",
    version="1.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request payload or missing required fields"},
    )


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail if isinstance(exc.detail, str) else "Request error"},
    )


async def get_current_user(request: Request) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail={"error": "Access token required"}
        )

    token = auth_header[7:].strip()
    if not token:
        raise HTTPException(
            status_code=401, detail={"error": "Access token required"}
        )

    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=401, detail={"error": "Invalid or expired token"}
            )
        return user_response.user
    except HTTPException:
        raise
    except (AuthApiError, Exception):
        raise HTTPException(
            status_code=401, detail={"error": "Invalid or expired token"}
        )


@app.get("/", summary="Root", description="Root endpoint")
async def root():
    return {"message": "Server running and connected to Supabase"}


@app.post(
    "/auth/signup",
    status_code=201,
    summary="Sign Up",
    description="Create a new user account with email and password",
)
async def signup(credentials: AuthCredentials):
    if (
        not credentials.email
        or not credentials.password
        or not credentials.email.strip()
        or not credentials.password.strip()
    ):
        return JSONResponse(
            status_code=400, content={"error": "Email and password are required"}
        )

    try:
        response = supabase.auth.sign_up(
            {"email": credentials.email.strip(), "password": credentials.password}
        )
        user_data = (
            response.user.model_dump(mode="json")
            if response.user
            else {"id": None, "email": credentials.email}
        )
        return JSONResponse(status_code=201, content=user_data)
    except AuthApiError as e:
        return JSONResponse(status_code=400, content={"error": str(e.message)})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.post(
    "/auth/login",
    status_code=200,
    summary="Log In",
    description="Authenticate user with email and password and return access token",
)
async def login(credentials: AuthCredentials):
    if (
        not credentials.email
        or not credentials.password
        or not credentials.email.strip()
        or not credentials.password.strip()
    ):
        return JSONResponse(
            status_code=400, content={"error": "Email and password are required"}
        )

    try:
        response = supabase.auth.sign_in_with_password(
            {"email": credentials.email.strip(), "password": credentials.password}
        )
        if not response.session:
            return JSONResponse(
                status_code=401, content={"error": "Invalid login credentials"}
            )

        return JSONResponse(
            status_code=200,
            content={
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "token_type": "bearer",
                "user": (
                    response.user.model_dump(mode="json")
                    if response.user
                    else None
                ),
            },
        )
    except AuthApiError:
        return JSONResponse(
            status_code=401, content={"error": "Invalid login credentials"}
        )
    except Exception:
        return JSONResponse(status_code=401, content={"error": "Invalid login credentials"})


@app.post(
    "/auth/logout",
    status_code=204,
    summary="Log Out",
    description="End current user session",
)
async def logout(current_user: User = Depends(get_current_user)):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    return Response(status_code=204)


@app.get(
    "/public/info",
    status_code=200,
    summary="Public Info",
    description="Public information endpoint accessible by anyone",
)
async def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get(
    "/protected/profile",
    summary="Protected User Profile",
    description="Protected profile endpoint verifying token via auth middleware",
)
async def get_profile(current_user: User = Depends(get_current_user)):
    created_at_str = (
        current_user.created_at.isoformat()
        if hasattr(current_user.created_at, "isoformat")
        else str(current_user.created_at)
    )
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": created_at_str,
    }


@app.get(
    "/protected/dashboard",
    summary="Protected Dashboard",
    description="Protected dashboard endpoint reusing auth middleware",
)
async def get_dashboard(current_user: User = Depends(get_current_user)):
    return {
        "message": f"Welcome to your dashboard, {current_user.email}!",
        "user_id": current_user.id,
        "audits": [
            {"id": 1, "target": "https://example.com", "score": 94},
            {"id": 2, "target": "https://flyrank.io", "score": 98},
        ],
    }
