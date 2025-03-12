import asyncio
import discord
from discord.ext import commands
import config  # Import shared config
from commands.bot_errors import BotErrors  # Import the error handler

class MessageUtils(commands.Cog):
    """Cog for message management commands (clear, match)."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @BotErrors.require_role("Fun Police")  # ✅ Requires both "Fun Police"
    @BotErrors.require_role("Vetted")  # ✅ and "Vetted" roles
    async def clear(self, ctx, limit: int = 1):
        """Clears a specified number of recent messages (default: 1, max: 100).
        
        **This command only works in servers.**
        
        Usage:
        `!clear` → Clears the last message.
        `!clear 5` → Clears the last 5 messages.
        """

        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        limit = min(limit, 100)

        try:
            deleted = await ctx.channel.purge(limit=limit + 1)  # Includes command message
            await ctx.send(f"✅ Cleared {len(deleted) - 1} messages in #{ctx.channel.name}.")
        except Exception as e:
            config.logger.error(f"Error clearing messages: {e}")
            await ctx.send("An error occurred while clearing messages.")

    @commands.command()
    @BotErrors.require_role("Vetted")  # ✅ Requires only "Vetted"
    async def match(self, ctx, *, text: str):
        """Finds a message that matches a partial string and reports its position.
        
        Usage:
        `!match hello` → Finds the most recent message containing "hello".
        """

        if await BotErrors.check_forbidden_channel(ctx):
            return

        is_dm = isinstance(ctx.channel, discord.DMChannel)  # ✅ Check if running in a DM

        try:
            count = 0
            async for message in ctx.channel.history(limit=100):
                if message.id == ctx.message.id:
                    continue
                count += 1
                if text in message.content:
                    await ctx.send(f"🔎 Found message {count} messages ago:\n**{message.author.display_name}:** `{message.content}`")
                    
                    if not is_dm:  # ✅ Only delete the command message in server mode
                        await ctx.message.delete()

                    return count  

            await ctx.send("❌ No messages found containing the specified text.")
            return None
        except Exception as e:
            config.logger.error(f"Error finding message: {e}")
            await ctx.send("An error occurred while searching for messages.")
            return None


async def setup(bot):
    await bot.add_cog(MessageUtils(bot))
    
    command = bot.get_command("clear")
    if command:
        command.command_mode = "server"

    command = bot.get_command("match")
    if command:
        command.command_mode = "both"
