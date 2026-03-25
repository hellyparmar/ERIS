from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from app.api.notifications.notification_manager import notification_manager
from app.api.notifications.email_service import email_service
from app.api.notifications.whatsapp_service import whatsapp_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])

class EmailRequest(BaseModel):
    email: EmailStr
    subject: str = "Test Email from R-DIOS"
    message: str = "Welcome! This is a test email."

class WhatsAppRequest(BaseModel):
    phone: str
    message: str = "Test WhatsApp message from R-DIOS."

@router.post("/test-email")
async def test_email(request: EmailRequest):
    """Test standard Gmail SMTP email delivery"""
    result = email_service.send_email(request.email, request.subject, request.message)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return {"status": "success", "message": "Email sent"}

@router.post("/test-whatsapp")
async def test_whatsapp(request: WhatsAppRequest):
    """Test MSG91 WhatsApp delivery"""
    result = whatsapp_service.send_template_message(request.phone, "test_template", [request.message])
    if result.get("skipped"):
        return {"status": "skipped", "message": "WhatsApp not configured"}
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return {"status": "success", "message": "WhatsApp message sent"}

@router.get("/status")
async def get_notification_status():
    """Get status of each notification provider"""
    return {
        "email_enabled": email_service.enabled,
        "whatsapp_enabled": whatsapp_service.enabled
    }
