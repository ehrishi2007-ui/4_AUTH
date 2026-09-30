import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
PORT = int(os.getenv("PORT", 8000))

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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


@app.get("/", summary="Root", description="Root endpoint")
async def root():
    return {"message": "Server running and connected to Supabase"}
