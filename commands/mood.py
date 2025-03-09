import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os

class MoodAnalyzer(commands.Cog):
    """Cog for analyzing the mood of a user or recent messages in a channel."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Initialize OpenAI client

    async def fetch_messages(self, ctx, user: discord.Member = None, channel: discord.TextChannel = None, limit=10):
        """Fetch the last `limit` messages from a specific user in the given channel."""
        if channel is None:
            channel = ctx.channel  # Default to the current channel
        
        messages = []
        async for message in channel.history(limit=100):  # Search up to 100 messages for context
            if user is None or message.author == user:
                messages.append(f"{message.author.display_name}: {message.content}")
                if len(messages) >= limit:
                    break

        return messages

    @commands.command()
    async def mood(self, ctx, user: discord.Member = None, channel: discord.TextChannel = None):
        """Analyze the mood of a specific user or the last 10 messages in the specified channel."""
        if config.is_forbidden_channel(ctx):
            return

        messages = await self.fetch_messages(ctx, user=user, channel=channel)
        if not messages:
            await ctx.send("No messages found for the specified user or channel.")
            return

        prompt = (
            "Analyze the emotions in this conversation and suggest how the participant might be feeling:\n\n" +
            "\n".join(messages) +
            "\n\nGive a concise emotional summary."
        )

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI that analyzes emotions in conversations."},
                    {"role": "user", "content": prompt}
                ],
            )
            
            mood_analysis = response.choices[0].message.content.strip()
            config.logger.info(f"Mood analysis result: {mood_analysis}")
            await ctx.send(f"💡 Mood Analysis: {mood_analysis}")

        except Exception as e:
            config.logger.error(f"Error analyzing mood: {e}")
            await ctx.send("An error occurred while analyzing the mood.")

async def setup(bot):
    await bot.add_cog(MoodAnalyzer(bot))
