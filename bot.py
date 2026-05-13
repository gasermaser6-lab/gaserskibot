import discord
import os
import httpx
import json
from collections import defaultdict

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MAX_HISTORY = 5

conversation_history = defaultdict(list)

SYSTEM_PROMPT = """Ti si Zoki, lik sa Discord servera koji je uvek tu za ekipu.
Pričaš isključivo srpski latinica, opušteno i prirodno kao u pravom četu.
Koristi srpski sleng - "brate", "bre", "ma daj", "jbg", "lmao" i slično kad je prikladno.
Nikad ne pominjеš da si bot ili AI osim ako te direktno pitaju.
Odgovori su kratki i direktni - kao kad drug odgovara na poruku.
Ne budi previše formalan, ne koristi liste, ne drži predavanja.
Šališ se samo kad je prirodno, ne preteruješ sa humorom.
Ako te neko zadirkuje, zadirkuj i ti nazad ali kratko.
Ako te neko nešto pita, odgovori konkretno i direktno na to pitanje.
Ako te neko zamoli da nešto ponovi ili kaže ponovo, ponovi to bez komentara.
Ako te pitaju za savet, informaciju ili objašnjenje - daj normalan odgovor kao što bi drug dao.
KRITIČNO: Uvek piši SAMO latiničnim slovima, nikad ćirilicom. Nikad ne koristi reči koje nisu srpske. Ako nisi siguran za neku reč, koristi jednostavniju srpsku reč.
NIKAD ne pišeš svoje razmišljanje ili analizu pre odgovora. Odgovaraš direktno i odmah.
VAŽNO: Pišeš isključivo standardni srpski jezik latinica bez grešaka. Nikad ne izmišljaš reči, nikad ne koristiš bosanske ili hrvatske izraze. Koristiš samo srpske reči i srpski pravopis."""

MODELS = [
    "openrouter/free",
]

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


async def get_ai_response(user_id: int, username: str, user_message: str) -> str:
    history = conversation_history[user_id]

    messages = [{"role": "system", "content": SYSTEM_PROMPT + f"\n\nKorisnik se zove: {username}"}]
    for entry in history:
        messages.append({"role": entry["role"], "content": entry["content"]})
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as http:
        for model in MODELS:
            try:
                resp = await http.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json={"model": model, "messages": messages, "max_tokens": 150}
                )
                data = resp.json()

                if resp.status_code != 200:
                    print(f"Greška sa {model}: {data}")
                    continue

                bot_reply = data["choices"][0]["message"]["content"].strip()

                history.append({"role": "user", "content": user_message})
                history.append({"role": "assistant", "content": bot_reply})
                if len(history) > MAX_HISTORY * 2:
                    conversation_history[user_id] = history[-(MAX_HISTORY * 2):]

                print(f"   (model: {model})")
                return bot_reply

            except Exception as e:
                print(f"Greška sa {model}: {e}")
                continue

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
        response = await get_ai_response(user_id, username, user_text)
        print(f"🤖 [Zoki]: {response}")

    await message.reply(response)


client.run(DISCORD_TOKEN)
