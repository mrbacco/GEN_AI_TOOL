# -*- coding: utf-8 -*-
"""
Spyder Editor

GEN_AI_TOOL project
mrbacco04@gmail.com
Feb 20, 2026

Multi-LLM Router
Supports:
- Ollama
- OpenAI
- Future providers (LM Studio, etc.)

"""


import asyncio
from typing import AsyncGenerator, List, Dict, Any

import ollama
from openai import OpenAI


ollama_client = ollama.Client()

openai_client = OpenAI(
    api_key="YOUR_OPENAI_API_KEY"
)


# =========================
# SAFE WRAPPERS
# =========================

def ollama_chat_stream(
    model: str,
    messages: List[Dict[str, str]],
) -> Any:

    return ollama_client.chat(
        model=model,
        messages=messages,
        stream=True,
    )


def openai_chat_stream(
    model: str,
    messages: List[Dict[str, str]],
) -> Any:

    return openai_client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )


# =========================
# OLLAMA STREAM
# =========================

async def stream_ollama(
    model: str,
    messages: List[Dict[str, str]],
) -> AsyncGenerator[str, None]:

    stream = ollama_chat_stream(model, messages)

    for chunk in stream:

        content = chunk["message"]["content"]

        if content:

            yield content

        await asyncio.sleep(0)


# =========================
# OPENAI STREAM
# =========================

async def stream_openai(
    model: str,
    messages: List[Dict[str, str]],
) -> AsyncGenerator[str, None]:

    stream = openai_chat_stream(model, messages)

    for chunk in stream:

        delta = chunk.choices[0].delta

        if delta.content:

            yield delta.content

        await asyncio.sleep(0)


# =========================
# ROUTER
# =========================

async def stream_chat(
    model: str,
    messages: List[Dict[str, str]],
) -> AsyncGenerator[str, None]:

    if model in ["mistral", "phi3", "llama3"]:

        async for token in stream_ollama(model, messages):

            yield token


    elif model in ["gpt-4o", "gpt-4o-mini"]:

        async for token in stream_openai(model, messages):

            yield token


    else:

        raise ValueError("Unsupported model")