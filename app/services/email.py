"""
Email service for Memorial Website.
Handles sending emails for verification, password reset, and notifications.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        self.settings = get_settings()
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """
        Send email asynchronously.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text content (optional)
            from_email: Sender email (optional, uses config default)
            from_name: Sender name (optional, uses config default)
            
        Returns:
            bool: True if email was sent successfully
        """
        if not self.settings.EMAIL_ENABLED:
            logger.info(f"Email disabled - would send: {subject} to {to_email}")
            return True
        
        try:
            # Use configured values or defaults
            from_email = from_email or self.settings.EMAIL_FROM_ADDRESS
            from_name = from_name or self.settings.EMAIL_FROM_NAME
            
            # Run email sending in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.executor,
                self._send_email_sync,
                to_email,
                subject,
                html_content,
                text_content,
                from_email,
                from_name
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _send_email_sync(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
        from_email: str,
        from_name: str
    ) -> bool:
        """
        Send email synchronously using SMTP.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content
            from_email: Sender email
            from_name: Sender name
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = to_email
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Connect to SMTP server and send
            if self.settings.EMAIL_USE_TLS:
                server = smtplib.SMTP(self.settings.EMAIL_HOST, self.settings.EMAIL_PORT)
                server.starttls()
            else:
                server = smtplib.SMTP(self.settings.EMAIL_HOST, self.settings.EMAIL_PORT)
            
            # Login if credentials provided
            if self.settings.EMAIL_USERNAME and self.settings.EMAIL_PASSWORD:
                server.login(self.settings.EMAIL_USERNAME, self.settings.EMAIL_PASSWORD)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP error sending email to {to_email}: {e}")
            return False
    
    async def send_bulk_email(
        self,
        recipients: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> int:
        """
        Send email to multiple recipients.
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text content (optional)
            
        Returns:
            int: Number of emails sent successfully
        """
        sent_count = 0
        
        for recipient in recipients:
            success = await self.send_email(
                to_email=recipient,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                sent_count += 1
            
            # Small delay between emails to avoid overwhelming SMTP server
            await asyncio.sleep(0.1)
        
        logger.info(f"Bulk email sent: {sent_count}/{len(recipients)} successful")
        return sent_count
    
    async def test_connection(self) -> bool:
        """
        Test email server connection.
        
        Returns:
            bool: True if connection successful
        """
        if not self.settings.EMAIL_ENABLED:
            logger.info("Email service disabled")
            return False
        
        try:
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.executor,
                self._test_connection_sync
            )
            return success
            
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False
    
    def _test_connection_sync(self) -> bool:
        """
        Test SMTP connection synchronously.
        
        Returns:
            bool: True if connection successful
        """
        try:
            if self.settings.EMAIL_USE_TLS:
                server = smtplib.SMTP(self.settings.EMAIL_HOST, self.settings.EMAIL_PORT)
                server.starttls()
            else:
                server = smtplib.SMTP(self.settings.EMAIL_HOST, self.settings.EMAIL_PORT)
            
            if self.settings.EMAIL_USERNAME and self.settings.EMAIL_PASSWORD:
                server.login(self.settings.EMAIL_USERNAME, self.settings.EMAIL_PASSWORD)
            
            server.quit()
            logger.info("Email connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False

def get_email_service() -> EmailService:
    """Get email service instance."""
    return EmailService()
