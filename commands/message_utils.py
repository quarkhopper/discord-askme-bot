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
        
        **DM Mode:** Deletes the bot’s own messages only.  
        **Server Mode:** Deletes messages from all users (if bot has permission).  
        
        Usage:
        `!clear` → Clears the last message.
        `!clear 5` → Clears the last 5 messages.
        """

        is_dm = isinstance(ctx.channel, discord.DMChannel)
        limit = min(limit, 100)

        try:
            dm_channel = await ctx.author.create_dm()
            await dm_channel.send(
                f"📌 **Command Executed:** `!clear`\n"
                f"📍 **Context:** {'Direct Message' if is_dm else ctx.channel.name}\n"
                f"⏳ **Timestamp:** {ctx.message.created_at}\n\n"
            )
        except discord.Forbidden:
            if not is_dm:
                await ctx.send("⚠️ Could not send a DM. Please enable DMs from server members.")
            return

        try:
            if is_dm:
                deleted = await ctx.channel.purge(limit=limit, check=lambda m: m.author == self.bot.user)
            else:
                deleted = await ctx.channel.purge(limit=limit + 1)

            await dm_channel.send(f"✅ Cleared {len(deleted) - (0 if is_dm else 1)} messages.")
        except Exception as e:
            config.logger.error(f"Error clearing messages: {e}")
            await dm_channel.send("An error occurred while clearing messages.")

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
            dm_channel = await ctx.author.create_dm()
            await dm_channel.send(
                f"📌 **Command Executed:** `!match`\n"
                f"📍 **Context:** {ctx.channel.name}\n"
                f"⏳ **Timestamp:** {ctx.message.created_at}\n\n"
                f"🔎 **Searching for:** `{text}`"
            )
        except discord.Forbidden:
            await ctx.send("⚠️ Could not send a DM. Please enable DMs from server members.")
            return

        try:
            count = 0
            async for message in ctx.channel.history(limit=100):
                if message.id == ctx.message.id:
                    continue
                count += 1
                if text in message.content:
                    await dm_channel.send(f"🔎 Found message {count} messages ago:\n**{message.author.display_name}:** `{message.content}`")
                    return count  

            await dm_channel.send("❌ No messages found containing the specified text.")
            return None
        except Exception as e:
            config.logger.error(f"Error finding message: {e}")
            await dm_channel.send("An error occurred while searching for messages.")
            return None

    @commands.command()
    @BotErrors.require_role("Fun Police")  # ✅ Requires both "Fun Police"
    @BotErrors.require_role("Vetted")  # ✅ and "Vetted" roles
    async def clearafter(self, ctx, *, text: str):
        """Clears all messages after a matched message.
        
        **DM Mode:** Deletes the bot’s own messages only.  
        **Server Mode:** Deletes messages from all users (if bot has permission).  

        Usage:
        `!clearafter hello` → Finds "hello" and deletes all messages after it.
        """

        if await BotErrors.check_forbidden_channel(ctx):
            return

        try:
            dm_channel = await ctx.author.create_dm()
            await dm_channel.send(
                f"📌 **Command Executed:** `!clearafter`\n"
                f"📍 **Context:** {ctx.channel.name}\n"
                f"⏳ **Timestamp:** {ctx.message.created_at}\n\n"
                f"🔎 **Searching for:** `{text}`"
            )
        except discord.Forbidden:
            await ctx.send("⚠️ Could not send a DM. Please enable DMs from server members.")
            return

        try:
            count = await self.match(ctx, text=text)  
            if count is None:
                return

            deleted = await ctx.channel.purge(limit=count + 2)  
            await dm_channel.send(f"✅ Cleared {len(deleted)} messages after `{text}`.")
        except Exception as e:
            config.logger.error(f"Error clearing messages after match: {e}")
            await dm_channel.send("An error occurred while clearing messages.")

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

        try:
            deleted = await ctx.channel.purge(limit=500, check=lambda m: m.author == self.bot.user)
            await dm_channel.send(f"✅ Cleared {len(deleted)} bot messages.")
        except Exception as e:
            config.logger.error(f"Error clearing bot messages in DM: {e}")
            await dm_channel.send("An error occurred while clearing messages.")

async def setup(bot):
    await bot.add_cog(MessageUtils(bot))
