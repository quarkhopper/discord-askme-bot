import discord
import openai
import os
from discord.ext import commands
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True  # Allows access to the content of messages
bot = commands.Bot(command_prefix="!", intents=intents)

# Log when bot is ready
@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")

# Define a command for the Discord bot
@bot.command()
async def chat(ctx, *, message: str):
    """A simple command to interact with OpenAI"""
    try:
        # Use the OpenAI chat API correctly (v1.0.0+)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Or whichever model you want to use
            messages=[{"role": "user", "content": message}]
        )
        # Send the response to Discord
        await ctx.send(response['choices'][0]['message']['content'])

    except Exception as e:
        logging.error(f"Error interacting with OpenAI: {e}")
        await ctx.send(f"An error occurred: {e}")

# Start the Discord bot
def run_bot():
    logging.info("Starting Discord bot...")
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    run_bot()
