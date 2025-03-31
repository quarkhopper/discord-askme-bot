import discord
from discord.ext import commands, tasks
import asyncio

class BugMe(commands.Cog):
    """Cog for reminding users of a message every 10 minutes."""

    def __init__(self, bot):
        self.bot = bot
        self.active_reminders = {}

    @commands.command()
    async def bugme(self, ctx, *, reminder: str = None):
        """Remind the user of the given message every 10 minutes via DM for up to 1 hour.

        Usage:
        `!bugme <reminder>` → Sends a DM reminder every 10 minutes for up to 1 hour.

        - **Server Mode Only**: This command can only be used in a server channel.
        """
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("⚠️ This command can only be used in a server channel.")
            return

        if reminder is None:
            # Fetch the last message in the channel if no argument is provided
            async for msg in ctx.channel.history(limit=2):
                if msg.id != ctx.message.id:  # Skip the command message itself
                    reminder = msg.content
                    break

            if not reminder:  # If no valid message is found
                await ctx.send("⚠️ Couldn't find a previous message to use as a reminder.")
                return

        user_id = ctx.author.id

        if user_id in self.active_reminders:
            await ctx.send("⚠️ You already have an active reminder. Use `!bugoff` in your DMs to stop it first.")
            return

        await ctx.send(f"✅ I'll remind you every 10 minutes: \"{reminder}\" for up to 1 hour. Use `!bugoff` in your DMs to stop early.")

        self.active_reminders[user_id] = True

        try:
            for _ in range(6):  # Limit to 6 reminders (1 hour)
                if not self.active_reminders.get(user_id):
                    break  # Stop if the user sends "!bugoff"
                user = await self.bot.fetch_user(user_id)  # Fetch user from Discord API
                if user:
                    await user.send(f"⏰ Reminder: {reminder}")
                else:
                    await ctx.send("⚠️ I couldn't find your user to send a DM.")
                    break
                await asyncio.sleep(600)  # Wait for 10 minutes
        except discord.Forbidden:
            await ctx.send("⚠️ I can't send you DMs. Please check your privacy settings.")
        except Exception as e:
            await ctx.send(f"⚠️ An error occurred: {e}")
        finally:
            self.active_reminders.pop(user_id, None)

    @commands.command()
    async def bugoff(self, ctx):
        """Stop the active reminder.

        Usage:
        `!bugoff` → Stops the current reminder. Must be used in DMs with the bot.
        """
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("⚠️ This command can only be used in DMs with the bot.")
            return

        user_id = ctx.author.id

        if user_id not in self.active_reminders:
            await ctx.send("⚠️ You don't have any active reminders.")
            return

        self.active_reminders.pop(user_id, None)
        await ctx.send("✅ Your reminder has been stopped.")

async def setup(bot):
    await bot.add_cog(BugMe(bot))

    command = bot.get_command("bugme")
    if command:
        command.command_mode = "server"