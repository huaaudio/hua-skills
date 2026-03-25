# PicoClaw Email Channel & WebSocket Integration

This SKILL.md comprehensively documents the architecture, logic, and operational flow of the automated PicoClaw Email Channel pipeline. It outlines how the components work together to provide an end-to-end, async AI assistant integrated via email.

## 🌟 Overview
The project monitors a configured email inbox via IMAP, robustly extracts text from incoming emails (handling complex character encodings), bridges the message to a local PicoClaw WebSocket server (maintaining conversation history per sender), and replies directly to the user via SMTP.

## 🏗️ Core Components

### 1. pico_channel.py (WebSocket Bridging API)
Acts as the central communication bridge between the email watcher and the local PicoClaw AI server.
- **WebSocket Connection**: Connects to ws://127.0.0.1:18800/pico/ws.
- **Authentication**: Parses PICOCLAW_WS_TOKEN from config.env and sends it securely via the Authorization: Bearer <token> HTTP header.
- **Session Management**: Automatically passes a session_id as a URI query parameter (?session_id=...). This binds the WebSocket to a specific session context, allowing the server to push responses asynchronously to the correct client. By using the email sender's address as the session_id, the AI correctly maintains and remembers conversation history on a per-user basis.
- **Payload Handling**: Wraps prompts in the required JSON schema (	ype: "message.send"). Listens to the incoming asynchronous stream, deliberately ignoring typing indicators, to intercept the final message.create event and return the exact text payload string.
- **Callable API**: Exposes straightforward synchronous (ask_pico(prompt, session_id)) and asynchronous (get_pico_response_async) functions so it can be imported as a module.

### 2. email-watcher.py (The Polling Daemon)
Executes the main repetitive loop, processing emails and interfacing with pico_channel.py.
- **IMAP Polling Loop**: Uses imaplib to regularly poll for unread (UNSEEN) messages on a configured interval. It maintains a state file (state/processed_emails.txt) to deduplicate incoming messages and track processed emails.
- **Smart Charset Decoding**: Uses the email's dynamically provided headers (part.get_content_charset()) rather than forcing a strict utf-8 decode. This prevents garbling of international/non-latin characters (e.g., preserving Chinese characters from Outlook which heavily rely on encodings like gb2312 or gbk). Fallbacks gracefully using errors='replace'.
- **AI Integration**: Imports pico_channel.ask_pico. Passes the cleanly decoded message body as the prompt, and maps the sender_email rigidly directly into the session_id parameter to guarantee user-level memory inside PicoClaw.
- **SMTP Reply**: Wraps the AI payload inside an explicitly formatted email string (with timestamp metadata) and transmits the reply securely back to the exact sender via TLS/SSL.

## 🛠️ Execution Flow
1. email-watcher.py routinely surveys the INBOX.
2. An email arrives. The daemon extracts the subject, sender address, and safely decodes the email body depending on the charset provided by the sending client.
3. The daemon triggers pico_channel.ask_pico(body, session_id=sender_address).
4. pico_channel.py handshakes with PicoClaw over WebSockets, submitting the text in a message.send JSON payload, tagged with the assigned session ID.
5. The script waits for the AI typing stream to finish, grabs the newly fired message.create event, and hands the pure response text back to the daemon.
6. The daemon formats an SMTP response utilizing the AI's context and fires it back to the sender.

---
**Configuration Needs**:
Relies on a .env (config.env) setup providing IMAP credentials, SMTP configurations, and the PICOCLAW_WS_TOKEN.
