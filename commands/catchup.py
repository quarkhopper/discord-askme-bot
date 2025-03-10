import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
import datetime
import re
from commands.bot_errors import BotErrors  # Import the error handler


class Catchup(commands.Cog):
    """Cog for summarizing the last 24 hours of messages across all channels."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @commands.command()
    @BotErrors.require_role("Peoples")  # Restrict to users with "Peoples" role
    async def catchup(self, ctx):
        """Summarizes activity across all channels over the past 24 hours, prioritizing major life events.
        
        Usage:
        `!catchup` → Fetches and summarizes messages from the last 24 hours.
        """

        if await BotErrors.check_forbidden_channel(ctx):  # Use the centralized check
            return

        # Notify the user that the bot is working
        waiting_message = await ctx.send("Fetching messages... Please wait.")

        time_threshold = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        recent_messages = []
        mentioned_users = set()
        token_limit = 12000  # Keep a buffer to avoid hitting 16,385 tokens

        # Gather messages from the last 24 hours
        for channel in ctx.guild.text_channels:
            try:
                async for message in channel.history(after=time_threshold, limit=500):
                    msg_text = f"{message.author.name}: {message.content}"
                    recent_messages.append(msg_text)

                    # Track mentioned users
                    mentions = re.findall(r"@(\w+)", message.content)
                    mentioned_users.update(mentions)

            except discord.Forbidden:
                continue  # Skip channels where the bot lacks permissions

        if not recent_messages:
            await waiting_message.edit(content="No significant messages in the past 24 hours.")
            return

        # Ensure message length stays within model token limits
        def estimate_tokens(text):
            """Rough estimation of token count."""
            return len(text.split()) * 1.3  # Approx 1.3 tokens per word (varies)

        total_tokens = sum(estimate_tokens(msg) for msg in recent_messages)
        
        # Trim messages if they exceed token limit
        while total_tokens > token_limit and len(recent_messages) > 1:
            removed_msg = recent_messages.pop(0)  # Remove the oldest message first
            total_tokens -= estimate_tokens(removed_msg)

        # Summarize using OpenAI
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Summarize the following Discord messages from the past 24 hours. "
                            "Prioritize major life events and crises such as medical emergencies, relapses, "
                            "job loss, and significant stress. "
                            "List these separately, including who shared them and a short summary of what happened. "
                            "Also, provide a general summary of discussions. "
                            "Finally, provide a list of users who were mentioned in messages, to help ensure "
                            "the community knows who was talked about and may need support."
                        ),
                    },
                    {"role": "user", "content": "\n".join(recent_messages)}
                ]
            )
            summary = response.choices[0].message.content

            # Add mentioned users to the summary
            if mentioned_users:
                summary += "\n\n**Users Mentioned:**\n" + "\n".join(f"- {user}" for user in mentioned_users)

            await waiting_message.edit(content=f"Here's what happened in the last 24 hours:\n{summary}")
        except Exception as e:
            await waiting_message.edit(content=f"Error generating summary: {e}")


async def setup(bot):
    await bot.add_cog(Catchup(bot))
