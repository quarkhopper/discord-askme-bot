import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
import re
from commands.bot_errors import BotErrors  # Import the error handler

class PlanLife(commands.Cog):
    """Cog for generating an exaggerated but semi-realistic lifelong mission based on recent messages."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Initialize OpenAI client

    async def fetch_user_messages(self, ctx, user: discord.Member, channel: discord.TextChannel, limit=10):
        """Fetch the last `limit` messages from the user in the specified channel."""
        messages = []
        async for message in channel.history(limit=100):
            if message.author == user and not message.content.startswith("!"):
                messages.append(message.content)
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
        """Tries to resolve a user by mention, name, or ID (Copied from planhour.py)."""
        member = None
        user_id = self.extract_id(identifier)

        if user_id:
            member = ctx.guild.get_member(user_id)  # Fast lookup in cache
            if not member:  # If not found in cache, fetch from Discord
                try:
                    member = await ctx.bot.fetch_user(user_id)
                except discord.NotFound:
                    return None
        else:
            member = discord.utils.get(ctx.guild.members, name=identifier)

        return member

    async def resolve_channel(self, ctx, identifier):
        """Tries to resolve a channel by mention, name, or ID."""
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
    @BotErrors.require_role("Peoples")  # Restrict to users with "Peoples" role
    async def planlife(self, ctx, *args):
        """Generates a wildly exaggerated but somewhat realistic lifelong mission based on recent messages.

        Usage:
        `!planlife` → Generates a plan based on **your** recent messages in the current channel.
        `!planlife @User` → Generates a plan based on **@User's** messages in the current channel.
        `!planlife #general` → Generates a plan based on recent messages in **#general**.
        `!planlife @User #general` → Generates a plan for **@User's** messages in **#general**.
        """
        if await BotErrors.check_forbidden_channel(ctx):  # Use the centralized check
            return

        user = ctx.author  # Default to executing user
        channel = ctx.channel  # Default to current channel

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

        messages = await self.fetch_user_messages(ctx, user=user, channel=channel)
        if not messages:
            await ctx.send(f"No recent messages found for {user.display_name} in {channel.mention}.")
            return

        prompt = f"Based on these recent activities: {messages}, create a wildly exaggerated but somewhat realistic lifelong mission."

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a witty AI that humorously extends a user's recent activities into an exaggerated but semi-realistic lifelong mission."},
                    {"role": "user", "content": prompt}
                ],
            )

            mission = response.choices[0].message.content.strip()
            await ctx.send(f"🌟 **Your Lifelong Mission:**\n{mission}")

        except Exception as e:
            config.logger.error(f"Error generating planlife: {e}")
            await ctx.send("An error occurred while planning your lifelong mission.")

async def setup(bot):
    await bot.add_cog(PlanLife(bot))
