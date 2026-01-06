from typing import Dict
from pinoywok.audio_player import AudioPlayer
import pinoywok.config
from pinoywok.logging import log
import pinoywok.helpers
import time
import aiohttp
from requests.utils import requote_uri
import json
import unicodedata
import asyncio
import sys
import websockets
import contextlib
# External function reference (assumed to be imported)
from print_service import print_order

from pinoywok.args import args
from pinoywok.config import config

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='urllib3')

# GLOBALS
has_internet_connection = True
remote_ws_service = None  # remote ws service
local_ws_service = None
audio_player = None  # Global audio player instance

# CONSTANTS
ENABLE_PING = False
PING_LOCAL_INTERVAL = 180
PING_REMOTE_INTERVAL = 180
PING_ACTION = "ping"
PING_MESSAGE = "pong"

# Alarm duration - must match frontend CustomNotificationsProcessing.tsx
ALARM_DURATION_SECONDS = 10

# Default welcome messages (can be overridden by config)
DEFAULT_WELCOME_MESSAGE = "Bienvenido a Kitchen Tabs"
DEFAULT_CONNECTED_MESSAGE = "Conectado al servidor"
DEFAULT_DISCONNECTED_MESSAGE = "Desconectado del servidor"
DEFAULT_SPEECH_LANGUAGE = "es"

def get_speech_message(key, default):
    """Get speech message from config with fallback to default"""
    return config.get_config(key) or default

