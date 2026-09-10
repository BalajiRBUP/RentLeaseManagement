from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chatbot import ChatQuery, ChatResponse
from app.core.chatbot_engine import ask_question, ChatbotError

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])


@router.post("/ask", response_model=ChatResponse)
def ask(payload: ChatQuery, db: Session = Depends(get_db)):
    try:
        result = ask_question(payload.question, db)
    except ChatbotError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result
