import discord
import os
from groq import Groq
from collections import defaultdict

# ─── KONFIGURACIJA ────────────────────────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MAX_HISTORY = 10
# ──────────────────────────────────────────────────────────────────────────────

groq_client = Groq(api_key=GROQ_API_KEY)

conversation_history = defaultdict(list)

SYSTEM_PROMPT = """Ti si prijateljski Discord bot koji priča isključivo na srpskom jeziku (latinica).
Tvoje ime je "Zoki" i ti si član ovog Discord servera.
Ponašaj se opušteno, kao pravi drug - koristi srpski sleng kad je prikladno.
Možeš da pričaš o svemu: kako si, vicevi, saveti, pomoc oko zadataka, gaming, muzika...
Odgovori treba da budu kratki i prirodni, kao u pravom četu - ne predugački.
Nikad ne pišeš na engleskom osim ako te neko direktno pita nešto na engleskom.
Budi zabavan, topao i iskren."""


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


def get_ai_response(user_id: int, username: str, user_message: str) -> str:
    history = conversation_history[user_id]

    messages = [{"role": "system", "content": SYSTEM_PROMPT + f"\n\nKorisnik se zove: {username}"}]

    for entry in history:
        messages.append({"role": entry["role"], "content": entry["content"]})

    messages.append({"role": "user", "content": user_message})

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=500
        )
        bot_reply = response.choices[0].message.content.strip()

        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": bot_reply})

        if len(history) > MAX_HISTORY * 2:
            conversation_history[user_id] = history[-(MAX_HISTORY * 2):]

        return bot_reply

    except Exception as e:
        print(f"Greška sa Groq API: {e}")
        return "Ej, desila mi se neka greška... pokušaj ponovo malo kasnije 😅"


@client.event
async def on_ready():
    print(f"✅ Bot je online kao: {client.user}")
    print(f"   ID: {client.user.id}")
    print("   Taguj bota da bi pričao sa njim!")


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if client.user not in message.mentions:
        return

    user_text = message.content
    for mention in message.mentions:
        user_text = user_text.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "")
    user_text = user_text.strip()

    if not user_text:
        await message.reply("Hej! 👋 Kaži mi nešto, samo me taguj pa napiši šta hoćeš 😄")
        return

    async with message.channel.typing():
        username = message.author.display_name
        user_id = message.author.id

        print(f"📨 [{username}]: {user_text}")

        response = get_ai_response(user_id, username, user_text)

        print(f"🤖 [Zoki]: {response}")

    await message.reply(response)


client.run(DISCORD_TOKEN)