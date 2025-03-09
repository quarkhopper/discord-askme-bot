import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
from commands.bot_errors import BotErrors  # Import the error handler

class DreamAnalysis(commands.Cog):
    """Cog for analyzing and interpreting dreams."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Initialize OpenAI client

    @commands.command()
    async def dream(self, ctx, *, description: str):
        """Analyze a dream and provide an interpretation.
        
        Usage:
        `!dream I was flying over the ocean` → Returns a dream interpretation.
        """
        if await BotErrors.check_forbidden_channel(ctx):  # Use the centralized check
            return

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI that analyzes and interprets dreams."},
                    {"role": "user", "content": f"Please analyze this dream and provide an interpretation:\n\n{description}"}
                ],
            )

            analysis = response.choices[0].message.content.strip()

            config.logger.info(f"Dream analyzed: {description[:50]}...")
            await ctx.send(f"💭 **Dream Interpretation:** {analysis}")

        except Exception as e:
            config.logger.error(f"Error analyzing dream: {e}")
            await ctx.send("An error occurred while analyzing the dream.")

async def setup(bot):
    await bot.add_cog(DreamAnalysis(bot))
