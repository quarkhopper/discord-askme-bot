import discord
from discord.ext import commands  # Import commands

class BotErrors:
    """Handles centralized error checks and messages for the bot."""

    @staticmethod
    async def check_forbidden_channel(ctx):
        """Check if a command is used in a forbidden channel and notify the user."""
        from config import is_forbidden_channel  # Import dynamically to avoid circular import issues
        if is_forbidden_channel(ctx):
            await ctx.send("⚠️ This bot cannot respond in this channel.")
            return True  # Signal that the command should stop
        return False

    @staticmethod
    def require_role(role_name):
        """Decorator to restrict commands to users with a specific role."""
        async def predicate(ctx):
            if discord.utils.get(ctx.author.roles, name=role_name):
                return True
            await ctx.send(f"⛔ You need the **{role_name}** role to use this command.")
            return False
        return commands.check(predicate)  # Fix: `commands` is now properly imported
