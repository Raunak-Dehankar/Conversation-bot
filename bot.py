import discord
import os
import random
import datetime
import google.generativeai as genai
from discord.ext import tasks
# --- CONFIGURATION ---

# Load secrets from Replit's environment
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Configure the Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# The ID of the channel where the bot will operate
# To get this: right-click your channel in Discord -> Copy Channel ID
# You might need to enable Developer Mode in Discord settings (Advanced)
TARGET_CHANNEL_ID = os.getenv('CHANNEL_ID')  # <<< IMPORTANT: CHANGE THIS

# Your list of predefined questions
DAILY_QUESTIONS = [
    "What is one thing you are looking forward to today?",
    "Reflecting on yesterday, what was a moment that made you smile?",
    "What's a small, achievable goal you can set for yourself right now?",
    "What's one thing you can do today that your future self will thank you for?",
    "How are you feeling right now, and what might be the reason for that feeling?"
]

# --- DISCORD BOT SETUP ---

# Define the bot's intents (permissions)
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)

# --- BOT EVENTS AND TASKS ---


@client.event
async def on_ready():
    """This function runs when the bot successfully connects to Discord."""
    print(f'We have logged in as {client.user}')
    # Start the background task when the bot is ready
    daily_prompt.start()


@tasks.loop(time=datetime.time(
    13, 15, tzinfo=datetime.timezone(datetime.timedelta(hours=5, minutes=30))))
async def daily_prompt():
    """This is the scheduled background task that runs daily."""
    try:
        channel = client.get_channel(TARGET_CHANNEL_ID)
        if channel:
            question = random.choice(DAILY_QUESTIONS)
            await channel.send(
                f"<@{829638015416270858}> **Good morning! Here is your daily prompt:**\n\n> {question}"
            )
        else:
            print(f"Error: Channel with ID {TARGET_CHANNEL_ID} not found.")
    except Exception as e:
        print(f"Error in daily_prompt task: {e}")


@client.event
async def on_message(message):
    """This function runs every time a new message is sent in any channel."""
    # 1. PREVENT THE BOT FROM REPLYING TO ITSELF
    if message.author == client.user:
        return

    # 2. CHECK IF THE MESSAGE IS IN OUR TARGET CHANNEL
    if message.channel.id != TARGET_CHANNEL_ID:
        return

    # 3. PROCESS THE MESSAGE FOR A CONVERSATIONAL REPLY
    try:
        # Show a "typing..." indicator to the user
        async with message.channel.typing():
            # Fetch the last 10 messages to create a conversation history
            history = []
            async for msg in message.channel.history(limit=10):
                # We build the history from oldest to newest
                role = "user" if msg.author != client.user else "model"
                history.append({'role': role, 'parts': [msg.content]})
            history.reverse()  # Oldest message is now first

            # Start a chat with the history
            chat = model.start_chat(
                history=history[:-1]
            )  # History without the user's latest message

            # Send the user's latest message to Gemini
            response = await chat.send_message_async(message.content)

            # Send the AI's response back to the Discord channel
            await message.channel.send(response.text)

    except Exception as e:
        print(f"An error occurred while processing a message: {e}")
        await message.channel.send(
            "Sorry, I encountered an error while trying to respond.")

# --- RUN THE BOT ---
# This line uses the secret token to start the bot
client.run(DISCORD_TOKEN)
