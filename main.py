import asyncio
import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
import config  # shared config
import pathlib

# Load environment variables
load_dotenv()

# Create bot instance (essential)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize OpenAI client if needed (use your pinned version)
# openai.api_key = os.getenv("OPENAI_API_KEY")

@bot.event
async def on_ready():
    config.logger.info(f"Logged in as {bot.user}")

# Load all cogs from 'commands' directory
async def load_cogs():
    commands_dir = pathlib.Path("commands")
    if commands_dir.exists():
        for command_file in commands_dir.glob("*.py"):
            cog_name = f"commands.{command_file.stem}"
            try:
                await bot.load_extension(cog_name)
                config.logger.info(f"Loaded cog: {cog_name}")
            except Exception as e:
                config.logger.error(f"Failed to load {cog_name}: {e}")

# Run the bot
async def run_bot():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_BOT_TOKEN"))

# Entry-point: define bot instance with proper intents
bot = commands.Bot(command_prefix=config.BOT_PREFIX, intents=intents)

asyncio.run(run_bot())
