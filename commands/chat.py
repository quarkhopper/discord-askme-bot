import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
from commands.bot_errors import BotErrors  # Import the error handler
from commands.command_utils import command_mode

class Chat(commands.Cog):
    """Cog for handling AI chat commands."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Initialize OpenAI client

    @command_mode("both")
    @commands.command()
    async def chat(self, ctx, *, message: str):
        """Talk to the bot and get AI-generated responses.
        
        Usage:
        `!chat <message>` → Sends `<message>` to the AI bot and receives a response.
        
        - **DM Mode**: The bot will respond in a private message. No role restrictions apply.
        - **Server Mode**: Requires the "Vetted" role. The bot will send results via DM and ensure the user is in the same server.
        """
        is_dm = isinstance(ctx.channel, discord.DMChannel)

        # Server mode: enforce role restriction and check server membership
        if not is_dm:
            if not BotErrors.require_role("Vetted")(ctx):
                return
            try:
                member = ctx.guild.get_member(ctx.author.id) or await ctx.guild.fetch_member(ctx.author.id)
                if not member:
                    await ctx.send("You must be a member of the same Discord server as the bot to use this command.")
                    return
            except discord.NotFound:
                await ctx.send("You must be a member of the same Discord server as the bot to use this command.")
                return
            except Exception:
                await ctx.send("An error occurred while verifying your membership.")
                return

        # Attempt to send the execution header via DM
        try:
            dm_channel = await ctx.author.create_dm()
            await dm_channel.send(
                f"📌 **Command Executed:** `!chat`\n"
                f"📍 **Channel:** {'Direct Message' if is_dm else ctx.channel.name}\n"
                f"⏳ **Timestamp:** {ctx.message.created_at}\n\n"
            )
            if not is_dm:
                await ctx.message.delete()  # Delete the original command message in server mode
        except discord.Forbidden:
            if not is_dm:
                await ctx.send("⚠️ Could not send a DM. Please enable DMs from server members.")
            return  # Stop execution if DM cannot be sent

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message}]
            )

            reply = response.choices[0].message.content
            await dm_channel.send(reply)
        except Exception as e:
            await dm_channel.send(f"Error: {e}")


async def setup(bot):
    await bot.add_cog(Chat(bot))
