import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
from commands.bot_errors import BotErrors  # Import the error handler


class Catchup(commands.Cog):
    """Cog for summarizing recent events since the user's last message."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @commands.command()
    @BotErrors.require_role("Peoples")  # Restrict to users with "Peoples" role
    async def catchup(self, ctx):
        """Summarizes activity across all channels since the user's last message.
        
        Usage:
        `!catchup` → Fetches messages since the last time the user posted.
        """

        if await BotErrors.check_forbidden_channel(ctx):  # Use the centralized check
            return

        user_id = ctx.author.id
        bot_id = self.bot.user.id
        last_message_time = None

        # Find the user's last message in any channel
        for channel in ctx.guild.text_channels:
            try:
                async for message in channel.history(limit=100):  # Fetch last 100 messages per channel
                    if message.author.id == user_id:
                        last_message_time = message.created_at
                        break
                if last_message_time:
                    break
            except discord.Forbidden:
                continue  # Skip channels where the bot lacks permissions

        if not last_message_time:
            await ctx.send("I couldn't find any of your past messages.")
            return

        # Gather messages since the last user's message
        recent_messages = []
        for channel in ctx.guild.text_channels:
            try:
                async for message in channel.history(after=last_message_time, limit=100):
                    if message.author.id == user_id:  
                        continue  # Ignore user's own messages
                    
                    if message.author.id == bot_id:  
                        continue  # Ignore bot's own messages
                    
                    if self.bot.user.mentioned_in(message):  
                        continue  # Ignore messages mentioning the bot
                    
                    if message.content.startswith(ctx.prefix):  
                        continue  # Ignore command messages

                    recent_messages.append(f"{message.author.name}: {message.content}")
            except discord.Forbidden:
                continue  # Skip channels where the bot lacks permissions

        if not recent_messages:
            await ctx.send("No new messages since your last post.")
            return

        # Summarize using OpenAI
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Summarize the following Discord messages."},
                    {"role": "user", "content": "\n".join(recent_messages)}
                ]
            )
            summary = response.choices[0].message.content
            await ctx.send(f"Here's what you missed:\n{summary}")
        except Exception as e:
            await ctx.send(f"Error generating summary: {e}")


async def setup(bot):
    await bot.add_cog(Catchup(bot))
