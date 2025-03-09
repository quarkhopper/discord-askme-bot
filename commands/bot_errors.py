import config

class BotErrors:
    """Handles centralized error checks and messages for the bot."""

    @staticmethod
    async def check_forbidden_channel(ctx):
        """Check if a command is used in a forbidden channel and notify the user."""
        if config.is_forbidden_channel(ctx):
            await ctx.send("⚠️ This bot cannot respond in this channel.")
            return True  # Signal that the command should stop
        return False
