import logging

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send_login_alert(email: str, ip_address: str):
        """
        Send a security alert email.
        For this assessment, we just log it to the console.
        """
        # In a real app, SendGrid or SMTP would be used here.
        logger.warning(
            f"SECURITY ALERT: New login for {email} from unknown IP: {ip_address}"
        )
        print(f"--> [EMAIL SENT] to {email}: Unrecognized login from {ip_address}")
