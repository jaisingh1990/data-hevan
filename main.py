import os
import sys
import asyncio
import time
from dotenv import load_dotenv
import discord
from google import genai

# --- 1. Load Keys and Setup ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

if not DISCORD_TOKEN or not GEMINI_API_KEY:
    print("ERROR: DISCORD_TOKEN or GOOGLE_API_KEY not found in .env file.")
    sys.exit(1)

# --- 2. User Input ---
try:
    # 1. Ask for Channel ID
    CHANNEL_ID = int(input("Enter Discord Channel ID where the bot should run: "))
    
    # 2. Ask for Reply Delay
    REPLY_DELAY = int(input("Enter the delay time between each automatic reply (in seconds, e.g., 30): "))
    
    # 3. Ask for Latest Message Send Time
    LAST_MESSAGE_DELAY = int(input("Enter the reply delay after receiving the latest message (in seconds, e.g., 3): "))

except ValueError:
    print("ERROR: Input must be a number.")
    sys.exit(1)


# --- 3. Initialize Gemini Client ---
try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    sys.exit(1)

# --- 4. Discord Client Setup ---
intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

# Variable to record the last reply time
last_reply_time = 0

# --- 5. Bot Logic (Auto-reply) ---
@client.event
async def on_ready():
    print("--------------------------------------------------")
    print(f'✅ Bot {client.user} is online.')
    print(f'⌛ Reply delay set to: {REPLY_DELAY} seconds')
    print(f'💬 Bot will only reply in Channel ID: {CHANNEL_ID}')
    print("--------------------------------------------------")

@client.event
async def on_message(message):
    global last_reply_time
    current_time = time.time()
    
    # A. Ignore bot's own messages and messages from wrong channels
    if message.author == client.user:
        return
    if message.channel.id != CHANNEL_ID:
        return

    # B. Timer Check: Stop if not enough time has passed since the last reply
    if current_time - last_reply_time < REPLY_DELAY:
        time_left = REPLY_DELAY - (current_time - last_reply_time)
        print(f"Waiting for reply delay. {time_left:.2f} seconds remaining.")
        return # Exit without sending a message

    # C. Latest Message Delay
    await asyncio.sleep(LAST_MESSAGE_DELAY)
    
    # D. Request response from Gemini
    user_message = message.content
    system_instruction = "You are a friendly and highly active Discord user. Your response should be concise, natural, and always encourage conversation to assist with leveling."
    
    try:
        print(f"\n[RECEIVED] {message.author}: {user_message}")
        
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config={"system_instruction": system_instruction}
        )
        
        gemini_reply = response.text
        
        # E. Send the reply to Discord
        await message.channel.send(gemini_reply)
        
        # F. Update the last reply time
        last_reply_time = time.time()
        print(f"[SENT] Reply sent. Next reply in {REPLY_DELAY} seconds.")
        
    except Exception as e:
        print(f"[ERROR] Gemini API Error: {e}")


# --- 6. Run the Bot ---
client.run(DISCORD_TOKEN)
