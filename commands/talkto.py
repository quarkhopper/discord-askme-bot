import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
import re  # Regex for extracting words
from collections import Counter
from commands.bot_errors import BotErrors  # Error handler

class TalkSimulator(commands.Cog):
    """Cog for simulating how a user might respond based on past messages."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @staticmethod
    async def not_in_dm(ctx):
        """Prevents the command from running in DMs."""
        if isinstance(ctx.channel, discord.DMChannel):
            try:
                await ctx.send("❌ The `!talkto` command can only be used in a server.")
            except discord.Forbidden:
                pass  # Fail silently if DMs are disabled
            return False  # Prevents command execution
        return True

    async def fetch_user_messages(self, ctx, user: discord.Member, limit_per_channel=10, total_limit=500, max_chars=6000):
        """Fetches messages from a user, with a total character cap of 6000."""
        messages = []
        total_chars = 0

        for channel in ctx.guild.text_channels:
            if not channel.permissions_for(ctx.guild.me).read_messages:
                continue  # Skip channels the bot can't read

            channel_message_count = 0

            try:
                async for message in channel.history(limit=100, oldest_first=False):
                    if message.author == user:
                        msg_text = message.content.strip()
                        if total_chars + len(msg_text) > max_chars:
                            break  # Stop when character limit is reached

                        messages.append(msg_text)
                        total_chars += len(msg_text)
                        channel_message_count += 1

                    if len(messages) >= total_limit:
                        return messages  # Stop if we've hit the total message limit

                    if channel_message_count >= limit_per_channel:
                        break  # Stop fetching from this channel

            except discord.Forbidden:
                continue  # Skip channels with permission issues

        return messages

    async def resolve_member(self, ctx, identifier):
        """Resolves a user by mention, name, or ID."""
        match = re.match(r"<@!?(\d+)>", identifier)
        user_id = int(match.group(1)) if match else None
        if user_id:
            return ctx.guild.get_member(user_id) or await self.bot.fetch_user(user_id)
        return discord.utils.get(ctx.guild.members, name=identifier)

    @commands.command()
    @commands.check(not_in_dm)  # ✅ Prevents DM execution before parsing arguments
    @BotErrors.require_role("Vetted")  # ✅ Standardized role requirement
    async def talkto(self, ctx, user_mention: str, *, prompt: str):
        """Simulates a user's response based on their last messages, using their vocabulary while allowing flexibility.

        **Usage:**
        `!talkto @User What do you think about AI?`

        **Restrictions:**
        - ❌ **This command cannot be used in DMs.**
        - ✅ **Requires the "Vetted" role to execute.**
        - 📩 **Sends the response via DM.**
        """

        # ✅ Immediately delete the command message to avoid clutter
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass  # If message was already deleted, ignore

        # Check if command is in a forbidden channel
        if await BotErrors.check_forbidden_channel(ctx):
            return

        user = await self.resolve_member(ctx, user_mention)
        if not user:
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send(f"⚠️ Could not find a user matching `{user_mention}`.")
            except discord.Forbidden:
                await ctx.send(f"⚠️ Could not find a user matching `{user_mention}`.")
            return

        try:
            dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()

            # ✅ Send execution header **before processing**
            execution_header = (
                f"**Command Executed:** !talkto\n"
                f"**Channel:** {ctx.channel.name}\n"
                f"**Timestamp:** {ctx.message.created_at}\n\n"
                f"🗣️ **Simulating a response from {user.display_name}... Please wait.**"
            )
            await dm_channel.send(execution_header)

            past_messages = await self.fetch_user_messages(ctx, user)
            if not past_messages:
                await dm_channel.send(f"⚠️ No messages found for {user.display_name}.")
                return

            # ✅ Ensure message history does not exceed 5000 characters (extra safety buffer)
            conversation_history = "\n".join(f"- {msg}" for msg in past_messages)
            if len(conversation_history) > 5000:
                conversation_history = conversation_history[:4997] + "..."

            topics = {word for word in past_messages if len(word) > 4}
            vocabulary = {word for word in past_messages}

            relevant_prompt = f"Prioritize responding in a way related to these topics: {', '.join(topics)}."
            vocabulary_hint = f"Try to use words from this set: {', '.join(vocabulary)}, but additional words are allowed."

            prompt_text = f"""
            The following are messages from {user.display_name}:
            {conversation_history}

            {relevant_prompt}
            {vocabulary_hint}
            You are allowed to use metaphors, but they must be relevant to the user’s way of speaking.

            Do NOT use emojis in the response. Stick to text only.
            
            Now, generate a response in their style to this comment: "{prompt}"
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Mimic the style of the provided user messages."},
                    {"role": "user", "content": prompt_text}
                ]
            )

            simulated_response = response.choices[0].message.content.strip()

            # ✅ Send final response separately
            await dm_channel.send(f"🗣️ **Simulated Response from {user.display_name}:**\n{simulated_response}")

        except Exception as e:
            config.logger.error(f"Error in !talkto: {e}")
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send("⚠️ An error occurred while generating a response.")
            except discord.Forbidden:
                await ctx.send("⚠️ An error occurred while generating a response.")

TalkSimulator.talkto.command_mode = "server"

async def setup(bot):
    await bot.add_cog(TalkSimulator(bot))

    command = bot.get_command("talkto")
    if command:
        command.command_mode = "server"