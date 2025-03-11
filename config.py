import logging
import discord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord_bot")  # Named logger for consistency

# Define forbidden channels (now empty)
FORBIDDEN_CHANNELS = []  # ✅ No longer restricting #general

def is_forbidden_channel(ctx):
    """Returns True if the command is executed in a forbidden channel."""
    if isinstance(ctx.channel, discord.DMChannel):  # DMs should not be blocked
        return False
    return ctx.channel.name in FORBIDDEN_CHANNELS
