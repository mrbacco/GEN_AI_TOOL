# -*- coding: utf-8 -*-
"""
Spyder Editor

GEN_AI_TOOL project
mrbacco04@gmail.com
Feb 20, 2026

"""

from contextlib import asynccontextmanager
from typing import List, Dict

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy import select

from app.database import engine, SessionLocal, Base
from app.models import ChatMessage

from app.llm import stream_chat
from app.file_parser import parse_file


# =====================
# INIT
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:

        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(lifespan=lifespan)


# =====================
# STATIC
# =====================

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def home():

    return FileResponse("static/index.html")


# =====================
# MEMORY
# =====================

async def save_message(role: str, content: str):

    async with SessionLocal() as session:

        session.add(ChatMessage(role=role, content=content))

        await session.commit()


async def get_memory():

    async with SessionLocal() as session:

        result = await session.execute(
            select(ChatMessage).order_by(ChatMessage.id)
        )

        rows = result.scalars().all()

        messages = []

        for r in rows:

            messages.append({
                "role": str(r.role),
                "content": str(r.content)
            })

        return messages


# =====================
# CHAT ENDPOINT
# =====================

@app.post("/chat")
async def chat(request: Request):

    data = await request.json()

    user_message = data.get("message", "")

    model = data.get("model", "mistral")


    await save_message("user", user_message)

    messages = await get_memory()


    async def generate():

        full = ""

        async for token in stream_chat(model, messages):

            full += token

            yield token

        await save_message("assistant", full)


    return StreamingResponse(generate(), media_type="text/plain")


# =====================
# UPLOAD
# =====================

@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    text = await parse_file(file)

    await save_message("system", text)

    return {"status": "ok"}