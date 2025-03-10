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
        `!catchup` → Summarizes recent discussions across all channels, prioritizing the most critical life events.
        `!catchup #channel` → Summarizes discussions in the specified channel, grouping messages by topic.
        """

        if await BotErrors.check_forbidden_channel(ctx):  # Prevents command use in #general
            return

        try:
            dm_channel = await ctx.author.create_dm()
            await dm_channel.send(
                f"**Command Executed:** catchup\n**Channel:** {channel.mention if channel else 'All Channels'}\n**Timestamp:** {ctx.message.created_at}"
            )
        except discord.Forbidden:
            await ctx.send("Could not send a DM. Please enable DMs from server members.")
            return

        waiting_message = await ctx.send("Fetching messages... Please wait.")
        time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)

        if channel:
            messages = []
            try:
                async for message in channel.history(after=time_threshold, limit=200):
                    if not message.author.bot:
                        messages.append(message.content)
            except discord.Forbidden:
                await dm_channel.send(f"I don’t have permission to read {channel.mention}.")
                return

            if not messages:
                await dm_channel.send(f"No recent discussions found in {channel.mention}.")
                return

            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Summarize the following Discord messages from a single channel, grouping discussions by topic in bullet points."},
                        {"role": "user", "content": "\n".join(messages)}
                    ]
                )
                summary = response.choices[0].message.content
                await dm_channel.send(f"Here's what's been happening in {channel.mention}:\n\n{summary}")
            except Exception as e:
                await dm_channel.send(f"Error generating summary: {e}")
        else:
            user_messages = defaultdict(list)
            for ch in ctx.guild.text_channels:
                try:
                    async for message in ch.history(after=time_threshold, limit=100):
                        if message.author.bot:
                            continue  
                        user_messages[message.author.display_name].append(message.content)
                except discord.Forbidden:
                    continue  

            if not user_messages:
                await dm_channel.send("No significant messages in the past 24 hours.")
                return

            formatted_messages = [f"{user}: " + " || ".join(messages) for user, messages in user_messages.items()]
            token_limit = 12000  
            while sum(len(msg.split()) for msg in formatted_messages) > token_limit and len(formatted_messages) > 1:
                formatted_messages.pop(0)

            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Summarize the following Discord messages in a bullet point format, grouping by user. Prioritize users experiencing the most severe life stresses, in this order: \n1) Medical emergencies, crises, or major loss should always appear first. \n2) Deep emotional distress, relapses, mental health breakdowns should come next. \n3) General stressors like work frustration, sleep issues, or minor emotional difficulties should appear last. \nSummarize each user’s contributions in up to 5 sentences, and limit the report to the **top {max_users} most affected users**. Each user’s summary should appear as a single bullet point."},
                        {"role": "user", "content": "\n".join(formatted_messages)}
                    ]
                )
                summary = response.choices[0].message.content
                await dm_channel.send("Here's a summary of recent discussions:")
                await dm_channel.send(summary)
            except Exception as e:
                await dm_channel.send(f"Error generating summary: {e}")
        
        await ctx.message.delete()
        await waiting_message.delete()


async def setup(bot):
    await bot.add_cog(Catchup(bot))
