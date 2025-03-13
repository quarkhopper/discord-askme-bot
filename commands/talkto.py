import discord
from discord.ext import commands
import openai
import os
import re  # Regex for extracting words
import asyncio
from collections import Counter

class TalkSimulator(commands.Cog):
    """Cog for simulating how a user might respond based on past messages."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.lock = asyncio.Lock()  # Prevents multiple API calls at once

    async def fetch_whitelisted_channels(self, ctx):
        """Fetch allowed channels from bot configuration."""
        config_manager = self.bot.get_cog("ConfigManager")
        if not config_manager:
            return []
        return await config_manager.get_command_whitelist("talkto")

    async def fetch_user_messages(self, ctx, user: discord.Member, limit_per_channel=10, total_limit=500, max_chars=6000):
        """Fetches messages from a user within whitelisted channels."""
        messages = []
        total_chars = 0
        whitelisted_channels = await self.fetch_whitelisted_channels(ctx)

        for channel in ctx.guild.text_channels:
            if channel.name not in whitelisted_channels:
                continue  # Skip non-whitelisted channels
            if not channel.permissions_for(ctx.guild.me).read_messages:
                continue  # Skip unreadable channels

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
                        return messages  # Stop if total limit reached

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
    async def talkto(self, ctx, user_mention: str, *, prompt: str):
        """Simulates a user's response based on their last messages.

        **Usage:**
        `!talkto @User What do you think about AI?`

        **Restrictions:**
        - ❌ **This command cannot be used in DMs.**
        - ✅ **Requires the "Vetted" role.**
        - 🕐 **Displays a "Please wait..." message while processing.**
        - 📩 **Results are posted in the server channel.**
        """

        # Ensure command only runs in a server
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("❌ The `!talkto` command can only be used in a server.")
            return

        # Enforce role restrictions
        role = discord.utils.get(ctx.author.roles, name="Vetted")
        if not role:
            await ctx.send("⚠️ You must have the 'Vetted' role to use this command.")
            return

        # Acknowledge command execution
        please_wait = await ctx.send(f"⏳ Processing... Simulating a response from `{user_mention}`. Please wait.")

        user = await self.resolve_member(ctx, user_mention)
        if not user:
            await please_wait.delete()
            await ctx.send(f"⚠️ Could not find a user matching `{user_mention}`.")
            return

        # Fetch user's past messages
        past_messages = await self.fetch_user_messages(ctx, user)
        if not past_messages:
            await please_wait.delete()
            await ctx.send(f"⚠️ No messages found for {user.display_name}.")
            return

        # Ensure message history does not exceed 5000 characters
        conversation_history = "\n".join(f"- {msg}" for msg in past_messages)
        if len(conversation_history) > 5000:
            conversation_history = conversation_history[:4997] + "..."

        # Generate relevant context from past messages
        topics = {word for word in past_messages if len(word) > 4}
        vocabulary = {word for word in past_messages}

        relevant_prompt = f"Prioritize responding in a way related to these topics: {', '.join(topics)}."
        vocabulary_hint = f"Try to use words from this set: {', '.join(vocabulary)}, but additional words are allowed."

        # Construct AI prompt
        prompt_text = f"""
        The following are messages from {user.display_name}:
        {conversation_history}

        {relevant_prompt}
        {vocabulary_hint}
        You are allowed to use metaphors, but they must be relevant to the user’s way of speaking.

        Do NOT use emojis in the response. Stick to text only.

        Now, generate a response in their style to this comment: "{prompt}"
        """

        # Fetch simulated response from OpenAI
        async with self.lock:
            try:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Mimic the style of the provided user messages."},
                        {"role": "user", "content": prompt_text}
                    ]
                )
                simulated_response = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[TalkTo] OpenAI API error: {e}")
                await please_wait.delete()
                await ctx.send("⚠️ An error occurred while generating a response.")
                return

        # Delete "Please wait..." message
        await please_wait.delete()

        # Send response in the server channel
        await ctx.send(f"🗣️ **Simulated Response from {user.display_name}:**\n{simulated_response}")

# ✅ Make this a **server-only** command
async def setup(bot):
    await bot.add_cog(TalkSimulator(bot))
    command = bot.get_command("talkto")
    if command:
        command.command_mode = "server"
