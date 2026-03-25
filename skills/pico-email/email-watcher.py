#!/usr/bin/env python3
"""
picoclaw Email Watcher - Background daemon that monitors email for messages

This script:
1. Connects to IMAP and checks for new messages
2. Generates responses using picoclaw (you'll need to call me)
3. Sends replies via SMTP

Run this as a background service or via cron job/Task Scheduler.
"""

import os
import sys
import time
import imaplib
import smtplib
import subprocess
import json
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import message_from_bytes, policy
from pathlib import Path
from datetime import datetime

# ============================================
# Configuration
# ============================================

# Load from environment or config file
def load_config():
    config = {}

    # Try to load from config.env
    config_path = Path(__file__).parent / "config.env"
    if config_path.exists():
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()

    # Override with environment variables if set
    env_vars = {
        'IMAP_SERVER', 'IMAP_PORT', 'IMAP_USER', 'IMAP_PASS',
        'SMTP_SERVER', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASS',
        'CHECK_INTERVAL',
        'ALLOWED_SENDER', 'RESPONSE_PREFIX'
    }
    for var in env_vars:
        if var in os.environ:
            config[var] = os.environ[var]

    return config

CONFIG = load_config()

# Set default values
IMAP_SERVER = CONFIG.get('IMAP_SERVER', 'imap.gmail.com')
IMAP_PORT = int(CONFIG.get('IMAP_PORT', '993'))
IMAP_USER = CONFIG.get('IMAP_USER', '')
IMAP_PASS = CONFIG.get('IMAP_PASS', '')

SMTP_SERVER = CONFIG.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(CONFIG.get('SMTP_PORT', '587'))
SMTP_USER = CONFIG.get('SMTP_USER', '')
SMTP_PASS = CONFIG.get('SMTP_PASS', '')

CHECK_INTERVAL = int(CONFIG.get('CHECK_INTERVAL', '60'))
ALLOWED_SENDER = CONFIG.get('ALLOWED_SENDER', '')
RESPONSE_PREFIX = CONFIG.get('RESPONSE_PREFIX', 'Re: ')

# State file to track processed emails
STATE_DIR = Path(__file__).parent / "state"
STATE_DIR.mkdir(exist_ok=True)
PROCESSED_FILE = STATE_DIR / "processed_emails.txt"

# ============================================
# State Management
# ============================================

def load_processed_emails():
    """Load list of already processed email IDs"""
    if PROCESSED_FILE.exists():
        with open(PROCESSED_FILE) as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_processed_email(email_id):
    """Mark an email as processed"""
    processed = load_processed_emails()
    processed.add(email_id)
    with open(PROCESSED_FILE, 'w') as f:
        f.write('\n'.join(sorted(processed)))
    # Mark email as seen in IMAP
    try:        
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(IMAP_USER, IMAP_PASS)
        mail.select('INBOX')
        mail.store(email_id, '+FLAGS', '\\Seen')
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"❌ IMAP connection failed: {e}")

# ============================================
# Email Operations
# ============================================

def connect_imap():
    """Connect to IMAP server"""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(IMAP_USER, IMAP_PASS)
        mail.select('INBOX')
        return mail
    except Exception as e:
        print(f"❌ IMAP connection failed: {e}")
        return None

def get_new_emails(mail):
    """Fetch unread emails from inbox"""
    try:
        # Search for unread messages
        status, messages = mail.search(None, '(UNSEEN)')

        if status != 'OK' or not messages[0]:
            return []

        email_ids = messages[0].split()
        emails = []

        for email_id in email_ids:
            # Skip if already processed
            if email_id.decode() in load_processed_emails():
                continue

            # Fetch email
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            if status != 'OK':
                continue

            email_message = message_from_bytes(msg_data[0][1], policy=policy.default)

            # Extract email info
            sender = email_message.get('From', '')
            subject = email_message.get('Subject', '')
            date = email_message.get('Date', '')

            # Extract email address from sender
            sender_match = re.search(r'<(.+?)>', sender)
            sender_email = sender_match.group(1) if sender_match else sender

            # Check if sender is allowed
            if ALLOWED_SENDER and ALLOWED_SENDER not in sender_email:
                print(f"⏭️  Skipping email from {sender_email} (not in allowed list)")
                continue

            # Extract body
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    if content_type == 'text/plain':
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            body = part.get_payload(decode=True).decode(charset, errors='replace')
                        except LookupError:
                            body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        break
            else:
                charset = email_message.get_content_charset() or 'utf-8'
                try:
                    body = email_message.get_payload(decode=True).decode(charset, errors='replace')
                except LookupError:
                    body = email_message.get_payload(decode=True).decode('utf-8', errors='replace')

            emails.append({
                'id': email_id.decode(),
                'sender': sender,
                'sender_email': sender_email,
                'subject': subject,
                'date': date,
                'body': body
            })

        return emails

    except Exception as e:
        print(f"❌ Error fetching emails: {e}")
        return []

