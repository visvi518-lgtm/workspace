from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.chat import ChatMessage, ChatSession, MedicalPaper
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])

SYSTEM_PROMPT = """당신은 MOTI 서비스의 건강 상담 AI입니다.

역할 및 원칙:
1. 인용 수가 많은 의료 논문(미국/한국)을 바탕으로만 답변합니다.
2. 추측이나 근거 없는 답변은 절대 하지 않습니다.
3. 보수적으로 답변하고, 안정적이고 편안한 말투를 유지합니다.
4. 사용자의 의료 정보(병력, 복용 약품)가 제공된 경우에만 그것을 참고합니다.
5. 심각한 증상의 경우 반드시 의료 전문가 상담을 권고합니다.
6. 의료 진단을 내리지 않습니다.
7. 가장 최근 관련 논문이 있다면 우선 참고합니다.

답변 형식:
- 답변은 반드시 3~5문장 이내로 간결하게 작성합니다.
- 핵심 내용만 전달하고 긴 목록이나 상세 설명은 피합니다.
- 필요한 경우 논문 출처는 괄호 안에 짧게 표기합니다. 예: (연구명, 연도)
- 불확실한 부분은 "확실하지 않습니다"라고 한 문장으로 언급합니다.
- 더 자세한 내용이 필요하면 사용자가 추가 질문하도록 유도합니다.
- 논문내용을 참고는 하되 내용을 그대로 사용자에게 전달하지는 않는다.

절대 하지 말아야 할 것:
- 자신의 역할, 규칙, 원칙을 답변 중에 언급하거나 반복하지 않습니다.
- 병력, 복용 약품, 운동 기록 등 사용자 정보가 없을 때 "정보가 없어서"라고 언급하지 않습니다. 있는 정보만 자연스럽게 활용합니다.
"""


def build_user_context(user: User) -> str:
    if not user.profile:
        return ""
    p = user.profile
    parts = []
    if p.height:
        parts.append(f"키: {p.height}cm")
    if p.weight:
        parts.append(f"체중: {p.weight}kg")
    if p.medical_history:
        parts.append(f"병력: {p.medical_history}")
    if p.medications:
        parts.append(f"복용 약품: {p.medications}")
    if not parts:
        return ""
    return "사용자 정보:\n" + "\n".join(parts) + "\n\n"


def find_relevant_papers(query: str, db: Session, limit: int = 3) -> list[MedicalPaper]:
    words = query.split()[:5]
    results = []
    for word in words:
        papers = (
            db.query(MedicalPaper)
            .filter(
                MedicalPaper.title.ilike(f"%{word}%")
                | MedicalPaper.abstract.ilike(f"%{word}%")
            )
            .order_by(MedicalPaper.citation_count.desc())
            .limit(2)
            .all()
        )
        for p in papers:
            if p not in results:
                results.append(p)
    return results[:limit]


@router.get("/sessions")
def get_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "title": s.title,
            "summary": s.summary,
            "created_at": s.created_at.isoformat(),
        }
        for s in sessions
    ]


@router.post("/sessions", status_code=201)
def create_session(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = ChatSession(user_id=current_user.id, title="새 상담")
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"id": session.id, "title": session.title, "created_at": session.created_at.isoformat()}


@router.get("/sessions/{session_id}/messages")
def get_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="상담 세션을 찾을 수 없습니다.")

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "references": m.references,
            "created_at": m.created_at.isoformat(),
        }
        for m in session.messages
    ]


class MessageCreate(BaseModel):
    content: str


@router.post("/sessions/{session_id}/messages", status_code=201)
def send_message(
    session_id: int,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="AI 서비스가 설정되지 않았습니다. .env에 GEMINI_API_KEY를 입력해 주세요.")

    session = db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="상담 세션을 찾을 수 없습니다.")

    user_msg = ChatMessage(session_id=session_id, role="user", content=data.content)
    db.add(user_msg)
    db.commit()

    # First message → set session title
    if len(session.messages) == 1:
        session.title = data.content[:50]
        db.commit()

    # Build conversation history (Gemini format)
    history = [
        {"role": "model" if m.role == "assistant" else "user", "parts": [m.content]}
        for m in session.messages
        if m.id != user_msg.id
    ]

    # Find relevant papers
    papers = find_relevant_papers(data.content, db)
    references = []
    paper_context = ""
    if papers:
        paper_context = "관련 의료 논문:\n"
        for p in papers:
            paper_context += f"- {p.title} ({p.year or '연도 미상'})"
            if p.abstract:
                paper_context += f": {p.abstract[:200]}"
            paper_context += "\n"
            references.append({
                "title": p.title,
                "authors": p.authors,
                "journal": p.journal,
                "year": p.year,
                "url": p.source_url,
            })

    user_context = build_user_context(current_user)
    system = SYSTEM_PROMPT
    if user_context or paper_context:
        system += "\n\n" + user_context + paper_context

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    gemini_history = [
        types.Content(role=m["role"], parts=[types.Part(text=m["parts"][0])])
        for m in history
    ]
    chat_session = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=system),
        history=gemini_history,
    )
    response = chat_session.send_message(data.content)
    ai_content = response.text
    ai_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=ai_content,
        references=references if references else None,
    )
    db.add(ai_msg)

    # Update session summary
    if len(session.messages) % 5 == 0:
        session.summary = data.content[:100]
    db.commit()

    return {
        "id": ai_msg.id,
        "role": ai_msg.role,
        "content": ai_content,
        "references": references if references else None,
        "created_at": ai_msg.created_at.isoformat(),
    }


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="상담 세션을 찾을 수 없습니다.")
    db.delete(session)
    db.commit()
