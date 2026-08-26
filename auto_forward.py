import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import os
import re
import hashlib
import json
import logging


print("=" * 50)
print("🚀 AAUCENTRAL FORWARD BOT (Full Album + Dedup)")
print("=" * 50)


# ==================================================
# 🔑 API
# ==================================================

# Put these in Railway Variables
API_ID = int(os.getenv("API_ID", "30133788"))
API_HASH = os.getenv("API_HASH", "1f2d2d024eaafe22909fbb1131e1f084")
STRING_SESSION = os.getenv("STRING_SESSION", "1BJWap1sBu7QDso8FxYgqLoL068fSdEvjsSDdDuI_XYpxdGzYT-yNOgAbv7P1Cw95F5JLVb7_I2FSW2TyCi99KGbOZalLPT7Ip7QRpVbZV_kaeXbBj-Yd1LtwGIMlHIFpr0FVwPR0E08oFYU1UB2VILPBFCDJ-t_uivmgHynYz0qN8luh3qwThRq89G7UOr0oZgW385db5fflDSlM5XSvAUlMrDJa0hE8IgTyVyfmRTejEKt588cCsKIVLEG98r0ay4Ft7c3P3B33NiSyfz7HK4juq565o47SFuFIXyNfBSk2CRhdsUW8t00C3edEmgoI3NKxX0rmpovbi0gRW9XWQdYoWjb0_DI=")

if not API_HASH:
    print("❌ API_HASH environment variable not set!")
    print("Please add it in Railway Variables")
    exit(1)

if not STRING_SESSION:
    print("❌ STRING_SESSION environment variable not set!")
    print("Please add it in Railway Variables")
    exit(1)


# ==================================================
# 📡 CHANNELS
# ==================================================

source_channels = [
    "AAUMEREJA",
    "AAU_GENERAL",
    "PECCAAiT",
    "AAUNews11",
]

target_channel = "AAUCentral"
your_username = "@AAUCentral"


print(f"\n📡 Monitoring {len(source_channels)} channels:")

for ch in source_channels:
    print(f"   - @{ch}")

print(f"🎯 Forwarding to: @{target_channel}")


# ==================================================
# 🤖 CLIENT
# ==================================================

client = TelegramClient(
    StringSession(STRING_SESSION),
    API_ID,
    API_HASH
)


# ==================================================
# 💾 PERSISTENT DEDUPLICATION STORAGE
# ==================================================

DATA_FILE = "processed.json"


def load_processed():
    if not os.path.exists(DATA_FILE):
        return {
            "processed": [],
            "processed_albums": []
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "processed": data.get("processed", []),
            "processed_albums": data.get("processed_albums", [])
        }

    except Exception as e:
        print(f"⚠️ Could not load processed.json: {e}")

        return {
            "processed": [],
            "processed_albums": []
        }


def save_processed():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "processed": list(processed),
                    "processed_albums": list(processed_albums)
                },
                f,
                ensure_ascii=False
            )

    except Exception as e:
        print(f"❌ Could not save processed.json: {e}")


saved_data = load_processed()

# For deduplication of single messages
processed = set(saved_data["processed"])

# For deduplication of albums and content hashes
processed_albums = set(saved_data["processed_albums"])


# ==================================================
# 🧹 CLEAN TEXT
# ==================================================

