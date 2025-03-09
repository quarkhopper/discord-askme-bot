from discord.ext import commands
import openai
import config  # Import shared config

def setup(bot):
    @bot.command()
    async def chat(ctx, *, message: str):
        """Talk to the bot and get AI-generated responses."""
        if config.is_forbidden_channel(ctx):
            return

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message}],
            )
            reply = response["choices"][0]["message"]["content"].strip()
            config.logger.info(f"Chat response generated for: {message}")
            await ctx.send(reply)
        except Exception as e:
            config.logger.error(f"Error generating chat response: {e}")
            await ctx.send("An error occurred while processing your request.")
