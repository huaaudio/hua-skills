import asyncio
import json
import uuid
import websockets
import os

async def get_pico_response_async(prompt: str, session_id: str = None) -> str:
    # Adjust port as necessary depending on your local server configuration
    uri = "ws://127.0.0.1:18800/pico/ws" # Replace with your actual websocket endpoint (ws://<the URL from your GUI>/pico/ws) if different
    config_path = os.path.join(os.path.dirname(__file__), "config.env")
    
    # Load token
    token = os.getenv("PICOCLAW_WS_TOKEN", "your_default_token_here")
    if config_path and os.path.exists(config_path):
        with open(config_path) as f:
            for line in f:
                if line.startswith("PICOCLAW_WS_TOKEN="):
                    token = line.strip().split("=", 1)[1]
                    break

    if not session_id:
        session_id = str(uuid.uuid4())
    
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        ws_url = f"{uri}?session_id={session_id}"
        async with websockets.connect(ws_url, additional_headers=headers) as websocket:

            message = {
                "id": str(uuid.uuid4()),
                "type": "message.send",
                "session_id": session_id,
                "payload": {
                    "content": prompt
                }
            }
            await websocket.send(json.dumps(message))

            while True:
                response_str = await websocket.recv()
                response = json.loads(response_str)
                
                # We specifically want the 'message.create' payload's content
                if response.get("type") == "message.create":
                    return response.get("payload", {}).get("content", "")
                elif response.get("type") == "error":
                    return f"Error from server: {response}"

    except websockets.exceptions.ConnectionClosed:
        return "Error: Connection closed"
    except Exception as e:
        return f"Error: {e}"

def ask_pico(prompt: str, session_id: str = None) -> str:
    """Synchronous wrapper to inject a prompt and return only the payload string."""
    return asyncio.run(get_pico_response_async(prompt, session_id))

if __name__ == "__main__":
    import sys
    test_prompt = sys.argv[1] if len(sys.argv) > 1 else "Hello from Python!"
    test_session = sys.argv[2] if len(sys.argv) > 2 else "my-persistent-session"
    # Execute and print purely the response payload
    print(ask_pico(test_prompt, session_id=test_session))
