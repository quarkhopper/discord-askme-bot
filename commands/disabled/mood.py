import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
import re  # Import regex module to extract IDs from mentions
from commands.bot_errors import BotErrors  # Import the error handler

class MoodAnalyzer(commands.Cog):
    """Cog for analyzing the mood of a user or recent messages in a channel."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Initialize OpenAI client

    async def fetch_messages(self, ctx, user: discord.Member = None, channel: discord.TextChannel = None, limit=10):
        """Fetch the last `limit` messages from a specific user in the given channel."""
        if channel is None:
            channel = ctx.channel  # Default to the current channel

        messages = []
        async for message in channel.history(limit=100):  # Search up to 100 messages for context
            if user is None or message.author == user:
                messages.append(f"{message.author.display_name}: {message.content}")
                if len(messages) >= limit:
                    break

        return messages

    def extract_id(self, mention):
        """Extracts the numeric ID from a Discord mention format (<@ID> or <#ID>)."""
        match = re.match(r"<@!?(\d+)>|<#(\d+)>", mention)
        if match:
            return int(match.group(1) or match.group(2))
        return None

    async def resolve_member(self, ctx, identifier):
        """Tries to resolve a user by mention, name, or ID in a server context."""
        if ctx.guild is None:
            return None  # Prevents lookup in DMs, since there's no guild

        member = None
        user_id = self.extract_id(identifier)

        if user_id:
            member = ctx.guild.get_member(user_id)  # Fast lookup
            if not member:  # If not in cache, fetch user
                try:
                    member = await ctx.bot.fetch_user(user_id)
                except discord.NotFound:
                    return None
        else:
            member = discord.utils.get(ctx.guild.members, name=identifier)

        return member

    async def resolve_channel(self, ctx, identifier):
        """Tries to resolve a channel by mention, name, or ID."""
        if ctx.guild is None:
            return None  # Prevents lookup in DMs, since there's no guild

        channel = None
        channel_id = self.extract_id(identifier)

        if channel_id:
            channel = ctx.guild.get_channel(channel_id)
            if not channel:
                try:
                    channel = await ctx.bot.fetch_channel(channel_id)
                except discord.NotFound:
                    return None
        else:
            channel = discord.utils.get(ctx.guild.text_channels, name=identifier)

        return channel

    @commands.command()
    @BotErrors.require_role("Vetted")  # ✅ Standardized role requirement
    async def mood(self, ctx, *args):
        """Analyze the mood of a specific user or the last 10 messages in the specified channel.
        
        **Usage:**
        `!mood` → Analyzes the current channel.
        `!mood @User` → Analyzes @User's messages in the current channel.
        `!mood #general` → Analyzes messages in #general.
        `!mood @User #general` → Analyzes @User's messages in #general.

        **Restrictions:**
        - ❌ **This command cannot be used in DMs.**
        """

        # ❌ Block DM mode but ensure the user gets feedback
        if isinstance(ctx.channel, discord.DMChannel):
            try:
                await ctx.send("❌ The `!mood` command can only be used in a server.")
            except discord.Forbidden:
                pass  # In case the user has DMs disabled
            return

        # Check if command is in a forbidden channel
        if await BotErrors.check_forbidden_channel(ctx):
            return

        user = None
        channel = ctx.channel  # Default to current channel

        # Resolve optional user and channel arguments
        for arg in args:
            resolved_user = await self.resolve_member(ctx, arg)
            if resolved_user:
                user = resolved_user
                continue

            resolved_channel = await self.resolve_channel(ctx, arg)
            if resolved_channel:
                channel = resolved_channel
                continue

            await ctx.send(f"⚠️ Could not recognize `{arg}` as a valid user or channel.")
            return

        messages = await self.fetch_messages(ctx, user=user, channel=channel)
        if not messages:
            await ctx.send("No messages found for the specified user or channel.")
            return

        prompt = (
            "Analyze the emotions in this conversation and suggest how the participant might be feeling:\n\n" +
            "\n".join(messages) +
            "\n\nGive a concise emotional summary."
        )

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI that analyzes emotions in conversations."},
                    {"role": "user", "content": prompt}
                ],
            )
            
            mood_analysis = response.choices[0].message.content.strip()
            config.logger.info(f"Mood analysis result: {mood_analysis}")

            # ✅ Ensure execution feedback is **ALWAYS** sent via DM
            execution_feedback = (
                f"**Command Executed:** !mood\n"
                f"**Channel:** {ctx.channel.name}\n"
                f"**Timestamp:** {ctx.message.created_at}\n\n"
                f"💡 **Mood Analysis:**\n{mood_analysis}"
            )

            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send(execution_feedback)
            except discord.Forbidden:
                await ctx.send("❌ Could not send a DM. Please enable DMs from server members.")

            # ✅ Delete command message in **server mode**
            await ctx.message.delete()

        except Exception as e:
            config.logger.error(f"Error analyzing mood: {e}")
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send("An error occurred while analyzing the mood.")
            except discord.Forbidden:
                await ctx.send("An error occurred while analyzing the mood.")


async def setup(bot):
    await bot.add_cog(MoodAnalyzer(bot))

    command = bot.get_command("mood")
    if command:
        command.command_mode = "server"
