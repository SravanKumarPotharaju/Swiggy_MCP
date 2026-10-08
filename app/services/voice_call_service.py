from twilio.rest import Client
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger


class VoiceCallService:
    def __init__(self):
        self.client: Optional[Client] = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def make_automated_call(
        self,
        to_phone: Optional[str] = None,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Triggers an automated phone call to the customer using Twilio Voice.
        The AI speaks the message when the customer answers the phone.
        """
        target_phone = to_phone or settings.USER_PHONE_NUMBER
        if not target_phone.startswith("+"):
            target_phone = f"+{target_phone}"

        caller_id = (settings.TWILIO_PHONE_NUMBER or settings.TWILIO_WHATSAPP_NUMBER or "").replace("whatsapp:", "")

        call_message = message or (
            "Hello! This is SmartFlow, your AI food concierge. "
            "Your delivery partner has arrived at your building gate with your order. "
            "Please collect your food. Enjoy your meal!"
        )

        twiml_speech = f"""<Response>
            <Say voice="alice" language="en-IN">{call_message}</Say>
        </Response>"""

        if not self.client:
            logger.warning("Twilio client is not initialized.")
            return {"success": False, "message": "Twilio credentials not configured"}

        logger.info(f"Initiating Twilio Voice call to {target_phone} from {caller_id}")
        try:
            call = self.client.calls.create(
                to=target_phone,
                from_=caller_id,
                twiml=twiml_speech,
            )
            logger.info(f"Call initiated successfully. Call SID: {call.sid}")
            return {
                "success": True,
                "call_sid": call.sid,
                "status": call.status,
                "to": target_phone,
                "message": "Automated phone call initiated successfully to customer phone.",
            }
        except Exception as e:
            logger.warning(f"Twilio voice call error: {e}")
            return {
                "success": False,
                "message": f"Twilio Voice Call to {target_phone} failed: {e}",
                "error": str(e),
                "to": target_phone,
            }



voice_call_service = VoiceCallService()
