import asyncio
import json
import logging
import os
import hashlib
import chainlit as cl
from google.cloud import pubsub_v1, firestore

# === Initialize Firestore ===
db = firestore.Client()

# === Initialize Pub/Sub ===
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project")
CONTEXT_REQUEST_TOPIC = os.getenv("CONTEXT_REQUEST_TOPIC", "ContextRequest")
CHAT_REQUEST_TOPIC = os.getenv("CHAT_REQUEST_TOPIC", "ChatRequest")

publisher = pubsub_v1.PublisherClient()
topic_path_ctx = publisher.topic_path(PROJECT_ID, CONTEXT_REQUEST_TOPIC)
topic_path_chat = publisher.topic_path(PROJECT_ID, CHAT_REQUEST_TOPIC)

# === Logging setup ===
logger = logging.getLogger("chainlit_app")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.info(f"🚀 Application started - Project: {PROJECT_ID}")


# === Authentication Helper Functions ===
def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


async def get_user_from_firestore(username: str):
    """Retrieve user from Firestore."""
    user_ref = db.collection("users").document(username)
    user_doc = user_ref.get()
    if user_doc.exists:
        return user_doc.to_dict()
    return None


async def create_user(username: str, password: str):
    """Create a new user in Firestore."""
    user_ref = db.collection("users").document(username)

    # Check if user already exists
    if user_ref.get().exists:
        logger.warning(f"Attempted to create existing user: {username}")
        return False

    user_data = {
        "username": username,
        "password_hash": hash_password(password),
        "created_at": firestore.SERVER_TIMESTAMP
    }
    user_ref.set(user_data)
    logger.info(f"Created new user: {username}")
    return True


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password meets requirements."""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, ""


# === Chainlit Password Authentication with Registration ===
@cl.password_auth_callback
async def auth_callback(username: str, password: str):
    """Authenticate user with Firestore-stored credentials or register new user."""

    # Validate inputs
    if not username or not password:
        logger.warning("Empty username or password attempted")
        return None

    # Check if user exists
    user_data = await get_user_from_firestore(username)

    if user_data:
        # Existing user - verify password
        if user_data.get("password_hash") == hash_password(password):
            logger.info(f"User logged in: {username}")
            return cl.User(
                identifier=username,
                metadata={"username": username, "is_new": False}
            )
        else:
            logger.warning(f"Failed login attempt for user: {username}")
            return None
    else:
        # New user - validate password and create account
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            logger.warning(f"Password validation failed for new user {username}: {error_msg}")
            return None

        # Create new user
        success = await create_user(username, password)
        if success:
            logger.info(f"New user registered and logged in: {username}")
            return cl.User(
                identifier=username,
                metadata={"username": username, "is_new": True}
            )
        else:
            logger.error(f"Failed to create user: {username}")
            return None


# === Firestore helper functions ===
async def wait_for_firestore_doc(collection: str, doc_id: str, timeout: int = 30):
    """Poll Firestore for document readiness."""
    doc_ref = db.collection(collection).document(doc_id)
    for _ in range(timeout * 10):
        doc = doc_ref.get()
        if doc.exists and doc.to_dict().get("ready"):
            logger.info(f"Document ready in {collection}/{doc_id}")
            return doc.to_dict()
        await asyncio.sleep(0.1)
    raise TimeoutError(f"Timeout waiting for Firestore document: {collection}/{doc_id}")


async def publish_event(topic_path, payload):
    """Publish JSON payload to Pub/Sub."""
    publisher.publish(topic_path, json.dumps(payload).encode("utf-8"))
    logger.info(f"Published event to {topic_path}: {payload}")


# === Chat start handler ===
@cl.on_chat_start
async def start_chat():
    """Initialize chat session after authentication."""
    user = cl.user_session.get("user")
    username = user.identifier
    is_new_user = user.metadata.get("is_new", False)

    if is_new_user:
        await cl.Message(content=f"🎉 Welcome, {username}! Your account has been created successfully.").send()
        logger.info(f"First-time chat started for new user: {username}")
    else:
        await cl.Message(content=f"👋 Welcome back, {username}!").send()
        logger.info(f"Chat started for existing user: {username}")

    # Load or request context
    await load_or_request_context(username)


async def load_or_request_context(username: str):
    """Load existing context or request new one."""
    session_ref = db.collection("sessions").document(username)
    session_doc = session_ref.get()

    if session_doc.exists and session_doc.to_dict().get("context"):
        context = session_doc.to_dict()["context"]
        cl.user_session.set("context", context)
        await cl.Message(content="✅ Session context loaded").send()
        logger.info(f"Loaded context for user {username}")
    else:
        await cl.Message(content="🔄 Setting up your session...").send()
        payload = {"session_id": username, "event": "context_request"}
        await publish_event(topic_path_ctx, payload)
        try:
            context_data = await wait_for_firestore_doc("sessions", username, timeout=60)
            cl.user_session.set("context", context_data.get("context"))
            await cl.Message(content="✅ Session ready!").send()
            logger.info(f"Context received and stored for user {username}")
        except TimeoutError:
            await cl.Message(content="⚠️ Session setup timed out. Please try again.").send()
            logger.error(f"Timeout while waiting for context for user {username}")


# === Chat message handler ===
@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming chat messages."""
    user = cl.user_session.get("user")
    username = user.identifier

    context = cl.user_session.get("context")
    chat_id = f"{username}-{message.id}"

    # Write chat request to Firestore
    db.collection("chats").document(chat_id).set({
        "username": username,
        "request": message.content,
        "status": "pending",
        "timestamp": firestore.SERVER_TIMESTAMP
    })
    logger.info(f"Chat request written to Firestore: {chat_id}")

    # Publish to Pub/Sub
    payload = {
        "chat_id": chat_id,
        "session_id": username,
        "context": context,
        "message": message.content,
    }
    await publish_event(topic_path_chat, payload)

    # Show processing message
    processing_msg = cl.Message(content="💬 Processing your request...")
    await processing_msg.send()

    # Wait for backend response in Firestore
    try:
        answer_doc = await wait_for_firestore_doc("chats", chat_id, timeout=60)
        response_text = answer_doc.get("response", "(no response)")

        # Update the processing message with the response
        processing_msg.content = response_text
        await processing_msg.update()

        logger.info(f"Chat response delivered to user {username}")
    except TimeoutError:
        processing_msg.content = "⚠️ Request timed out. Please try again."
        await processing_msg.update()
        logger.error(f"Timeout waiting for chat response: {chat_id}")
    except Exception as e:
        processing_msg.content = f"⚠️ Error: {str(e)}"
        await processing_msg.update()
        logger.error(f"Error processing message: {e}")