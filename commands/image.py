from discord.ext import commands
import openai
import config  # Import shared config

def setup(bot):
    @bot.command()
    async def image(ctx, *, prompt: str):
        """Generate an image using OpenAI's DALL·E API"""
        if config.is_forbidden_channel(ctx):
            return
        
        try:
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            image_url = response["data"][0]["url"]
            config.logger.info(f"Generated image for prompt: {prompt}")
            await ctx.send(image_url)
        except Exception as e:
            config.logger.error(f"Error generating image: {e}")
            await ctx.send("An error occurred while generating the image.")