def log(message):
    """Helper function to log messages with timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def speak(message, lang=None):
    """Helper function to speak a message using text-to-speech"""
    global audio_player
    try:
        if audio_player is None:
            audio_player = AudioPlayer()
        if lang is None:
            lang = config.get_config('SPEECH_LANGUAGE') or DEFAULT_SPEECH_LANGUAGE
        log(f"Speaking ({lang}): {message}")
        audio_player.thread_generate_audio(message, None, lang=lang)  # Use None to let audio_player use tempfile
    except Exception as e:
        log(f"Error speaking message: {e}")

async def is_internet_connected():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head("https://www.google.com") as response:
                return response.status == 200
    except aiohttp.ClientError:
        return False

async def check_internet_connection():
    global has_internet_connection
    while True:
        connected = await is_internet_connected()
        if connected != has_internet_connection:
            has_internet_connection = connected
            log(f"Internet connection state changed: {has_internet_connection}")
        await asyncio.sleep(5)

def WSMessage(action, message):
    messageObject = {"action": action, "timestamp": time.time()}
    try:
        message_json = json.loads(message)
        messageObject.update(message_json)
    except json.JSONDecodeError:
        messageObject["message"] = message
    return json.dumps(messageObject)

async def handle_reverb_event(channel, data):
    """Handle events from Laravel Reverb"""
    log(f"Received event on channel {channel}:")
    log(str(data))
    # Process your event data here
    await websocket_handler(json.dumps(data))

async def websocket_handler(message_bytes):
    _args = args.get_args()
    """
    Handle incoming Socket messages.
    :param message: incoming message (string or JSON)
    """
    # message bytes -> message string
    # TODO: some characters such as utf emoticons, make the application to crash. They are removed for now. 
    message = unicodedata.normalize('NFKD', message_bytes).encode('ascii', 'ignore').decode('ascii')
    log("Raw message received from websocket")
    log(message)
    # Check if message is a JSON string or a plain string
    try:
        json_message = json.loads(message)
        # Process the message based on type if needed
        if "type" in json_message:
            message_type = json_message["type"]
            log(f"Message Type: {message_type}")
            if "print" in message_type:
                # Handle nested data structure from Laravel notifications
                inner_data = json_message.get("data", {})
                tab_id = inner_data.get("tab_id", "")
                # If tab_id not found at first level, check nested data
                if not tab_id and isinstance(inner_data, dict):
                    tab_id = inner_data.get("data", {}).get("tab_id", "")
                log(f"Print Tab id: {tab_id}")
                if tab_id:
                    log(f"Calling print_order for tab {tab_id}...")
                    print_order(tab_id, _args.token.strip('"'), _args.log, _args.config)
                    log(f"print_order completed for tab {tab_id}")
                else:
                    log("ERROR: No tab_id found in message!")
            if "speech" in message_type:
                audio_player = AudioPlayer()
                speech_text = json_message.get("data", {}).get("speech") or json_message.get("data", {}).get("message", "")
                log(f"Speech Message: {speech_text}")
                
                # Check notification control flags from payload
                notification_data = json_message.get("data", {})
                
                # TTS flag - explicitly enable/disable text-to-speech
                tts_enabled = notification_data.get("tts") == "true" or notification_data.get("tts") == True
                
                # Alarm flag - indicates frontend will play alarm sound
                has_alarm = notification_data.get("alarm") == "true" or notification_data.get("alarm") == True
                
                # TTS delay - configurable delay before speaking (default to ALARM_DURATION if alarm is set)
                tts_delay = notification_data.get("tts_delay")
                if tts_delay is not None:
                    try:
                        delay = int(tts_delay)
                    except (ValueError, TypeError):
                        delay = ALARM_DURATION_SECONDS if has_alarm else 0
                else:
                    # Fallback: if alarm is set but no explicit delay, use default alarm duration
                    delay = ALARM_DURATION_SECONDS if has_alarm else 0
                
                if delay > 0:
                    log(f"[TTS] Will start after {delay}s delay (alarm: {has_alarm}, tts_enabled: {tts_enabled})")
                
                # Only generate TTS audio if tts_enabled is true
                if tts_enabled:
                    # Non-blocking: delay happens inside the audio thread
                    # Use None for audio_file to let audio_player use tempfile (avoids read-only filesystem issues)
                    audio_player.thread_generate_audio(speech_text, None, delay_seconds=delay)
                else:
                    log(f"[TTS] Disabled for this message (tts_enabled: {tts_enabled})")
    except json.JSONDecodeError:
        # If not JSON, assume it's a plain string, and create a 'standard' app format object with default action
        log("JSON Decode Error")
        json_message = {"action":"sendmessage","message": message}
        log(json.dumps(json_message))
        return

# You need to generate an auth token
async def get_auth_token(socket_id, channel):
    _args = args.get_args()
    AUTH_URL = f"{config.get_config('API_SCHEME')}://{config.get_config('API_HOST')}{':' + str(config.get_config('API_PORT')) if config.get_config('API_PORT') else ''}/{config.get_config('AUTH_ENDPOINT')}"
    """Get authentication token for private channels"""
    log(AUTH_URL)
    TOKEN = _args.token
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {TOKEN}",                    
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            json_data = {
                "socket_id": socket_id,
                "channel_name": channel.replace("null", "1") if "null" in channel else channel          
            }
            log(f"POST Headers: {json.dumps(headers, indent=2)}")
            log(f"POST JSON: {json.dumps(json_data, indent=2)}")
            async with session.post(
                AUTH_URL,
                headers=headers,
                json=json_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    log(f"Got auth token: {result}")
                    return result.get("auth")
                else:
                    log(f"Failed to get auth token. Status: {response.status}")
                    error_text = await response.text()
                    log(f"Error: {error_text}")
                    return None    
    except Exception as e:
        log(f"Error getting auth token: {e}")
        return None

# Update your receive_remote_ws_messages function
async def receive_remote_ws_messages(socket):
    _args = args.get_args()
    """
    Listen for incoming messages from the remote WebSocket service.
    This function will run continuously in an asyncio task.
    """
    log("=== Starting receive_remote_ws_messages function ===")
    try:
        # Wait for connection to be established first
        log("Waiting for connection_established event...")
        connection_established = False
        socket_id = None
        while not connection_established and socket.open:
            try:
                message = await socket.recv()
                log(f"Received initial message: {message}")
                try:
                    data = json.loads(message)
                    if data.get('event') == 'pusher:connection_established':
                        connection_data = json.loads(data.get('data', '{}'))
                        socket_id = connection_data.get('socket_id')
                        log(f"Connection established with Pusher server. Socket ID: {socket_id}")
                        connection_established = True
                except json.JSONDecodeError:
                    log(f"Error decoding initial message: {message}")
            except websockets.ConnectionClosed:
                log("Connection closed while waiting for establishment")
                return
            except Exception as e:
                log(f"Error while waiting for connection establishment: {e}")
                await asyncio.sleep(1)
        if not connection_established or not socket_id:
            log("Failed to establish connection properly or get socket ID")
            return
        # Now subscribe to channel with authentication
        log(f"Attempting to subscribe to private channel: {_args.channel}")
        # Get authentication token
        auth_token = await get_auth_token(socket_id, _args.channel)
        if not auth_token:
            log("Failed to get authentication token. Cannot subscribe to private channel.")
            return
        subscribe_payload = {
            "event": "pusher:subscribe",
            "data": {
                "channel": _args.channel,
                "auth": auth_token
            }
        }
        payload_json = json.dumps(subscribe_payload)
        log(f"Sending subscription payload: {payload_json}")
        await socket.send(payload_json)
        log(f"Subscription request sent for channel: {_args.channel}")
        # Main message processing loop
        log("Starting main message processing loop")
        while socket.open:
            try:
                # Wait for a message
                message = await socket.recv()
                # Clean message for logging to avoid Unicode issues
                clean_message = unicodedata.normalize('NFKD', message).encode('ascii', 'ignore').decode('ascii')
                log(f"Received message: {clean_message}")
                # Parse the message
                try:
                    message_data = json.loads(message)
                    # Check if it's a Pusher protocol message
                    event_type = message_data.get('event', '')
                    if event_type.startswith('pusher:'):
                        # Handle Pusher protocol messages
                        if event_type == 'pusher:subscription_succeeded':
                            log(f"Successfully subscribed to channel: {message_data.get('channel', 'unknown')}")
                            # Speak connected message when subscription succeeds
                            #connected_msg = get_speech_message('SPEECH_CONNECTED_MESSAGE', DEFAULT_CONNECTED_MESSAGE)
                            #speak(connected_msg)
                        elif event_type == 'pusher:ping':
                            log("Received ping, sending pong")
                            await socket.send(json.dumps({"event": "pusher:pong"}))
                        continue
                    # Process application event
                    channel = message_data.get('channel')
                    event = message_data.get('event')
                    log(f"Received application event: {event} on channel: {channel}")
                    # Extract data from the message
                    data = {}
                    if 'data' in message_data:
                        try:
                            if isinstance(message_data['data'], str):
                                data = json.loads(message_data['data'])
                            else:
                                data = message_data['data']
                        except json.JSONDecodeError:
                            log(f"Error decoding data: {message_data['data']}")
                            data = {"raw": message_data['data']}
                    # Process the message data
                    log(f"Processing event data: {data}")
                    await handle_reverb_event(channel, data)
                except json.JSONDecodeError:
                    log(f"Error decoding JSON message: {message}")
            except websockets.ConnectionClosed:
                log("WebSocket connection closed during message processing")
                return
            except Exception as e:
                log(f"Error in message processing loop: {e}")
                await asyncio.sleep(1)
    except Exception as e:
        log(f"Fatal error in receive_remote_ws_messages: {e}")
        import traceback
        log(traceback.format_exc())

async def send_remote_websocket(socket, message):
    """Send a message to the remote WebSocket"""
    try:
        await socket.send(message)
        log(f"Sent message to remote WebSocket: {message}")
    except Exception as e:
        log(f"Error sending message to remote WebSocket: {e}")

async def main():
    global has_internet_connection
    global remote_ws_service
    global audio_player

    # Config
    args.set_key("token", sys.argv[1] if len(sys.argv) > 1 else None)
    args.set_key("channel", sys.argv[2] if len(sys.argv) > 2 else None)
    args.set_key("config", sys.argv[3] if len(sys.argv) > 3 else "config.dev.yaml")
    args.set_key("log", sys.argv[4] if len(sys.argv) > 4 else "log.txt")

    _args = args.get_args()
    log(f"Token: {_args.token[1:-1]}")
    if not _args.token:
        log("Error: Token is required")
        sys.exit(1)
    config.load_config(_args.config)
    log(config.to_json())
    TOKEN = _args.token[1:-1]

    # Initialize audio player and speak welcome message
    try:
        audio_player = AudioPlayer()
        log("Audio player initialized")
        #welcome_msg = get_speech_message('SPEECH_WELCOME_MESSAGE', DEFAULT_WELCOME_MESSAGE)
        #speak(welcome_msg)
    except Exception as e:
        log(f"Warning: Could not initialize audio player: {e}")

    # Start the internet connection checker as a background task
    connection_checker_task = asyncio.create_task(check_internet_connection())

    try:
        while True:
            if has_internet_connection:
                try:
                    # Try to connect to the remote WebSocket service if not already connected
                    if remote_ws_service is None or not remote_ws_service.open:
                        WS_URL = f"{'wss' if config.get_config('WS_SCHEME') == 'https' else 'ws'}://{config.get_config('WS_HOST')}{':' + str(config.get_config('WS_PORT')) if config.get_config('WS_PORT') else ''}/app/{config.get_config('APP')}?protocol=7&client=python&version=7.0.0"       
                        log(f"REMOTE_WS: Connecting to {WS_URL}")
                        try:
                            remote_ws_service = await websockets.connect(
                                WS_URL, 
                                extra_headers={"Authorization": f"Bearer {TOKEN}"},
                                ping_interval=20,
                                ping_timeout=20
                            )
                            if remote_ws_service.open:
                                log(f"REMOTE_WS: Connected successfully")
                                log(f"REMOTE_WS Type: {type(remote_ws_service)}")
                                log(f"REMOTE_WS State: {remote_ws_service.state}")
                            else:
                                log("REMOTE_WS: Connection failed")
                                await asyncio.sleep(5)  # Wait before trying again
                                continue
                        except Exception as e:
                            log(f"REMOTE_WS Error during connection: {e}")
                            await asyncio.sleep(5)  # Wait before trying again
                            continue
                    # Start necessary tasks
                    log(f"Starting WebSocket listening and monitoring tasks")
                    tasks = [
                        # check_internet_connection() is already running in the background
                        #asyncio.create_task(pinoywok.helpers.monitor_system_events()),
                        asyncio.create_task(receive_remote_ws_messages(remote_ws_service)),
                    ]
                    # Add ping task if enabled
                    if ENABLE_PING:
                        tasks.append(asyncio.create_task(ping_remote_websocket(remote_ws_service)))
                    # Run all tasks concurrently, but return when any task finishes
                    done, pending = await asyncio.wait(
                        tasks,
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    # Cancel all pending tasks (e.g., receive_remote_ws_messages)
                    for task in pending:
                        task.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await task
                except Exception as e:
                    log(f"main - Unexpected error: {e}")
                    # Close socket if it exists
                    if remote_ws_service and remote_ws_service.open:
                        await remote_ws_service.close()
                    remote_ws_service = None
                    await asyncio.sleep(1)
            else:
                log("No internet connection. Waiting for connection...")
                await asyncio.sleep(1)
    finally:
        connection_checker_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await connection_checker_task

# Add this ping function back in case you want to re-enable it
async def ping_remote_websocket(socket):
    """Send regular pings to keep the connection alive"""
    while True:
        try:
            log("Sending ping to remote WebSocket")
            await socket.send(json.dumps({"event": "pusher:ping"}))
            await asyncio.sleep(PING_REMOTE_INTERVAL)
        except websockets.ConnectionClosed:
            log("Connection closed during ping, will attempt to reconnect")
            return  # Let the main loop handle reconnection
        except Exception as e:
            log(f"ping_remote_websocket - Error: {e}")
            await asyncio.sleep(1)

# Start the main async function
if __name__ == "__main__":
    asyncio.run(main())