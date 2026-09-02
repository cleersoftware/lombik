import resend
import threading
from dotenv import load_dotenv
from typing import Dict, Optional, Any, Union
import requests
import os

load_dotenv()

def send_email(
    to: Union[str, list[str]],
    subject: str,
    html: str,
    text: Optional[str] = None,
    from_name: Optional[str] = None,
    callback: Optional[callable] = None,
) -> threading.Thread:
    """
    Send an email using Resend in a background thread.
    
    Args:
        callback: Optional function that receives (success: bool, error: Exception|None)
    
    Returns:
        The thread object (useful for joining or checking if still running)
    """
    
    def _send():
        try:
            api_key = os.getenv("RESEND_API_KEY")
            from_email = os.getenv("MAIL_FROM")

            if not api_key or not from_email:
                raise RuntimeError("RESEND_API_KEY and MAIL_FROM must be set to send email.")

            if isinstance(to, str):
                to_list = [to]
            else:
                to_list = to

            sender = (
                f"{from_name} <{from_email}>"
                if from_name
                else from_email
            )

            payload = {
                "from": sender,
                "to": to_list,
                "subject": subject,
                "html": html,
            }

            if text:
                payload["text"] = text

            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=15,
            )

            success = response.ok
            error = None if success else Exception(f"HTTP {response.status_code}: {response.text}")
            
        except Exception as e:
            success = False
            error = e

        if callback:
            callback(success, error)

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
    return thread