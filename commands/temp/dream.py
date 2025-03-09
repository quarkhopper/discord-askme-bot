from discord.ext import commands
import config  # Import shared config

def setup(bot, openai_client):  # Add openai_client as an argument
    @bot.command()
    async def dream(ctx, *, description: str):
        """Analyze a dream and provide an interpretation."""
        if config.is_forbidden_channel(ctx):
            return
        
        try:
            response = openai_client.chat.completions.create(
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
