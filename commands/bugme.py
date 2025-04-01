import discord
from discord.ext import commands
import asyncio
import openai
import os

class BugMe(commands.Cog):
    """Cog for reminding users of a message at specified intervals."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Initialize OpenAI client
        self.active_reminders = {}
        self.openai_semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent OpenAI API calls

    async def call_openai(self, prompt):
        """Call OpenAI API with rate limiting."""
        async with self.openai_semaphore:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Error with OpenAI API: {e}")
                return None

    async def synthesize_reminder(self, input_text, context=None):
        """Use OpenAI to synthesize a reminder sentence."""
        prompt = (
            f"You are an assistant that creates concise and actionable reminders based on user input.\n"
            f"Input: {input_text}\n"
        )
        if context:
            prompt += f"Context: {context}\n"

        prompt += (
            f"Examples:\n"
            f"Input: 'remind me about the penguins'\n"
            f"Context: 'I keep having problems with penguins breaking out of my walls and I need to stop them. I need to set some traps.'\n"
            f"Reminder: 'Set traps to stop penguins from breaking out of your walls.'\n"
            f"Input: 'remind me to do the dishes'\n"
            f"Context: 'The sink is full of dirty dishes.'\n"
            f"Reminder: 'Wash the dirty dishes in the sink.'\n"
            f"Input: 'remind me to take a break'\n"
            f"Reminder: 'Take a break and relax for a few minutes.'\n"
            f"Input: {input_text}\n"
            f"Reminder:"
        )

        return await self.call_openai(prompt)

    async def parse_reminder(self, input_text):
        """Use OpenAI to parse the reminder details from freeform input."""
        prompt = (
            f"Extract the reminder details from the following input:\n"
            f"Input: {input_text}\n"
            f"Output format: {{'message': '<reminder message>', 'interval': <interval in seconds>, 'duration': <duration in seconds>}}\n"
            f"Example 1:\n"
            f"Input: 'tell me to do the dishes every 30 seconds for 10 minutes'\n"
            f"Output: {{'message': 'do the dishes', 'interval': 30, 'duration': 600}}\n"
            f"Example 2:\n"
            f"Input: 'remind me that I am awesome every 5 minutes for 1 hour'\n"
            f"Output: {{'message': 'I am awesome', 'interval': 300, 'duration': 3600}}\n"
            f"Example 3:\n"
            f"Input: 'remind me about the thing above with penguins'\n"
            f"Output: {{'message': 'the thing above with penguins', 'interval': 1800, 'duration': 7200}}\n"
            f"Example 4:\n"
            f"Input: 'remind me in an hour to feed the cat'\n"
            f"Output: {{'message': 'feed the cat', 'interval': 3600, 'duration': 3600}}\n"
            f"Input: {input_text}\n"
            f"Output:"
        )

        result = await self.call_openai(prompt)
        if result:
            try:
                return eval(result)  # Use eval cautiously; ensure OpenAI output is sanitized
            except Exception as e:
                print(f"Error parsing OpenAI response: {e}")
        return None

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)  # Cooldown: 1 use per 10 seconds per user
    async def bugme(self, ctx, *, reminder: str = None):
        """Remind the user of the given message at specified intervals.

        Usage:
        `!bugme` → Creates a reminder from the last message in the channel.
        `!bugme <reminder>` → Creates a reminder from the user's input.
        `!bugme <reminder> every <interval> for <duration>` → Custom interval and duration.
        """
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("⚠️ This command can only be used in a server channel.")
            return

        # Get the last message in the channel if no reminder is provided
        if reminder is None:
            async for message in ctx.channel.history(limit=1):
                reminder = message.content
                break

        # Parse the reminder using OpenAI
        parsed_reminder = await self.parse_reminder(reminder)
        if not parsed_reminder:
            await ctx.send("⚠️ I couldn't understand your reminder. Please try again.")
            return

        message = parsed_reminder.get("message", "Reminder")
        interval = parsed_reminder.get("interval", 1800)  # Default to 30 minutes
        duration = parsed_reminder.get("duration", interval)  # Default to 1 reminder (same as interval)

        # Validate interval and duration
        if not isinstance(interval, int) or interval <= 0:
            interval = 1800  # Default to 30 minutes
        if not isinstance(duration, int) or duration <= 0:
            duration = interval  # Default to 1 reminder (same as interval)

        # Synthesize the reminder
        synthesized_reminder = await self.synthesize_reminder(message)
        if not synthesized_reminder:
            await ctx.send("⚠️ I couldn't generate a reminder. Please try again.")
            return

        user_id = ctx.author.id

        if user_id in self.active_reminders:
            await ctx.send("⚠️ You already have an active reminder. Use `!bugoff` in your DMs to stop it first.")
            return

        # Display interval in seconds if less than 60 seconds
        interval_display = f"{interval // 60} minutes" if interval >= 60 else f"{interval} seconds"
        await ctx.send(
            f"✅ I'll remind you every {interval_display}: \"{synthesized_reminder}\" for up to {duration // 60} minutes. Use `!bugoff` in your DMs to stop early."
        )

        self.active_reminders[user_id] = True

        try:
            total_reminders = max(1, duration // interval)  # Ensure at least one reminder is sent
            await asyncio.sleep(interval)  # Wait for the first interval before sending the first reminder
            for i in range(total_reminders):
                if not self.active_reminders.get(user_id):
                    break  # Stop if the user sends "!bugoff"
                user = await self.bot.fetch_user(user_id)  # Fetch user from Discord API
                if user:
                    await user.send(f"⏰ Reminder: {synthesized_reminder}")
                else:
                    await ctx.send("⚠️ I couldn't find your user to send a DM.")
                    break
                if i < total_reminders - 1:  # Avoid sleeping after the last reminder
                    await asyncio.sleep(interval)  # Wait for the specified interval
        except discord.Forbidden:
            await ctx.send("⚠️ I can't send you DMs. Please check your privacy settings.")
        except Exception as e:
            await ctx.send(f"⚠️ An error occurred: {e}")
        finally:
            self.active_reminders.pop(user_id, None)

    @commands.command()
    async def bugoff(self, ctx):
        """Stop the active reminder."""
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
    """Load the cog into the bot."""
    await bot.add_cog(BugMe(bot))