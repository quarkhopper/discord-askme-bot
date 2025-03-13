import discord
from discord.ext import commands
import asyncio
import os

class ClearMessages(commands.Cog):
    """Cog for clearing messages in a channel."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def clear(self, ctx, limit: int = 1):
        """Clears a specified number of recent messages (default: 1, max: 100).
        
        **This command only works in servers and requires both "Fun Police" and "Vetted" roles.**
        
        Usage:
        `!clear` → Clears the last message.
        `!clear 5` → Clears the last 5 messages.
        """

        # Ensure command only runs in a server
        if not ctx.guild:
            return  # No error message; command is silently ignored in DMs

        # Enforce role restrictions
        fun_police_role = discord.utils.get(ctx.author.roles, name="Fun Police")
        vetted_role = discord.utils.get(ctx.author.roles, name="Vetted")

        if not fun_police_role or not vetted_role:
            return  # No error message; silently ignore unauthorized users

        # Limit the number of messages that can be cleared
        limit = min(limit, 100)

        try:
            await ctx.channel.purge(limit=limit + 1)  # Includes the command message itself
        except Exception as e:
            print(f"[Clear] Error clearing messages: {e}")  # Logs the error, no output to channel

# ✅ Ensure this command is server-only
async def setup(bot):
    await bot.add_cog(ClearMessages(bot))
    command = bot.get_command("clear")
    if command:
        command.command_mode = "server"
