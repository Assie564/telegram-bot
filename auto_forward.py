from telethon import TelegramClient, events
import json
import os
import re
import hashlib
import asyncio
import logging
from telethon.sessions import StringSession

# ==========================
# 🔑 API & CONFIG
# ==========================
api_id = 30133788
api_hash = "1f2d2d024eaafe22909fbb1131e1f084"
SESSION = "1BJWap1sBuyDitjiqa5zljH-ujf-oP7Uf5DmEuRcjL_y4lkiPjgmuz0W4Dp_UAnpTWww7W8F4v9agiRZYpBX4XAW0IDhsjSSTuWbAUXbtaqy4yo-fnSwM7bQlvoeyVvoYqrfGuh6iCMtFT3cJQEfiy-HvrZ32__6Pw45aEEjNT7wpsll5FGCEUW2hPgW-VLu7zizbtGwcSaOXJI7hdftwM5oPsA9XsilJRcqyyMVamJEloHkAn9B5gvMRqDpzohLJvb9rLxtC980gf-qt8dvddGAqFN5-oDRVoOAUGtizRsbVgz1TSrW-IJ_ixgUkB6jRjrwZ2aUPl7a5nzacKyS26RZTWFuOBHM="

# --- NEW MODE SETTING ---
# Options: "media" (only photos/videos), "text" (only text messages), or "all"
PROCESS_MODE = "media" 

# --- LINK REPLACEMENT DICTIONARY ---
# Add items here to automatically swap old links/usernames for new ones
REPLACEMENTS = {
    "@AAUMEREJA": "@AAUCentral",
    "@AAU_GENERAL": "@AAUCentral",
    "@PECCAAiT": "@AAUCentral",
    "@AAUNews11": "@AAUCentral",
    "t.me/old_link": "t.me/AAUCentral"
}

# ==========================
# 📡 CHANNELS
# ==========================
source_channels = ["@AAUMEREJA", "@AAU_GENERAL", "@PECCAAiT", "@AAUNews11"]
destination_channel = "@AAUCentral"

client = TelegramClient(StringSession(SESSION), api_id, api_hash)

# ==========================
# 🧠 STORAGE
# ==========================
DATA_FILE = "processed.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        processed = json.load(f)
else:
    processed = {}

def save():
    with open(DATA_FILE, "w") as f:
        json.dump(processed, f)

# ==========================
# 🧹 CLEAN & REPLACE TEXT
# ==========================
def clean_text(text):
    if not text:
        return ""

    # 1. Automatic Link/Username Replacement
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)

    # 2. Remove spam words (but NOT links or @usernames)
    text = re.sub(r"(join|subscribe|follow|contact us)", "", text, flags=re.IGNORECASE)

    # 3. Clean up extra spaces/newlines
    text = re.sub(r"\n\s*\n", "\n\n", text)
    
    return text.strip()

# ==========================
# 🚫 REMOVE NOISE LINES
# ==========================
def remove_noise_lines(text):
    lines = text.split("\n")
    clean_lines = []

    for line in lines:
        # We no longer remove lines just because they have an "@"
        # We only remove lines that are purely "Join us" or "Subscribe"
        lower_line = line.lower().strip()
        if lower_line in ["join", "subscribe", "follow", "click here"]:
            continue
        clean_lines.append(line)

    return "\n".join(clean_lines)

# ==========================
# 🧠 DUPLICATE CHECK
# ==========================
def get_hash(text):
    # Use the raw text for hashing to ensure uniqueness
    return hashlib.md5((text or "").lower().encode()).hexdigest()

print(f"🚀 BOT RUNNING IN MODE: {PROCESS_MODE}")

# ==========================
# 📸 HANDLE ALBUMS
# ==========================
@client.on(events.Album(chats=source_channels))
async def album_handler(event):
    # Mode Filter
    if PROCESS_MODE == "text":
        return

    text = event.messages[0].text or ""
    hash_key = get_hash(text)

    if hash_key in processed:
        return

    processed[hash_key] = True
    save()

    files = [msg.media for msg in event.messages]
    clean = clean_text(text)
    clean = remove_noise_lines(clean)
    clean += "\n\n📢 @AAUCentral"

    try:
        await client.send_file(destination_channel, files, caption=clean)
        print("📸 Album forwarded")
    except Exception as e:
        print("Error:", e)

# ==========================
# ✍ HANDLE NORMAL POSTS
# ==========================
@client.on(events.NewMessage(chats=source_channels))
async def message_handler(event):
    message = event.message
    if message.grouped_id:
        return

    # --- MODE FILTERING ---
    has_media = bool(message.media)
    
    if PROCESS_MODE == "media" and not has_media:
        return # Skip text-only posts
    
    if PROCESS_MODE == "text" and has_media:
        return # Skip media posts

    text = message.text or ""
    hash_key = get_hash(text)

    if hash_key in processed:
        return

    processed[hash_key] = True
    save()

    clean = clean_text(text)
    clean = remove_noise_lines(clean)
    clean += "\n\n📢 @AAUCentral"

    try:
        if message.media:
            await client.send_file(destination_channel, message.media, caption=clean)
        else:
            await client.send_message(destination_channel, clean)
        print("✅ Message forwarded")
    except Exception as e:
        print("Error:", e)

# ==========================
# 🚀 RUN
# ==========================
logging.basicConfig(level=logging.INFO)

async def main():
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
