import discord
from discord.ext import commands
import config  # Import shared config

class CommandsHelp(commands.Cog):
    """Cog that lists all available commands and their arguments."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="commands")
    async def list_commands(self, ctx, command_name: str = None):
        """Displays a list of available commands, or detailed help for a specific command.

        Usage:
        `!commands` → Shows a list of available commands in alphabetical order.
        `!commands <command>` → Shows detailed usage for a specific command.
        """
        if config.is_forbidden_channel(ctx):
            return

        if command_name:
            # ✅ Show detailed help for a specific command
            command = self.bot.get_command(command_name)
            if not command:
                await ctx.send(f"⚠️ No command named `{command_name}` found.")
                return

            usage = f"**`!{command.name}`**\n"
            if command.help:
                usage += f"{command.help}\n"

            params = [f"<{param}>" for param in command.clean_params]
            if params:
                usage += f"**Usage:** `!{command.name} {' '.join(params)}`\n"

            await ctx.send(usage)
            return

        # ✅ Show general command list (sorted alphabetically)
        commands_list = sorted(self.bot.commands, key=lambda c: c.name)  # Sort by command name
        help_text = "**Available Commands (A-Z):**\n"

        for command in commands_list:
            if command.help:
                help_text += f"🔹 **`!{command.name}`** - {command.help.splitlines()[0]}\n"

        await ctx.send(help_text)

async def setup(bot):
    await bot.add_cog(CommandsHelp(bot))
