import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
from commands.bot_errors import BotErrors  # Import the error handler
from commands.command_utils import command_mode

class ImageGen(commands.Cog):
    """Cog for generating images using OpenAI's DALL·E API."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Initialize OpenAI client

    @commands.command()
    @command_mode("both")
    @BotErrors.require_role("Vetted")  # ✅ Enforce correct role
    async def image(self, ctx, *, prompt: str):
        """Generate an image using OpenAI's DALL·E API.
        
        Usage:
        `!image a futuristic city at sunset` → Generates an image of a futuristic city at sunset.
        """
        is_dm = isinstance(ctx.channel, discord.DMChannel)

        if not is_dm and await BotErrors.check_forbidden_channel(ctx):  # Prevents execution in forbidden channels
            return

        # Attempt to send the execution header via DM
        try:
            dm_channel = await ctx.author.create_dm()
            await dm_channel.send(
                f"📌 **Command Executed:** `!image`\n"
                f"📍 **Channel:** {'Direct Message' if is_dm else ctx.channel.name}\n"  # ✅ Fixes AttributeError
                f"⏳ **Timestamp:** {ctx.message.created_at}\n\n"
                f"🎨 **Generating an image for prompt:** `{prompt}`"
            )
            if not is_dm:
                await ctx.message.delete()  # Delete the command message in server mode
        except discord.Forbidden:
            if not is_dm:
                await ctx.send("⚠️ Could not send a DM. Please enable DMs from server members.")
            return  # Stop execution if DM cannot be sent

        try:
            response = self.openai_client.images.generate(
                prompt=prompt,
                n=1,
                size="1024x1024"
            )

            # Access the generated image URL
            image_url = response.data[0].url  

            config.logger.info(f"Generated image for prompt: {prompt}")

            # Send the image link via DM
            await dm_channel.send(f"🖼 **Here is your generated image:**\n{image_url}")

        except Exception as e:
            config.logger.error(f"Error generating image: {e}")
            await dm_channel.send("An error occurred while generating the image.")

async def setup(bot):
    await bot.add_cog(ImageGen(bot))
