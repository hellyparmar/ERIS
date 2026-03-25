from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any
from app.middleware.auth import get_current_user
from app.models.multitenant_models import User

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


class TestEmailRequest(BaseModel):
    to: str
    subject: str = "Test Email from R-DIOS"
    message: str = "It works!"


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Return which services are configured and operational"""
    # Lazy imports to avoid blocking at startup
    try:
        from app.notifications.email_service import email_service
        email_status = "configured" if email_service.is_configured() else "not_configured"
    except Exception:
        email_status = "error"

    try:
        from app.notifications.whatsapp_service import whatsapp_service
        wa_status = "configured" if whatsapp_service.is_configured() else "not_configured"
    except Exception:
        wa_status = "error"

    try:
        from app.ml.assistant.llm_provider import llm
        ai_status = "configured" if llm.is_available() else "not_configured"
        if llm.provider != "none":
            ai_status += f" ({llm.provider})"
    except Exception:
        ai_status = "error"

    try:
        from app.config import settings
        flags = {
            "enable_ai": settings.ENABLE_AI_ASSISTANT,
            "enable_email": settings.ENABLE_EMAIL,
            "enable_whatsapp": settings.ENABLE_WHATSAPP
        }
    except Exception:
        flags = {}

    return {
        "email": email_status,
        "whatsapp": wa_status,
        "ai": ai_status,
        "feature_flags": flags
    }


@router.post("/test-email")
async def test_email(request: TestEmailRequest, current_user: User = Depends(get_current_user)):
    """Send a test email to the specified address"""
    from app.config import settings
    from app.notifications.email_service import email_service

    if not settings.ENABLE_EMAIL:
        raise HTTPException(status_code=400, detail="Email feature is disabled. Set ENABLE_EMAIL=true in .env")

    success = await email_service.send_email(
        to=request.to,
        subject=request.subject,
        body=request.message
    )

    if success:
        return {"status": "success", "message": f"✅ Test email sent to {request.to}"}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send email. Check SMTP_USER and SMTP_PASSWORD in backend/.env"
        )


@router.post("/test-ai")
async def test_ai_endpoint(prompt: str = "Hello, what can you do?", current_user: User = Depends(get_current_user)):
    """Test the AI provider connectivity"""
    from app.config import settings
    from app.ml.assistant.llm_provider import llm

    if not settings.ENABLE_AI_ASSISTANT:
        raise HTTPException(status_code=400, detail="AI Assistant is disabled in config")

    response = await llm.chat([{"role": "user", "content": prompt}])
    return {"status": "success", "provider": llm.provider, "response": response}
