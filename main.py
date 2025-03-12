import asyncio
import discord
import openai
import os
from discord.ext import commands
from dotenv import load_dotenv
import config  # Import shared config
import pathlib

# Load environment variables
load_dotenv()

# Initialize OpenAI client with the latest API format
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True  # Allows access to message content
bot = commands.Bot(command_prefix="!", intents=intents)

# Log when bot is ready
@bot.event
async def on_ready():
    config.logger.info(f"Logged in as {bot.user}")

# Load all Cogs from the 'commands' directory
async def load_cogs():
    commands_dir = pathlib.Path("commands")
    if commands_dir.exists():
        for command_file in commands_dir.glob("*.py"):
            if command_file.stem == "__init__":  # ⛔ Skip __init__.py
                continue
            
            module_name = f"commands.{command_file.stem}"
            try:
                await bot.load_extension(module_name)
                config.logger.info(f"Loaded {module_name}")
            except Exception as e:
                config.logger.error(f"Failed to load {module_name}: {e}")

# Start the bot
async def run_bot():
    config.logger.info("Starting Discord bot...")
    await load_cogs()
    await bot.start(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    asyncio.run(run_bot())
