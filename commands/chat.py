import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
from commands.bot_errors import BotErrors  # Import the error handler


class Chat(commands.Cog):
    """Cog for handling AI chat commands."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Initialize OpenAI client

    @commands.command()
    async def chat(self, ctx, *, message: str):
        """Talk to the bot and get AI-generated responses.
        
        Usage:
        `!chat Hello bot!` → Sends "Hello bot!" to the AI and returns a response.
        """

        
        if await BotErrors.check_forbidden_channel(ctx):  # Use the centralized check
            return

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message}]
            )

            # Extract response correctly
            reply = response.choices[0].message.content  # Correct way to access content

            await ctx.send(reply)
        except Exception as e:
            await ctx.send(f"Error: {e}")

async def setup(bot):
    await bot.add_cog(Chat(bot))
