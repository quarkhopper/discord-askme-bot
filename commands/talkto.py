import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
import re  # Regex for extracting IDs
from commands.bot_errors import BotErrors  # Error handler

class TalkSimulator(commands.Cog):
    """Cog for simulating how a user might respond based on past messages."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def fetch_user_messages(self, ctx, user: discord.Member, limit=10):
        """Fetch the last `limit` messages from the specified user across all channels."""
        messages = []
        for channel in ctx.guild.text_channels:
            if not channel.permissions_for(ctx.guild.me).read_messages:
                continue  # Skip channels the bot can't read
            
            try:
                async for message in channel.history(limit=100):  # Fetch more for filtering
                    if message.author == user:
                        messages.append(message.content)
                        if len(messages) >= limit:
                            return messages
            except discord.Forbidden:
                continue  # Skip channels with permission issues
        return messages

    def extract_id(self, mention):
        """Extracts a numeric ID from a Discord mention."""
        match = re.match(r"<@!?(\d+)>", mention)
        return int(match.group(1)) if match else None

    async def resolve_member(self, ctx, identifier):
        """Resolves a user by mention, name, or ID."""
        user_id = self.extract_id(identifier)
        if user_id:
            return ctx.guild.get_member(user_id) or await self.bot.fetch_user(user_id)
        return discord.utils.get(ctx.guild.members, name=identifier)

    @commands.command()
    @BotErrors.require_role("Peoples")  # Ensure only authorized roles can use it
    async def talkto(self, ctx, user_mention: str, *, prompt: str):
        """Simulates a user's response based on their last 10 messages.

        Usage:
        `!talkto @User What do you think about AI?`
        """
        if config.is_forbidden_channel(ctx):
            return
        
        user = await self.resolve_member(ctx, user_mention)
        if not user:
            await ctx.send(f"⚠️ Could not find a user matching `{user_mention}`.")
            return

        past_messages = await self.fetch_user_messages(ctx, user)
        if not past_messages:
            await ctx.send(f"⚠️ No messages found for {user.display_name}.")
            return

        conversation_history = "\n".join(f"- {msg}" for msg in past_messages)

        prompt_text = f"""
        The following are messages from {user.display_name}:
        {conversation_history}

        Now, generate a response in their style to this comment: "{prompt}"
        """

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Mimic the style of the provided user messages."},
                    {"role": "user", "content": prompt_text}
                ]
            )

            simulated_response = response.choices[0].message.content.strip()
            await ctx.send(f"**{user.display_name} might say:** {simulated_response}")

        except Exception as e:
            config.logger.error(f"Error in !talkto: {e}")
            await ctx.send("⚠️ An error occurred while generating a response.")

async def setup(bot):
    await bot.add_cog(TalkSimulator(bot))
