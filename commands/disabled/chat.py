import discord
from discord.ext import commands
import openai
import os
from commands.bot_errors import BotErrors  # Import the error handler

class Chat(commands.Cog):
    """Cog for handling AI chat commands within a server."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Initialize OpenAI client

    @commands.command()
    async def chat(self, ctx, *, message: str):
        """Talk to the bot and get AI-generated responses.

        Usage:
        `!chat <message>` → Sends `<message>` to the AI bot and receives a response.

        - **Server Mode Only**: Requires the "Vetted" role and responds directly in the server channel.
        """
        # Ensure command is executed within a server
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("⚠️ This command can only be used in a server.")
            return

        # Verify the user has the "Vetted" role
        if not BotErrors.require_role("Vetted")(ctx):
            return

        # Send "Please wait..." message
        wait_message = await ctx.send("⏳ Processing... Please wait.")

        try:
            # Generate AI response
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message}]
            )

            reply = response.choices[0].message.content
            await wait_message.delete()  # Remove "Please wait..." message
            await ctx.send(reply)  # Post response in the server channel

        except Exception as e:
            await wait_message.delete()
            await ctx.send(f"⚠️ An error occurred: {e}")

async def setup(bot):
    """Load the cog into the bot."""
    await bot.add_cog(Chat(bot))

    command = bot.get_command("chat")
    if command:
        command.command_mode = "server"
