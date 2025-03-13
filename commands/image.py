import discord
from discord.ext import commands
import openai
import os
import asyncio

class ImageGen(commands.Cog):
    """Cog for generating images using OpenAI's DALL·E API."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.lock = asyncio.Lock()  # Prevents multiple API calls at once

    @commands.command()
    async def image(self, ctx, *, prompt: str):
        """Generate an image using OpenAI's DALL·E API.
        
        Usage:
        `!image a futuristic city at sunset` → Generates an image of a futuristic city at sunset.
        """

        is_dm = isinstance(ctx.channel, discord.DMChannel)

        # Enforce role restriction in server mode
        if not is_dm:
            role = discord.utils.get(ctx.author.roles, name="Vetted")
            if not role:
                await ctx.send("⚠️ You must have the 'Vetted' role to use this command.")
                return

        # Acknowledge command execution
        please_wait = await ctx.send(f"⏳ Generating an image for: `{prompt}`. Please wait...")

        # Delete the original command message in server mode
        if not is_dm:
            try:
                await ctx.message.delete()
            except discord.NotFound:
                pass  # Message already deleted

        # Generate image using OpenAI API
        async with self.lock:
            try:
                response = await self.openai_client.images.generate(
                    prompt=prompt,
                    n=1,
                    size="1024x1024"
                )
                image_url = response.data[0].url  # Extract generated image URL
            except Exception as e:
                print(f"[ImageGen] OpenAI API error: {e}")
                await please_wait.delete()
                await ctx.send("⚠️ An error occurred while generating the image.")
                return

        # Delete "Please wait..." message
        await please_wait.delete()

        # Create an embed to display the image without showing the URL
        embed = discord.Embed(title="🖼 Generated Image", description=f"Prompt: `{prompt}`", color=discord.Color.blue())
        embed.set_image(url=image_url)

        # Send the embedded image
        await ctx.send(embed=embed)

# ✅ Set this command to work in both server and DM mode
async def setup(bot):
    await bot.add_cog(ImageGen(bot))
    command = bot.get_command("image")
    if command:
        command.command_mode = "both"
