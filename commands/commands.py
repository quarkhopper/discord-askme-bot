import discord
from discord.ext import commands
import config  # Import shared config
from commands.bot_errors import BotErrors  # Import the error handler

class CommandsHelp(commands.Cog):
    """Cog that lists all available commands."""

    def __init__(self, bot):
        self.bot = bot  # Store bot instance

    @commands.command(name="commands")
    async def list_commands(self, ctx):
        """Displays a list of available commands dynamically."""
        if await BotErrors.check_forbidden_channel(ctx):  # Use the centralized check
            return

        help_text = "**Available Commands:**\n"

        # Dynamically list all loaded commands
        for command in self.bot.commands:
            if command.help:  # Only include commands that have help text
                help_text += f"`!{command.name}` - {command.help}\n"

        await ctx.send(help_text)

async def setup(bot):
    await bot.add_cog(CommandsHelp(bot))
