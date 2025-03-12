import discord
from discord.ext import commands
import openai
import config
import os
import datetime
from collections import defaultdict
from commands.bot_errors import BotErrors  # Import the error handler
from commands.command_utils import command_mode
print(command_mode)

class Catchup(commands.Cog):
    """Cog for summarizing recent events across all channels or within a single channel."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @commands.command()
    @command_mode("server")
    @BotErrors.require_role("Vetted")  # Restrict to users with "Vetted" role
    async def catchup(self, ctx, channel: discord.TextChannel = None):
        """Summarizes activity across all channels or within a single specified channel.
        
        Usage:
        `!catchup` → Summarizes recent discussions across all channels, prioritizing the most critical life events.
        `!catchup #channel` → Summarizes discussions in the specified channel, grouping messages by topic.
        """

        # Prevent command execution in DMs
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        if await BotErrors.check_forbidden_channel(ctx):  # Prevents command use in #general
            return

        # Attempt to send the execution header via DM
        try:
            dm_channel = await ctx.author.create_dm()
            await dm_channel.send(
                f"📌 **Command Executed:** `!catchup`\n"
                f"📍 **Channel:** {channel.mention if channel else 'All Channels'}\n"
                f"⏳ **Timestamp:** {ctx.message.created_at}\n\n"
            )
            await ctx.message.delete()  # Delete command message after DM is sent
        except discord.Forbidden:
            await ctx.send("⚠️ Could not send a DM. Please enable DMs from server members.")
            return  # Stop execution if DM cannot be sent

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
                        {"role": "system", "content": "Summarize the following Discord messages from a single channel, ensuring that each topic grouping is meaningful and distinct. Avoid placing unrelated messages under incorrect headings."},
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
                        {"role": "system", "content": 
                            "Summarize the following Discord messages in a structured format with **four distinct categories**: \n"
                            "1) **Medical emergencies, crises, or major loss** – These should always be prioritized first. \n"
                            "2) **Deep emotional distress, relapses, or mental health struggles** – These include severe emotional challenges, recovery struggles, and urgent support needs. \n"
                            "3) **General stressors** – Cover minor frustrations, work stress, sleep issues, and common day-to-day struggles. \n"
                            "4) **Positive news and miscellaneous updates** – Include celebrations, achievements, lighthearted moments, casual discussions, and general check-ins.\n"
                            "Ensure messages are categorized correctly, and avoid placing positive updates in stressful categories."
                        },
                        {"role": "user", "content": "\n".join(formatted_messages)}
                    ]
                )
                summary = response.choices[0].message.content
                await dm_channel.send("Here's a summary of recent discussions:")
                await dm_channel.send(summary)
            except Exception as e:
                await dm_channel.send(f"Error generating summary: {e}")


async def setup(bot):
    await bot.add_cog(Catchup(bot))
