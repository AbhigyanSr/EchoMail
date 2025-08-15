from flask import Flask, request, jsonify
import smtplib
import csv
import os
import boto3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from contextlib import contextmanager
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = '/tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'csv'}

# SMTP configuration mapping
SMTP_CONFIG = {
    'gmail.com': {'host': 'smtp.gmail.com', 'port': 587},
    'outlook.com': {'host': 'smtp-mail.outlook.com', 'port': 587},
    'hotmail.com': {'host': 'smtp-mail.outlook.com', 'port': 587},
    'live.com': {'host': 'smtp-mail.outlook.com', 'port': 587}
}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_smtp_config(email):
    """Get SMTP configuration based on email domain."""
    domain = email.split('@')[1].lower()
    return SMTP_CONFIG.get(domain)

@contextmanager
def smtp_connection(sender_email, sender_password):
    """Context manager for SMTP connection to ensure proper cleanup."""
    smtp_config = get_smtp_config(sender_email)
    if not smtp_config:
        raise ValueError(f"Unsupported email provider for {sender_email}")
    
    smtp = None
    try:
        smtp = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
        smtp.ehlo()
        smtp.starttls()
        smtp.login(sender_email, sender_password)
        yield smtp
    except Exception as e:
        logger.error(f"SMTP connection error: {e}")
        raise
    finally:
        if smtp:
            smtp.quit()

def create_email_message(sender_email, recipient_email, subject, body):
    """Create a properly formatted email message."""
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    return msg

def validate_email(email):
    """Basic email validation."""
    return '@' in email and '.' in email.split('@')[1]

@app.route('/send-emails', methods=['POST'])
def send_emails():
    """Send emails to recipients listed in a CSV file from S3."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        required_fields = ['bucket', 'key', 'filename', 'sender_email', 'sender_password', 'subject', 'body']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Extract data from the request
        bucket = data['bucket']
        key = data['key']
        filename = data['filename']
        sender_email = data['sender_email']
        sender_password = data['sender_password']
        subject = data['subject']
        body = data['body']
        
        # Validate sender email
        if not validate_email(sender_email):
            return jsonify({'error': 'Invalid sender email format'}), 400
        
        # Check if email provider is supported
        if not get_smtp_config(sender_email):
            return jsonify({'error': 'Unsupported email provider'}), 400
        
        if not allowed_file(filename):
            return jsonify({'error': 'Invalid file type. Only CSV files are allowed'}), 400
        
        # Download the file from S3
        s3 = boto3.client('s3')
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            s3.download_file(bucket, key, file_path)
        except Exception as e:
            logger.error(f"S3 download error: {e}")
            return jsonify({'error': 'Failed to download file from S3'}), 500
        
        # Read recipients from CSV
        recipients = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row_num, row in enumerate(reader, 1):
                    if len(row) >= 2:  # Ensure row has at least 2 columns
                        recipient_email = row[1].strip()
                        if validate_email(recipient_email):
                            recipients.append(recipient_email)
                        else:
                            logger.warning(f"Invalid email at row {row_num}: {recipient_email}")
        except Exception as e:
            logger.error(f"CSV reading error: {e}")
            return jsonify({'error': 'Failed to read CSV file'}), 500
        finally:
            # Clean up downloaded file
            if os.path.exists(file_path):
                os.remove(file_path)
        
        if not recipients:
            return jsonify({'error': 'No valid email addresses found in CSV'}), 400
        
        # Send emails using a single SMTP connection
        sent_count = 0
        failed_emails = []
        
        try:
            with smtp_connection(sender_email, sender_password) as smtp:
                for recipient_email in recipients:
                    try:
                        msg = create_email_message(sender_email, recipient_email, subject, body)
                        smtp.send_message(msg)
                        sent_count += 1
                        logger.info(f'Email sent to {recipient_email}')
                    except Exception as e:
                        logger.error(f'Error sending email to {recipient_email}: {e}')
                        failed_emails.append(recipient_email)
        except Exception as e:
            logger.error(f"SMTP connection failed: {e}")
            return jsonify({'error': 'Failed to establish email connection'}), 500
        
        response_data = {
            'message': f'Email sending completed. {sent_count} emails sent successfully.',
            'sent_count': sent_count,
            'total_recipients': len(recipients)
        }
        
        if failed_emails:
            response_data['failed_emails'] = failed_emails
            response_data['failed_count'] = len(failed_emails)
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)