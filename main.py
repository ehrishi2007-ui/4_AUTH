import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase import create_client, Client
from supabase_auth.errors import AuthApiError

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
    except Exception as e:
        return JSONResponse(status_code=401, content={"error": "Invalid login credentials"})
