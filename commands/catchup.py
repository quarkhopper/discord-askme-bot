import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
import datetime
from collections import defaultdict
from commands.bot_errors import BotErrors  # Import the error handler


class Catchup(commands.Cog):
    """Cog for summarizing the last 24 hours of messages across all channels."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @commands.command()
    @BotErrors.require_role("Peoples")  # Restrict to users with "Peoples" role
    async def catchup(self, ctx):
        """Summarizes user activity over the past 24 hours, emphasizing major life events, emotions, and support opportunities.
        
        Usage:
        `!catchup` → Fetches and summarizes messages from the last 24 hours.
        """

        if await BotErrors.check_forbidden_channel(ctx):  # Use the centralized check
            return

        # Notify the user that the bot is working
        waiting_message = await ctx.send("Fetching messages... Please wait.")

        time_threshold = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        user_messages = defaultdict(list)
        token_limit = 12000  # Buffer to stay within OpenAI's 16,385 token limit

        # Gather messages from the last 24 hours, grouped by user
        for channel in ctx.guild.text_channels:
            try:
                async for message in channel.history(after=time_threshold, limit=500):
                    if message.author.bot:
                        continue  # Ignore bot messages
                    
                    user_messages[message.author.name].append(message.content)

            except discord.Forbidden:
                continue  # Skip channels where the bot lacks permissions

        if not user_messages:
            await waiting_message.edit(content="No significant messages in the past 24 hours.")
            return

        # Format messages for OpenAI processing
        formatted_messages = [
            f"{user}: " + " || ".join(messages) for user, messages in user_messages.items()
        ]

        # Ensure message length stays within model token limits
        def estimate_tokens(text):
            """Rough estimation of token count."""
            return len(text.split()) * 1.3  # Approx 1.3 tokens per word (varies)

        total_tokens = sum(estimate_tokens(msg) for msg in formatted_messages)
        
        # Trim messages if they exceed token limit
        while total_tokens > token_limit and len(formatted_messages) > 1:
            removed_msg = formatted_messages.pop(0)  # Remove the oldest user first
            total_tokens -= estimate_tokens(removed_msg)

        # Summarize using OpenAI
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Summarize the following Discord messages from the past 24 hours in a bullet point format, "
                            "grouping by user. Exclude trivial conversations and focus on major life events, expressions of strong emotion, "
                            "and opportunities for users to support each other. For each user, summarize their contributions in up to 5 sentences, "
                            "providing enough detail to understand their key experiences and struggles."
                        ),
                    },
                    {"role": "user", "content": "\n".join(formatted_messages)}
                ]
            )
            summary = response.choices[0].message.content

            await waiting_message.edit(content=f"Here's what happened in the last 24 hours:\n{summary}")
        except Exception as e:
            await waiting_message.edit(content=f"Error generating summary: {e}")


async def setup(bot):
    await bot.add_cog(Catchup(bot))
