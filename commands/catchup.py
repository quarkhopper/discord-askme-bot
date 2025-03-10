import discord
from discord.ext import commands
import openai
import config
import os
import datetime
from collections import defaultdict
from commands.bot_errors import BotErrors  # Import the error handler


class Catchup(commands.Cog):
    """Cog for summarizing recent events across all channels or within a single channel."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @commands.command()
    @BotErrors.require_role("Peoples")  # Restrict to users with "Peoples" role
    async def catchup(self, ctx, channel: discord.TextChannel = None, max_users: int = 10):
        """Summarizes activity across all channels or within a single specified channel.
        
        Usage:
        `!catchup` → Fetches and summarizes messages from the last 24 hours (default: top 10 users).
        `!catchup 5` → Summarizes messages for the top 5 most affected users.
        `!catchup #channel` → Summarizes recent discussions **in that channel**, grouped by topic.
        """

        if await BotErrors.check_forbidden_channel(ctx):  # Prevents command use in #general
            return

        # Notify the user that the bot is working
        waiting_message = await ctx.send("Fetching messages... Please wait.")

        time_threshold = datetime.datetime.utcnow() - datetime.timedelta(days=1)

        if channel:  # **Single-Channel Mode**
            messages = []
            try:
                async for message in channel.history(after=time_threshold, limit=200):
                    if not message.author.bot:
                        messages.append(message.content)
            except discord.Forbidden:
                await waiting_message.edit(content=f"I don’t have permission to read {channel.mention}.")
                return

            if not messages:
                await waiting_message.edit(content=f"No recent discussions found in {channel.mention}.")
                return

            # Generate a **topic-based summary** for the single channel
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Summarize the following Discord messages from a single channel, grouping discussions by topic. "
                                "Return a simple bulleted list of key topics discussed."
                            ),
                        },
                        {"role": "user", "content": "\n".join(messages)}
                    ]
                )
                summary = response.choices[0].message.content

                await waiting_message.edit(content=f"Here's what's been happening in {channel.mention}:\n{summary}")
            except Exception as e:
                await waiting_message.edit(content=f"Error generating summary: {e}")

        else:  # **All-Channels Mode (default behavior)**
            user_messages = defaultdict(list)

            for ch in ctx.guild.text_channels:
                try:
                    async for message in ch.history(after=time_threshold, limit=100):
                        if message.author.bot:
                            continue  
                        user_messages[message.author.name].append(message.content)
                except discord.Forbidden:
                    continue  

            if not user_messages:
                await waiting_message.edit(content="No significant messages in the past 24 hours.")
                return

            formatted_messages = [
                f"{user}: " + " || ".join(messages) for user, messages in user_messages.items()
            ]

            def estimate_tokens(text):
                return len(text.split()) * 1.3  

            total_tokens = sum(estimate_tokens(msg) for msg in formatted_messages)

            token_limit = 12000  
            while total_tokens > token_limit and len(formatted_messages) > 1:
                removed_msg = formatted_messages.pop(0)
                total_tokens -= estimate_tokens(removed_msg)

            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Summarize the following Discord messages from the past 24 hours in a bullet point format, "
                                "grouping by user. Prioritize users experiencing the most severe life stresses, in this order: "
                                "1) Medical emergencies, crises, or major loss should always appear first. "
                                "2) Deep emotional distress, relapses, mental health breakdowns should come next. "
                                "3) General stressors like work frustration, sleep issues, or minor emotional difficulties should appear last. "
                                f"Summarize each user’s contributions in up to 5 sentences, and limit the report to the **top {max_users} most affected users**."
                            ),
                        },
                        {"role": "user", "content": "\n".join(formatted_messages)}
                    ]
                )
                summary = response.choices[0].message.content

                max_length = 2000
                parts = [summary[i:i + max_length] for i in range(0, len(summary), max_length)]

                await waiting_message.edit(content=parts[0])
                for part in parts[1:]:
                    await ctx.send(part)

            except Exception as e:
                await waiting_message.edit(content=f"Error generating summary: {e}")


async def setup(bot):
    await bot.add_cog(Catchup(bot))
