
from lms_agent import chat, driver
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# Ensure the Neo4j driver closes cleanly when Uvicorn shuts down
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    driver.close()


app = FastAPI(title="Adaptive Learning Tutor API", lifespan=lifespan)


# ---------- Request & Response Schemas ----------
class ChatRequest(BaseModel):
    id: str = Field(..., examples=["s1"])
    message: str = Field(..., examples=[
                         "I have difficulty learning Grade 8th Map. Help!"])
    history: list[dict[str, Any]] = Field(default_factory=list, examples=[[]])


class ChatResponse(BaseModel):
    reply: str
    history: list[dict[str, Any]]


# ---------- Endpoints ----------
@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def tutor_chat(req: ChatRequest):
    try:
        reply, updated_messages = chat(
            student_id=req.id,
            user_message=req.message,
            history=req.history,
        )
        # Convert LangChain BaseMessage objects to serializable dicts for JSON response
        # pickling history by serializing
        pickling_history = [
            m.model_dump() if hasattr(m, "model_dump") else m
            for m in updated_messages
        ]
        return ChatResponse(reply=reply, history=pickling_history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
