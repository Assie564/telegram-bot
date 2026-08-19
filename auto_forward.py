from telethon import TelegramClient, events
import json
import os
import hashlib
import asyncio
import logging
from telethon.sessions import StringSession

# ==========================
# 🔑 API
# ==========================
api_id = 30133788
api_hash = "YOUR_API_HASH"

# Put your existing StringSession here
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
    DO NOT MODIFY ORIGINAL TEXT.

    This keeps:
    - Normal URLs
    - Hidden URLs
    - @usernames
    - Bold
    - Italic
    - Underline
    - Code
    - Telegram formatting
    """

    if not text:
        return ""

    return text


# ==========================
# 📢 BRANDING
# ==========================
def add_branding(text):
    branding = "📢 @AAUCentral"

    if not text:
        return branding

    # Don't add branding twice
    if "@AAUCentral" in text:
        return text

    return text + "\n\n" + branding


# ==========================
# 🧠 DUPLICATE CHECK
# ==========================
def get_hash(text):
    text = (text or "").lower()

    return hashlib.md5(
        text.encode("utf-8")
    ).hexdigest()


# ==========================
# 📤 SEND NORMAL MESSAGE
# ==========================
async def send_normal_message(message):

    text = message.raw_text or ""

    clean = clean_text(text)
    clean = add_branding(clean)

    entities = message.entities

    try:

        # Try preserving Telegram formatting/entities
        await client.send_message(
            destination_channel,
            clean,
            formatting_entities=entities
        )

        return True

    except Exception as e:

        print("⚠ Formatting send failed:")
        print(e)

        # ==========================
        # FALLBACK
        # ==========================
        # Try sending without formatting entities.
        # This ensures normal URLs still work.
        try:

            await client.send_message(
                destination_channel,
                clean
            )

            print("✅ Sent using fallback method")

            return True

        except Exception as e2:

            print("❌ Fallback send failed:")
            print(e2)

            return False


# ==========================
# 📤 SEND MEDIA MESSAGE
# ==========================
async def send_media_message(message):

    text = message.raw_text or ""

    clean = clean_text(text)
    clean = add_branding(clean)

    entities = message.entities

    try:

        # Try preserving Telegram formatting/entities
        await client.send_file(
            destination_channel,
            message.media,
            caption=clean,
            formatting_entities=entities
        )

        return True

    except Exception as e:

        print("⚠ Media formatting send failed:")
        print(e)

        # ==========================
        # FALLBACK
        # ==========================
        try:

            await client.send_file(
                destination_channel,
                message.media,
                caption=clean
            )

            print("✅ Media sent using fallback method")

            return True

        except Exception as e2:

            print("❌ Media fallback failed:")
            print(e2)

            return False


# ==========================
# 📸 HANDLE ALBUMS
# ==========================
@client.on(events.Album(chats=source_channels))
async def album_handler(event):

    try:

        message = event.messages[0]

        text = message.raw_text or ""

        # ==========================
        # DUPLICATE CHECK
        # ==========================
        hash_key = get_hash(text)

        if hash_key in processed:

            print("⚠ Duplicate album skipped")

            return

        # ==========================
        # GET MEDIA
        # ==========================
        files = [
            msg.media
            for msg in event.messages
            if msg.media
        ]

        if not files:

            print("⚠ Album contains no media")

            return

        # ==========================
        # CAPTION
        # ==========================
        clean = clean_text(text)
        clean = add_branding(clean)

        # ==========================
        # SEND ALBUM
        # ==========================
        try:

            await client.send_file(
                destination_channel,
                files,
                caption=clean,
                formatting_entities=message.entities
            )

            print("📸 Album forwarded with links and formatting")

            # Only mark as processed AFTER successful sending
            processed[hash_key] = True
            save()

        except Exception as e:

            print("⚠ Album formatting send failed:")
            print(e)

            # ==========================
            # FALLBACK ALBUM
            # ==========================
            try:

                await client.send_file(
                    destination_channel,
                    files,
                    caption=clean
                )

                print("📸 Album forwarded using fallback")

                processed[hash_key] = True
                save()

            except Exception as e2:

                print("❌ Album forwarding failed:")
                print(e2)

    except Exception as e:

        print("❌ Album handler error:")
        print(e)


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

        # ==========================
        # SEND MESSAGE
        # ==========================
        success = False

        if message.media:

            success = await send_media_message(message)

        else:

            success = await send_normal_message(message)

        # ==========================
        # ONLY SAVE AFTER SUCCESS
        # ==========================
        if success:

            processed[hash_key] = True
            save()

            print("✅ Message forwarded successfully")

        else:

            print("❌ Message was NOT forwarded")
            print("It will be tried again if another event occurs.")

    except Exception as e:

        print("❌ Message handler error:")
        print(e)


# ==========================
# 🚀 RUN
# ==========================
logging.basicConfig(
    level=logging.INFO
)


async def main():

    print("")
    print("======================================")
    print("🚀 AAUCENTRAL FORWARDING BOT")
    print("======================================")
    print("")
    print("📡 Source channels:")

    for channel in source_channels:
        print("   •", channel)

    print("")
    print("📢 Destination:")
    print("   •", destination_channel)

    print("")
    print("🔗 Links: PRESERVED")
    print("👤 @usernames: PRESERVED")
    print("✨ Formatting: PRESERVED")
    print("📢 Branding: @AAUCentral")
    print("")
    print("======================================")
    print("🚀 BOT RUNNING...")
    print("======================================")
    print("")

    await client.run_until_disconnected()


# ==========================
# START
# ==========================
with client:
    client.loop.run_until_complete(main())
