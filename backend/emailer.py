import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Dict
from backend.logger import get_logger
from models import EmailConfig

# I'm importing the logger so can use it throughout this file.
logger = get_logger()

class EmailSender:
    def __init__(self, config: EmailConfig):
        self.config = config
    
    def send_email_with_certificate(self, student_data: Dict, certificate_path: str) -> bool:
        """Send email with certificate attachment to a single student."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.sender_email
            msg['To'] = student_data['email']
            msg['Subject'] = self.config.subject
            
            # Check for required keys before formatting email body
            required_keys = ['name', 'email', 'branch', 'year_of_study']
            missing_keys = [k for k in required_keys if k not in student_data]
            if missing_keys:
                logger.error(f"Student record missing keys: {missing_keys}. Data: {student_data}")
                return False
            # Email body
            body = self.config.body_template.format(
                name=student_data.get('name', 'N/A'),
                branch=student_data.get('branch', 'N/A'),
                year=student_data.get('year_of_study', 'N/A')
            )
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach certificate
            if os.path.exists(certificate_path):
                with open(certificate_path, 'rb') as attachment:
                    part = MIMEApplication(attachment.read(), _subtype='pdf')
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename=certificate_{student_data["name"]}.pdf'
                    )
                    msg.attach(part)
            else:
                logger.error(f"Certificate file not found: {certificate_path}")
                return False
            
            # Send email
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.sender_email, self.config.sender_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {student_data['email']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {student_data['email']}: {e}")
            return False
    
    def send_bulk_emails(self, students: List[Dict], certificate_paths: List[str]) -> Dict:
        """Send emails to all students with their respective certificates."""
        results = {
            'successful': [],
            'failed': [],
            'total': len(students),
            'success_count': 0,
            'failure_count': 0
        }
        
        for i, (student, cert_path) in enumerate(zip(students, certificate_paths)):
            try:
                success = self.send_email_with_certificate(student, cert_path)
                
                if success:
                    results['successful'].append({
                        'name': student['name'],
                        'email': student['email']
                    })
                    results['success_count'] += 1
                else:
                    results['failed'].append({
                        'name': student['name'],
                        'email': student['email'],
                        'error': 'Email sending failed'
                    })
                    results['failure_count'] += 1
                    
            except Exception as e:
                results['failed'].append({
                    'name': student['name'],
                    'email': student['email'],
                    'error': str(e)
                })
                results['failure_count'] += 1
        
        logger.info(f"Email sending completed. Success: {results['success_count']}, Failed: {results['failure_count']}")
        return results
    
    def test_email_connection(self) -> bool:
        """Test email server connection."""
        try:
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.sender_email, self.config.sender_password)
            logger.info("Email connection test successful")
            return True
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False
