from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = YOUR_API_ID
api_hash = "YOUR_API_HASH"
SESSION = "YOUR_STRING_SESSION"

client = TelegramClient(StringSession(SESSION), api_id, api_hash)


async def main():
    try:
        channel = await client.get_entity("@AAUNews11")

        print("✅ CHANNEL FOUND")
        print("ID:", channel.id)
        print("Title:", channel.title)
        print("Username:", channel.username)

    except Exception as e:
        print("❌ CANNOT ACCESS CHANNEL")
        print(type(e).__name__)
        print(e)


with client:
    client.loop.run_until_complete(main())
