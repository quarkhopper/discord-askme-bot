import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord_bot")  # Named logger for consistency

# Define forbidden channels
FORBIDDEN_CHANNELS = ["general"]

def is_forbidden_channel(ctx):
    return ctx.channel.name in FORBIDDEN_CHANNELS
