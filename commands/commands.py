import discord
from discord.ext import commands
import config  # Import shared config
from commands.bot_errors import BotErrors  # Import error handling

class CommandsHelp(commands.Cog):
    """Cog that lists all available commands and their arguments."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="commands")
    @BotErrors.require_role("Vetted")  # Restrict to users with "Vetted" role
    async def list_commands(self, ctx, command_name: str = None):
        """Displays a list of available commands, or detailed help for a specific command.
        
        Usage:
        `!commands` → Lists all available commands in the bot.
        `!commands <command_name>` → Provides detailed usage for a specific command.
        """
        if await BotErrors.check_forbidden_channel(ctx):
            return

        try:
            dm_channel = await ctx.author.create_dm()
            channel_name = ctx.channel.name if isinstance(ctx.channel, discord.TextChannel) else "Direct Message"
            await dm_channel.send(
                f"**Command Executed:** commands\n**Channel:** {channel_name}\n**Timestamp:** {ctx.message.created_at}"
            )
            await ctx.message.delete()  # Delete the original command message
        except discord.Forbidden:
            await ctx.send("Could not send a DM. Please enable DMs from server members.")
            return

        if command_name:
            command = self.bot.get_command(command_name)
            if not command:
                await dm_channel.send(f"⚠️ No command named `{command_name}` found.")
                return

            usage = f"**`!{command.name}`**\n"
            if command.help:
                usage += f"{command.help}\n"

            params = [f"<{param}>" for param in command.clean_params]
            if params:
                usage += f"**Usage:** `!{command.name} {' '.join(params)}`\n"

            await dm_channel.send(usage)
            return

        commands_list = sorted(self.bot.commands, key=lambda c: c.name)
        help_text = "**Available Commands (A-Z):**\n"

        for command in commands_list:
            if command.help:
                help_text += f"🔹 **`!{command.name}`** - {command.help.splitlines()[0]}\n"

        await dm_channel.send(help_text)

async def setup(bot):
    await bot.add_cog(CommandsHelp(bot))
