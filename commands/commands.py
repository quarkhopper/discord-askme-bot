from discord.ext import commands
import config as config  # Import shared config

def setup(bot):
    # Define the help command
    @bot.command(name="commands")
    async def commands(ctx):
        """Displays a list of available commands."""
        if config.is_forbidden_channel(ctx):
            return
        
        help_text = "**Available Commands:**\n"
        help_text += "`!commands` - Displays this help message.\n"
        help_text += "`!chat [message]` - Talk to the bot and get AI-generated responses.\n"
        help_text += "`!image [prompt]` - Generate an image using OpenAI's DALL·E API.\n"
        help_text += "`!mood [@user]` - Analyze the mood of a user or the last 10 messages.\n"
        help_text += "`!clear` - Clears up to 100 recent messages.\n"
        help_text += "`!match [text]` - Finds a message that matches a partial string and its position in history.\n"
        help_text += "`!clearafter [text]` - Clears all messages after a matched message.\n"
        await ctx.send(help_text)
