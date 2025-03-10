import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
import datetime
from commands.bot_errors import BotErrors  # Import the error handler


class Catchup(commands.Cog):
    """Cog for summarizing the last 24 hours of messages across all channels."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @commands.command()
    @BotErrors.require_role("Peoples")  # Restrict to users with "Peoples" role
    async def catchup(self, ctx):
        """Summarizes activity across all channels over the past 24 hours.
        
        Usage:
        `!catchup` → Fetches and summarizes messages from the last 24 hours.
        """

        if await BotErrors.check_forbidden_channel(ctx):  # Use the centralized check
            return

        time_threshold = datetime.datetime.utcnow() - datetime.timedelta(days=1)

        # Gather messages from the last 24 hours
        recent_messages = []
        for channel in ctx.guild.text_channels:
            try:
                async for message in channel.history(after=time_threshold, limit=500):
                    recent_messages.append(f"{message.author.name}: {message.content}")
            except discord.Forbidden:
                continue  # Skip channels where the bot lacks permissions

        if not recent_messages:
            await ctx.send("No significant messages in the past 24 hours.")
            return

        # Summarize using OpenAI
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Summarize the following Discord messages from the past 24 hours."},
                    {"role": "user", "content": "\n".join(recent_messages)}
                ]
            )
            summary = response.choices[0].message.content
            await ctx.send(f"Here's what happened in the last 24 hours:\n{summary}")
        except Exception as e:
            await ctx.send(f"Error generating summary: {e}")


async def setup(bot):
    await bot.add_cog(Catchup(bot))
