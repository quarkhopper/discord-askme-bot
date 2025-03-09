import discord
import openai
import os
from discord.ext import commands
from dotenv import load_dotenv
import importlib.util
import pathlib
import config  # Import shared config

# Load environment variables
load_dotenv()

# Initialize OpenAI client with the latest API format
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True  # Allows access to the content of messages
bot = commands.Bot(command_prefix="!", intents=intents)

# Log when bot is ready
@bot.event
async def on_ready():
    config.logger.info(f"Logged in as {bot.user}")

# Dynamically load command modules from the 'commands' directory and pass openai_client
commands_dir = pathlib.Path("commands")
if commands_dir.exists():
    for command_file in commands_dir.glob("*.py"):
        module_name = f"commands.{command_file.stem}"
        spec = importlib.util.spec_from_file_location(module_name, command_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "setup"):
            module.setup(bot, openai_client)  # Pass the OpenAI client to command modules

# Start the Discord bot
def run_bot():
    config.logger.info("Starting Discord bot...")
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    run_bot()
