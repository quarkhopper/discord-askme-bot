import discord
from discord.ext import commands
import config  # Import shared config
from commands.bot_errors import BotErrors  # Import error handling
from commands.command_utils import command_mode

class CommandsHelp(commands.Cog):
    """Cog that lists all available commands and their arguments."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="commands")
    @command_mode("both")  # Available in both DM and Server Mode
    @BotErrors.require_role("Vetted")  # Restrict to users with "Vetted" role
    async def list_commands(self, ctx, command_name: str = None):
        """Displays a list of available commands, or detailed help for a specific command.

        Usage:
        `!commands` → Lists all available commands in the bot.
        `!commands <command_name>` → Provides detailed usage for a specific command.
        """
        if await BotErrors.check_forbidden_channel(ctx):
            return

        # Determine execution mode
        is_dm = isinstance(ctx.channel, discord.DMChannel)
        mode_filter = "dm" if is_dm else "server"

        # If a command name is provided, display details for that command
        if command_name:
            command = self.bot.get_command(command_name)
            if not command:
                await ctx.send(f"⚠️ No command named `{command_name}` found.")  # Exception: Allow this to display in server
                return

            # Ensure command matches the correct mode
            if hasattr(command, "command_mode") and command.command_mode not in ["both", mode_filter]:
                await ctx.send(f"⚠️ The command `!{command_name}` is not available in this mode.")  # Exception: Allow in server
                return

            usage = f"**`!{command.name}`**\n"
            if command.help:
                usage += f"{command.help}\n"

            params = [f"<{param}>" for param in command.clean_params]
            if params:
                usage += f"**Usage:** `!{command.name} {' '.join(params)}`\n"

            await ctx.send(usage)  # Exception: Display directly in server
            return

        # Filter commands by mode
        commands_list = sorted(
            [cmd for cmd in self.bot.commands if hasattr(cmd, "command_mode") and cmd.command_mode in ["both", mode_filter]],
            key=lambda c: c.name
        )

        help_text = "**Available Commands:**\n"

        for command in commands_list:
            if command.help:
                help_text += f"🔹 **`!{command.name}`** - {command.help.splitlines()[0]}\n"

        await ctx.send(help_text)  # Exception: Display directly in server

async def setup(bot):
    await bot.add_cog(CommandsHelp(bot))
