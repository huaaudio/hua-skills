# picoclaw Email Watcher

Automated email watcher daemon for picoclaw that monitors an inbox, decrypts GPG-encrypted messages, processes them, and sends encrypted responses.

## 📁 Files

- **email-watcher.py** - Main watcher daemon

## 🚀 Quick Start

### 1. Configure Email Settings

Edit `config.env` with your email credentials:

```env
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IMAP_USER=picoclaw@example.com
IMAP_PASS=your-app-password

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=picoclaw@example.com
SMTP_PASS=your-app-password

CHECK_INTERVAL=60
```

### 2. Test the Watcher

```powershell
# Windows
python email-watcher.py --test

# Unix/Linux/macOS
python3 email-watcher.py --test
```

### 3. Run Once (Test)

```powershell
python email-watcher.py --once
```

## 🔄 How It Works

1. **Check for new emails** - Connects to IMAP and fetches unread messages
4. **Generate response** - Calls picoclaw AI (you need to integrate this!)
6. **Send reply** - Sends encrypted response via SMTP
7. **Mark as processed** - Tracks processed emails to avoid duplicates

## 🔧 Integrating picoclaw AI

The `generate_response()` function in `email-watcher.py` has been updated to seamlessly integrate with your local PicoClaw WebSocket server using `pico_channel.py`.

### How it works:
```python
def generate_response(message, sender_email):
    """Generate response using the async PicoClaw WebSocket API"""
    import pico_channel
    
    # We pass sender_email as the session_id to maintain individual conversation history
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
```

## 📊 Monitoring

### View Logs

```powershell
# Windows
type logs\watcher.log

# Unix/Linux/macOS
tail -f logs/watcher.log
```

### Status

```bash
# Linux systemd
sudo systemctl status picoclaw-email-watcher

# macOS launchctl
launchctl list | grep picoclaw

# Windows (if using NSSM)
nssm status PicoclawEmailWatcher
```

## 🛠️ Troubleshooting

### Emails not being processed
1. Check logs for errors
2. Verify IMAP credentials in `config.env`

### Service not starting
1. Check service logs
2. Verify Python in PATH
3. Run `--test` flag to check configuration

## 🔐 Security Notes

2. **Use app passwords** - Never use account passwords for Gmail
3. **TLS/SSL only** - All connections use SSL/TLS
4. **Limit senders** - Set `ALLOWED_SENDER` in config to restrict who can send emails
5. **Monitor logs** - Regularly check for suspicious activity

---

🦞 picoclaw - Your automated AI assistant
