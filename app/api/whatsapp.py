import httpx
from typing import Optional
from fastapi import APIRouter, Request, Form, Response
from app.core.config import settings
from app.core.logging import logger
from app.services.llm_agent import llm_agent
from app.services.whatsapp_service import whatsapp_service

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: Optional[str] = Form(None),
    NumMedia: Optional[int] = Form(0),
    MediaUrl0: Optional[str] = Form(None),
    MediaContentType0: Optional[str] = Form(None),
):
    """
    Inbound webhook for Twilio WhatsApp messages (Text + Voice Notes).
    """
    user_phone = From.replace("whatsapp:", "").strip()
    logger.info(f"Incoming WhatsApp from {user_phone} | Text: '{Body}' | NumMedia: {NumMedia}")

    audio_bytes = None
    audio_mime = "audio/ogg"

    # Handle voice note / audio message
    if NumMedia and NumMedia > 0 and MediaUrl0:
        logger.info(f"Downloading media from Twilio: {MediaUrl0} ({MediaContentType0})")
        try:
            # Twilio media requires HTTP Basic Auth with Account SID & Auth Token
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    MediaUrl0,
                    auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                    follow_redirects=True,
                )
                if res.status_code == 200:
                    audio_bytes = res.content
                    audio_mime = MediaContentType0 or "audio/ogg"
                    logger.info(f"Downloaded {len(audio_bytes)} bytes of audio.")
                else:
                    logger.error(f"Failed to download audio from Twilio: status {res.status_code}")
        except Exception as e:
            logger.error(f"Error downloading media attachment: {e}")

    # Process through Gemini AI Agent
    reply_text = await llm_agent.process_user_message(
        user_phone=user_phone,
        text_message=Body,
        audio_bytes=audio_bytes,
        audio_mime_type=audio_mime,
    )

    # Check if there is an active QR image generated for UPI payment
    media_url = None
    # If the reply mentions order placed with UPI QR, attach QR image
    if "Order ID:" in reply_text and "UPI QR" in reply_text:
        # Check if we have public ngrok URL or serve locally
        host = request.headers.get("host", "localhost:8000")
        proto = request.headers.get("x-forwarded-proto", "https")
        # Extract order ID if possible
        import re
        m = re.search(r"Order ID: `([^`]+)`", reply_text)
        if m:
            order_id = m.group(1)
            media_url = f"{proto}://{host}/static/qr/order_{order_id}.png"

    # Return TwiML XML
    twiml_xml = whatsapp_service.create_twiml_reply(reply_text, media_url=media_url)
    return Response(content=twiml_xml, media_type="application/xml")
