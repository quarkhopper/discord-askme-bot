import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
from commands.bot_errors import BotErrors  # Import the error handler

class ImageGen(commands.Cog):
    """Cog for generating images using OpenAI's DALL·E API."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Initialize OpenAI client

    @commands.command()
    async def image(self, ctx, *, prompt: str):
        """Generate an image using OpenAI's DALL·E API."""
        if await BotErrors.check_forbidden_channel(ctx):  # Use the centralized check
            return

        try:
            response = self.openai_client.images.generate(
                prompt=prompt,
                n=1,
                size="1024x1024"
            )

            # Correctly access the generated image URL
            image_url = response.data[0].url  

            config.logger.info(f"Generated image for prompt: {prompt}")
            await ctx.send(image_url)

        except Exception as e:
            config.logger.error(f"Error generating image: {e}")
            await ctx.send("An error occurred while generating the image.")

async def setup(bot):
    await bot.add_cog(ImageGen(bot))
