import discord
from discord.ext import commands
import openai
import os
from commands.bot_errors import BotErrors

class Egg(commands.Cog):
    """Cog for handling egg-obsessed AI chat responses."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @commands.command()
    async def egg(self, ctx, *, message: str):
        """Talk to the eggbot. Everything leads back to eggs.

        Usage:
        `!egg <message>` → Responds with egg metaphors and excitement.

        - **Server Mode Only**: Requires the "Vetted" role.
        """
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("🥚 This command can only be used in a server.")
            return

        if not BotErrors.require_role("Vetted")(ctx):
            return

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        wait_message = await ctx.send("🥚 Hatching your response...")

        try:
            prompt = (
                f"You are an AI who is absolutely obsessed with eggs. "
                f"Every answer should use egg metaphors, make egg puns, or redirect the conversation toward eggs. "
                f"If the user talks about eggs, you get very excited. "
                f"Be enthusiastic, silly, and clever. Here's what the user said:\n\n{message}"
            )

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )

            reply = response.choices[0].message.content
            await wait_message.delete()
            await ctx.send(reply)

        except Exception as e:
            await wait_message.delete()
            await ctx.send(f"⚠️ An error occurred while cracking the egg: {e}")

async def setup(bot):
    await bot.add_cog(Egg(bot))

    command = bot.get_command("egg")
    if command:
        command.command_mode = "server"
