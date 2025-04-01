import discord
from discord.ext import commands
import asyncio

class BugMe(commands.Cog):
    """Cog for reminding users of a message at specified intervals."""

    def __init__(self, bot):
        self.bot = bot
        self.active_reminders = {}

    async def parse_reminder(self, input_text):
        """Use OpenAI to parse the reminder details from freeform input."""
        prompt = (
            f"Extract the reminder details from the following input:\n"
            f"Input: {input_text}\n"
            f"Output format: {{'message': '<reminder message>', 'interval': <interval in minutes>, 'duration': <duration in hours>}}\n"
            f"Example 1:\n"
            f"Input: 'tell me to do the dishes every 20 minutes for 3 hours'\n"
            f"Output: {{'message': 'do the dishes', 'interval': 20, 'duration': 3}}\n"
            f"Example 2:\n"
            f"Input: 'remind me that I am awesome'\n"
            f"Output: {{'message': 'I am awesome', 'interval': 30, 'duration': 2}}\n"
            f"Input: {input_text}\n"
            f"Output:"
        )

        try:
            # Use the OpenAI client from the bot instance
            response = await self.bot.openai_client.Completion.acreate(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=100,
                temperature=0.7,
            )
            result = response.choices[0].text.strip()
            # Parse the result into a dictionary
            return eval(result)  # Use eval cautiously; ensure OpenAI output is sanitized
        except Exception as e:
            print(f"Error with OpenAI API: {e}")
            return None

    @commands.command()
    async def bugme(self, ctx, *, reminder: str = None):
        """Remind the user of the given message at specified intervals.

        Usage:
        `!bugme <reminder>` → Sends a DM reminder at specified intervals for a specified duration.

        Examples:
        - `!bugme tell me to do the dishes every 20 minutes for 3 hours`
        - `!bugme remind me that I am awesome`
        """
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("⚠️ This command can only be used in a server channel.")
            return

        if reminder is None:
            await ctx.send("⚠️ Please provide a reminder message.")
            return

        # Parse the reminder using OpenAI
        parsed_reminder = await self.parse_reminder(reminder)
        if not parsed_reminder:
            await ctx.send("⚠️ I couldn't understand your reminder. Please try again.")
            return

        message = parsed_reminder.get("message", "Reminder")
        interval = parsed_reminder.get("interval", 30)  # Default to 30 minutes
        duration = parsed_reminder.get("duration", 2)  # Default to 2 hours

        user_id = ctx.author.id

        if user_id in self.active_reminders:
            await ctx.send("⚠️ You already have an active reminder. Use `!bugoff` in your DMs to stop it first.")
            return

        await ctx.send(f"✅ I'll remind you every {interval} minutes: \"{message}\" for up to {duration} hours. Use `!bugoff` in your DMs to stop early.")

        self.active_reminders[user_id] = True

        try:
            total_reminders = (duration * 60) // interval  # Calculate total reminders
            for _ in range(total_reminders):
                if not self.active_reminders.get(user_id):
                    break  # Stop if the user sends "!bugoff"
                user = await self.bot.fetch_user(user_id)  # Fetch user from Discord API
                if user:
                    await user.send(f"⏰ Reminder: {message}")
                else:
                    await ctx.send("⚠️ I couldn't find your user to send a DM.")
                    break
                await asyncio.sleep(interval * 60)  # Wait for the specified interval
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