def send_email(to_email, subject, body, is_encrypted=False):
    """Send email via SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject

        # Set Content-Type based on encryption
        if is_encrypted:
            # PGP/MIME format
            encrypted_msg = MIMEText(body, 'plain')
            encrypted_msg.add_header('Content-Disposition', 'attachment', filename='encrypted.asc')
            msg.attach(encrypted_msg)
            msg.add_header('Content-Type', 'multipart/encrypted; protocol="application/pgp-encrypted"')
        else:
            msg.attach(MIMEText(body, 'plain'))

        # Send email
        if SMTP_PORT == 465:
            # Use implicit SSL for port 465
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
        else:
            # Use STARTTLS for 587 (or others)
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)

        print(f"✅ Email sent to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

# ============================================
# Message Processing
# ============================================

def process_email(email_data):
    """Process a single email"""
    print(f"\n{'='*60}")
    print(f"📧 Processing email from: {email_data['sender_email']}")
    print(f"   Subject: {email_data['subject']}")
    print(f"{'='*60}")

    # Skip decryption, use raw body directly
    message_text = email_data['body'].strip()
    
    print(f"📄 Received message:")
    print(f"   {message_text[:100]}{'...' if len(message_text) > 100 else ''}")

    # Generate response (this is where you'd call picoclaw!)
    response = generate_response(message_text, email_data['sender_email'])

    if not response:
        print("❌ No response generated")
        return False

    print(f"💬 Response generated")

    # Skip encryption, always send unencrypted
    print(f"Sending plaintext response")
    send_email(
        email_data['sender_email'],
        RESPONSE_PREFIX + email_data['subject'],
        response,
        is_encrypted=False
    )

    return True

def generate_response(message, sender_email):
    """
    Generate a response to the message.

    This is a placeholder function. In a real implementation, you would:
    1. Call the picoclaw AI with the message
    2. Get the AI's response
    3. Return it here

    For now, this returns a simple acknowledgement.
    """
    import pico_channel
    
    response_content = pico_channel.ask_pico(message, session_id=sender_email)

    response = f"""This is an automated response from picoclaw.

Your message has been received:
{message}

---
AI Reply:
{response_content}
---

Sender: {sender_email}
Time: {datetime.now().isoformat()}"""

    return response

# ============================================
# Main Loop
# ============================================

def run_once():
    """Run one check cycle"""
    print(f"\n🔍 Checking for new emails at {datetime.now().isoformat()}")

    # Connect to IMAP
    mail = connect_imap()
    if not mail:
        return False

    try:
        # Get new emails
        emails = get_new_emails(mail)

        if not emails:
            print("✅ No new emails found")
            return True

        print(f"📬 Found {len(emails)} new email(s)")

        # Process each email
        for email in emails:
            if process_email(email):
                save_processed_email(email['id'])
                print(f"✅ Email {email['id']} processed and marked")
            else:
                print(f"⚠️  Email {email['id']} processing failed")

        return True

    finally:
        mail.close()
        mail.logout()

def run_daemon():
    """Run as a daemon - continuously check for emails"""
    print("🦞 picoclaw Email Watcher starting...")
    print(f"   Check interval: {CHECK_INTERVAL} seconds")
    print(f"   IMAP: {IMAP_USER}@{IMAP_SERVER}:{IMAP_PORT}")
    print(f"   SMTP: {SMTP_USER}@{SMTP_SERVER}:{SMTP_PORT}")
    print()

    try:
        while True:
            run_once()
            print(f"\n⏳ Sleeping for {CHECK_INTERVAL} seconds...")
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n🛑 Watcher stopped by user")

# ============================================
# Entry Point
# ============================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='picoclaw Email Watcher')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--test', action='store_true', help='Test mode - print config and exit')
    args = parser.parse_args()

    if args.test:
        print("Configuration test:")
        print(f"  IMAP: {IMAP_USER}@{IMAP_SERVER}:{IMAP_PORT}")
        print(f"  SMTP: {SMTP_USER}@{SMTP_SERVER}:{SMTP_PORT}")
        print(f"  Check Interval: {CHECK_INTERVAL}s")
        print(f"  Allowed Sender: {ALLOWED_SENDER or 'Any'}")
        sys.exit(0)

    if args.once:
        success = run_once()
        sys.exit(0 if success else 1)

    # Run as daemon
    run_daemon()
