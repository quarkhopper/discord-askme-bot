import asyncio
import discord
from discord.ext import commands
import config  # Import shared config
from commands.bot_errors import BotErrors  # Import the error handler


class MessageUtils(commands.Cog):
    """Cog for message management commands (clear, match, clearafter, clearall)."""

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

        try:
            count = 0
            async for message in ctx.channel.history(limit=100):
                if message.id == ctx.message.id:
                    continue
                count += 1
                if text in message.content:
                    await ctx.send(f"🔎 Found message {count} messages ago:\n**{message.author.display_name}:** `{message.content}`")
                    await ctx.message.delete()  # ✅ Deletes command message in server mode
                    return count  

            await ctx.send("❌ No messages found containing the specified text.")
            return None
        except Exception as e:
            config.logger.error(f"Error finding message: {e}")
            await ctx.send("An error occurred while searching for messages.")
            return None

    @commands.command()
    @BotErrors.require_role("Fun Police")  # ✅ Requires both "Fun Police"
    @BotErrors.require_role("Vetted")  # ✅ and "Vetted" roles
    async def clearafter(self, ctx, *, text: str):
        """Clears all messages after a matched message.
        
        **This command only works in servers.**  

        Usage:
        `!clearafter hello` → Finds "hello" and deletes all messages after it.
        """

        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        try:
            count = 0
            async for message in ctx.channel.history(limit=100):
                if text in message.content:
                    break
                count += 1
            else:
                await ctx.send("❌ No messages found containing the specified text.")
                return

            deleted = await ctx.channel.purge(limit=count + 2)  # Deletes after match + command message
            await ctx.send(f"✅ Cleared {len(deleted)} messages after `{text}` in #{ctx.channel.name}.")
        except Exception as e:
            config.logger.error(f"Error clearing messages after match: {e}")
            await ctx.send("An error occurred while clearing messages.")

    @commands.command()
    async def clearall(self, ctx):
        """Clears all bot messages in the DM history.  
        
        **This command only works in DMs.**
        """

        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("❌ This command can only be used in a direct message.")
            return

        try:
            dm_channel = await ctx.author.create_dm()
            await dm_channel.send(
                f"📌 **Command Executed:** `!clearall`\n"
                f"📍 **Context:** Direct Message\n"
                f"⏳ **Timestamp:** {ctx.message.created_at}\n\n"
                f"🧹 **Clearing all bot messages in this DM.**"
            )
        except discord.Forbidden:
            await ctx.send("⚠️ Could not send a DM. Please enable DMs from server members.")
            return

        deleted_count = 0

        try:
            # Fetch the last 500 messages and delete only those from the bot
            async for message in ctx.channel.history(limit=500):
                if message.author == self.bot.user:
                    try:
                        await message.delete()
                        deleted_count += 1
                        await asyncio.sleep(0.5)  # Prevent rate-limiting
                    except discord.NotFound:
                        continue  # Skip if message is already deleted

            await dm_channel.send(f"✅ Cleared {deleted_count} bot messages.")
        except Exception as e:
            config.logger.error(f"Error clearing bot messages in DM: {e}")
            await dm_channel.send("An error occurred while clearing messages.")

async def setup(bot):
    await bot.add_cog(MessageUtils(bot))
