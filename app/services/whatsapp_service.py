import os
import qrcode
from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from app.core.config import settings
from app.core.logging import logger


class WhatsAppService:
    def __init__(self):
        self.qr_dir = "/Users/auto/Desktop/SmartFlow/static/qr"
        os.makedirs(self.qr_dir, exist_ok=True)
        self.client: Optional[Client] = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def generate_qr_code(self, data: str, name: str = "order_qr") -> str:
        """Generates a QR code image file from data string (e.g. UPI Intent / QR payload)."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        filepath = os.path.join(self.qr_dir, f"{name}.png")
        img.save(filepath)
        logger.info(f"Saved UPI QR image to {filepath}")
        return filepath

    def create_twiml_reply(self, message_text: str, media_url: Optional[str] = None) -> str:
        """Builds a Twilio MessagingResponse XML string."""
        response = MessagingResponse()
        msg = response.message()
        msg.body(message_text)
        if media_url:
            msg.media(media_url)
        return str(response)

    def send_whatsapp_message(
        self,
        message_text: str,
        to_phone: Optional[str] = None,
        media_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sends an outbound proactive WhatsApp notification to the user via Twilio.
        """
        if not self.client:
            return {"success": False, "error": "Twilio client not initialized"}

        target_phone = to_phone or settings.USER_PHONE_NUMBER
        if not target_phone.startswith("whatsapp:"):
            target_phone = f"whatsapp:{target_phone}"
        from_phone = settings.TWILIO_WHATSAPP_NUMBER
        if not from_phone.startswith("whatsapp:"):
            from_phone = f"whatsapp:{from_phone}"

        logger.info(f"Sending WhatsApp notification to {target_phone} from {from_phone}")
        try:
            kwargs = {
                "from_": from_phone,
                "to": target_phone,
                "body": message_text,
            }
            if media_url:
                kwargs["media_url"] = [media_url]

            msg = self.client.messages.create(**kwargs)
            logger.info(f"WhatsApp sent successfully. SID: {msg.sid}, Status: {msg.status}")
            return {"success": True, "sid": msg.sid, "status": msg.status}
        except Exception as e:
            logger.warning(f"Twilio WhatsApp notification note: {e}")
            return {
                "success": False,
                "error": str(e),
                "note": "Outbound WhatsApp requires the user to join the Twilio sandbox or an approved ContentSid template.",
            }


whatsapp_service = WhatsAppService()

