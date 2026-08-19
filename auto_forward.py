from telethon import TelegramClient, events
import json
import os
import re
import hashlib
import asyncio
import logging
from telethon.sessions import StringSession

# ==========================
# 🔑 API
# ==========================
api_id = 30133788
api_hash = "YOUR_API_HASH"

# IMPORTANT:
# Put your Telegram StringSession here.
# Do NOT publish this value on GitHub or share it.
SESSION = "YOUR_STRING_SESSION"

# ==========================
# 📡 CHANNELS
# ==========================
source_channels = [
    "@AAUMEREJA",
    "@AAU_GENERAL",
    "@PECCAAiT",
    "@AAUNews11"
]

destination_channel = "@AAUCentral"

client = TelegramClient(
    StringSession(SESSION),
    api_id,
    api_hash
)

# ==========================
# 🧠 STORAGE
# ==========================
DATA_FILE = "processed.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        processed = json.load(f)
else:
    processed = {}


def save():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2)


# ==========================
# 🧹 TEXT
# ==========================
def clean_text(text):
    """
    IMPORTANT:
    Do NOT modify the original Telegram text.

    This preserves:
    - Normal URLs
    - Hidden URLs
    - @usernames
    - Bold
    - Italic
    - Underline
    - Code
    - Telegram formatting entities
    """

    if not text:
        return ""

    return text


# ==========================
# 📢 AAUCENTRAL BRANDING
# ==========================
def add_branding(text):
    branding = "📢 @AAUCentral"

    if not text:
        return branding

    # Prevent duplicate branding
    if "@AAUCentral" in text:
        return text

    return f"{text}\n\n{branding}"


# ==========================
# 🧠 DUPLICATE CHECK
# ==========================
def get_hash(text):
    text = (text or "").lower()

    return hashlib.md5(
        text.encode("utf-8")
    ).hexdigest()


print("🚀 PROFESSIONAL BOT RUNNING")


# ==========================
# 📸 HANDLE ALBUMS
# ==========================
@client.on(events.Album(chats=source_channels))
async def album_handler(event):

    try:
        # Use the first message for the caption
        message = event.messages[0]

        # raw_text preserves the original Telegram text
        text = message.raw_text or ""

        # ==========================
        # DUPLICATE CHECK
        # ==========================
        hash_key = get_hash(text)

        if hash_key in processed:
            print("⚠ Duplicate album skipped")
            return

        processed[hash_key] = True
        save()

        # ==========================
        # GET MEDIA
        # ==========================
        files = [
            msg.media
            for msg in event.messages
            if msg.media
        ]

        # ==========================
        # KEEP ORIGINAL TEXT
        # ==========================
        clean = clean_text(text)

        # ==========================
        # ADD BRANDING
        # ==========================
        clean = add_branding(clean)

        # ==========================
        # SEND ALBUM
        # ==========================
        await client.send_file(
            destination_channel,
            files,
            caption=clean,
            formatting_entities=message.entities
        )

        print("📸 Album forwarded with original links")

    except Exception as e:
        print("❌ Album Error:", e)


# ==========================
# ✍ HANDLE NORMAL POSTS
# ==========================
@client.on(events.NewMessage(chats=source_channels))
async def message_handler(event):

    try:

        message = event.message

        # ==========================
        # IGNORE ALBUM MESSAGES
        # ==========================
        if message.grouped_id:
            return

        # ==========================
        # ORIGINAL TEXT
        # ==========================
        text = message.raw_text or ""

        # ==========================
        # DUPLICATE CHECK
        # ==========================
        hash_key = get_hash(text)

        if hash_key in processed:
            print("⚠ Duplicate skipped")
            return

        processed[hash_key] = True
        save()

        # ==========================
        # KEEP ORIGINAL TEXT
        # ==========================
        clean = clean_text(text)

        # ==========================
        # ADD BRANDING
        # ==========================
        clean = add_branding(clean)

        # ==========================
        # SEND MESSAGE
        # ==========================
        if message.media:

            await client.send_file(
                destination_channel,
                message.media,
                caption=clean,
                formatting_entities=message.entities
            )

        else:

            await client.send_message(
                destination_channel,
                clean,
                formatting_entities=message.entities
            )

        print("✅ Message forwarded with original links")

    except Exception as e:
        print("❌ Message Error:", e)


# ==========================
# 🚀 RUN
# ==========================
logging.basicConfig(
    level=logging.INFO
)


async def main():

    print("🚀 BOT RUNNING...")
    print("📡 Monitoring:")

    for channel in source_channels:
        print(f"   • {channel}")

    print(f"📢 Destination: {destination_channel}")
    print("🔗 Original links: PRESERVED")
    print("👤 Original @usernames: PRESERVED")
    print("✨ Telegram formatting: PRESERVED")
    print("")


    await client.run_until_disconnected()


# ==========================
# START
# ==========================
with client:
    client.loop.run_until_complete(main())