def clean_text(text):

    if not text:
        return ""

    # Keep links — do NOT remove http or t.me links

    # Remove @usernames
    text = re.sub(r"@\w+", "", text)

    # Remove spam words
    text = re.sub(
        r"(join|subscribe|follow)",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Remove excessive empty lines
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    return text.strip()


# ==================================================
# 🚫 REMOVE NOISE LINES
# ==================================================

def remove_noise_lines(text):

    lines = text.split("\n")
    clean_lines = []

    for line in lines:

        if any(
            word in line.lower()
            for word in ["join", "follow", "subscribe", "@"]
        ):
            continue

        clean_lines.append(line)

    return "\n".join(clean_lines).strip()


# ==================================================
# 🧠 DUPLICATE HASH
# ==================================================

def get_text_hash(text):
    """Generate a hash of the cleaned text for deduplication."""

    cleaned = clean_text(text)

    cleaned = remove_noise_lines(cleaned)

    # Same approach as the second code:
    # use the first 200 characters as fingerprint
    fingerprint = cleaned[:200] if cleaned else ""

    # For empty captions return empty string
    # This avoids treating all captionless posts as identical
    if not fingerprint:
        return ""

    return hashlib.md5(
        fingerprint.encode("utf-8")
    ).hexdigest()


# ==================================================
# ✂️ SPLIT LONG MESSAGE
# ==================================================

def split_message(text, max_len=4000):

    if len(text) <= max_len:
        return [text]

    chunks = []

    for i in range(0, len(text), max_len):
        chunks.append(text[i:i + max_len])

    return chunks


# ==================================================
# 📢 CREATE FINAL MESSAGE
# ==================================================

def create_full_message(cleaned):

    if cleaned:
        return f"{cleaned}\n\n📢 {your_username}"

    return f"📢 {your_username}"


# ==================================================
# 📤 SEND LONG MESSAGE
# ==================================================

async def send_long(channel, message):

    chunks = split_message(message)

    if not chunks:
        return

    print(f"📝 Splitting into {len(chunks)} parts")

    first = await client.send_message(
        channel,
        chunks[0],
        parse_mode=None
    )

    for i, chunk in enumerate(chunks[1:], start=2):

        try:

            await client.send_message(
                channel,
                chunk,
                reply_to=first.id,
                parse_mode=None
            )

            print(f"📤 Part {i}/{len(chunks)} sent")

            await asyncio.sleep(0.3)

        except:

            await client.send_message(
                channel,
                chunk,
                parse_mode=None
            )

    return len(chunks)


# ==================================================
# 📸 ALBUM HANDLER
# Same structure as your SECOND CODE
# ==================================================

@client.on(events.Album)
async def album_handler(event):

    try:

        chat = await event.get_chat()

        if not chat.username:
            return

        # Check source channel
        if chat.username.lower() not in [
            ch.lower() for ch in source_channels
        ]:
            return

        grouped_id = event.grouped_id

        if not grouped_id:
            return

        # Collect ALL media and captions
        media_list = []
        caption_parts = []

        for msg in event.messages:

            if msg.media:
                media_list.append(msg.media)

            if msg.raw_text:
                caption_parts.append(msg.raw_text)

        if not media_list:

            print("⚠️ No media in album, skipping.")

            return


        # Combine captions and clean
        combined_caption = (
            "\n".join(caption_parts)
            if caption_parts
            else ""
        )

        cleaned = clean_text(combined_caption)

        cleaned = remove_noise_lines(cleaned)


        # ==========================================
        # DEDUPLICATION
        # Same logic as SECOND CODE
        # ==========================================

        caption_hash = get_text_hash(combined_caption)

        # Include chat ID like the second code
        # For captionless albums use grouped ID
        if caption_hash:
            album_key = (
                f"{chat.id}_album_{caption_hash}"
            )
        else:
            album_key = (
                f"{chat.id}_album_{grouped_id}"
            )


        if album_key in processed_albums:

            print(
                f"⏩ Skipping duplicate album "
                f"from @{chat.username}"
            )

            return


        # Mark as processed
        processed_albums.add(album_key)


        # Also mark individual message IDs
        # to prevent double processing
        for msg in event.messages:

            msg_key = f"{chat.id}_{msg.id}"

            processed.add(msg_key)


        # Keep storage manageable
        if len(processed_albums) > 5000:
            processed_albums.clear()

        if len(processed) > 5000:
            processed.clear()

        save_processed()


        # Add AAUCentral branding
        full = create_full_message(cleaned)


        print(
            f"\n📸 Album detected from @{chat.username} "
            f"({len(media_list)} media items)"
        )

        print(
            f"   Caption length: {len(full)} characters"
        )


        # Send ALL media as ONE album
        await client.send_file(
            target_channel,
            media_list,
            caption=full,
            parse_mode=None,
            album=True
        )


        print(
            f"✅ Album forwarded: "
            f"{len(media_list)} media items with caption"
        )


    except Exception as e:

        print(f"❌ Album handler error: {e}")

        import traceback
        traceback.print_exc()


# ==================================================
# ✍ SINGLE MESSAGE HANDLER
# Same structure as your SECOND CODE
# ==================================================

@client.on(events.NewMessage)
async def handler(event):

    try:

        # Skip messages belonging to an album
        if event.message.grouped_id is not None:
            return


        chat = await event.get_chat()

        if not chat.username:
            return


        # Check source channel
        if chat.username.lower() not in [
            ch.lower() for ch in source_channels
        ]:
            return


        msg_id = f"{chat.id}_{event.id}"


        # Check if exact message was processed
        if msg_id in processed:
            return


        print(
            f"\n📨 From @{chat.username} "
            f"(single message)"
        )


        original = event.raw_text or ""

        cleaned = clean_text(original)

        cleaned = remove_noise_lines(cleaned)


        # ==========================================
        # DEDUPLICATION
        # Same approach as SECOND CODE
        # ==========================================

        caption_hash = get_text_hash(original)


        if caption_hash:

            single_key = (
                f"{chat.id}_single_{caption_hash}"
            )


            if single_key in processed_albums:

                print(
                    f"⏩ Skipping duplicate single message "
                    f"from @{chat.username}"
                )

                processed.add(msg_id)

                save_processed()

                return


            processed_albums.add(single_key)


            if len(processed_albums) > 5000:
                processed_albums.clear()


        # Mark message as processed
        processed.add(msg_id)


        if len(processed) > 5000:
            processed.clear()


        save_processed()


        # Add AAUCentral branding
        full = create_full_message(cleaned)


        # ==========================================
        # SINGLE MEDIA
        # ==========================================

        if event.message.media:

            print(
                "📎 Single media – sending with caption"
            )


            await client.send_file(
                target_channel,
                event.message.media,
                caption=full,
                parse_mode=None
            )


            print(
                "✅ Single media sent with caption"
            )


        # ==========================================
        # TEXT ONLY
        # ==========================================

        else:

            parts = await send_long(
                target_channel,
                full
            )


            print(
                f"✅ Done – {parts} parts sent"
            )


    except Exception as e:

        print(f"❌ Error in handler: {e}")

        import traceback
        traceback.print_exc()


# ==================================================
# 🚀 MAIN
# ==================================================

async def main():

    print("\n🔌 Connecting...")

    await client.start()

    me = await client.get_me()

    print(
        f"✅ Connected as "
        f"@{me.username if me.username else me.id}"
    )

    print("🤖 Bot running\n")

    await client.run_until_disconnected()


# ==================================================
# ▶️ START
# ==================================================

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    asyncio.run(main())
