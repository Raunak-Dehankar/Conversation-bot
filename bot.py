import discord
import asyncio
from datetime import datetime, time, timedelta
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# === CONFIG ===
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DAILY_HOUR = int(os.getenv("DAILY_HOUR", 9))
DAILY_MINUTE = int(os.getenv("DAILY_MINUTE", 0))

# Setup Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-pro")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# === Daily Check-in Questions ===
daily_questions = [
    "How are you feeling today? (1–5)",
    "What’s one thing you want to accomplish?",
    "Any distractions you should avoid?",
    "Share one small thing you’re grateful for.",
    "Do you want a motivational boost or a focus tip today?"
]

# === Memory storage ===
conversation_history = {}
current_day = datetime.now().date()

def reset_daily_memory():
    """Reset conversation histories at midnight."""
    global conversation_history, current_day
    today = datetime.now().date()
    if today != current_day:
        conversation_history = {}
        current_day = today

async def send_daily_checkin():
    """Send daily check-in questions at the scheduled time."""
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    while not client.is_closed():
        now = datetime.now()
        target = datetime.combine(now.date(), time(DAILY_HOUR, DAILY_MINUTE))
        if now > target:
            target += timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())
        
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(daily_questions)])
        await channel.send(f"🌞 Good morning! Here’s your daily check-in:\n\n{questions_text}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.channel.id == CHANNEL_ID:
        reset_daily_memory()
        user_id = str(message.author.id)
        
        # Get or initialize history for this user
        if user_id not in conversation_history:
            conversation_history[user_id] = [
                {"role": "system", "content": "You are a friendly daily check-in coach helping the user reflect and stay motivated."}
            ]
        
        # Add user message
        conversation_history[user_id].append({"role": "user", "content": message.content})
        
        try:
            response = model.generate_content(
                "\n".join([f"{m['role']}: {m['content']}" for m in conversation_history[user_id]])
            )
            reply = response.text.strip()
            
            # Save bot response to history
            conversation_history[user_id].append({"role": "assistant", "content": reply})
            
            if reply:
                await message.channel.send(reply)
        except Exception as e:
            await message.channel.send("⚠️ Sorry, I hit an error with Gemini.")
            print("Gemini error:", e)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

client.loop.create_task(send_daily_checkin())
client.run(DISCORD_TOKEN)
