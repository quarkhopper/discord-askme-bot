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

    async def find_relevant_message(self, ctx, query):
        """Search the last 20 messages in the channel for a relevant message."""
        async for message in ctx.channel.history(limit=20):
            if message.id == ctx.message.id:
                continue  # Skip the command message itself

            # Use OpenAI to evaluate the relevance of the message
            prompt = (
                f"Determine if the following message is relevant to the user's query.\n"
                f"User's query: {query}\n"
                f"Message: {message.content}\n"
                f"Respond with 'yes' if the message is relevant, otherwise respond with 'no'."
            )

            result = await self.call_openai(prompt)
            if result and result.lower() == "yes":
                return message.content  # Return the first relevant message

        return None  # No relevant message found

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

    async def synthesize_reminder(self, input_text, context=None):
        """Use OpenAI to synthesize a reminder sentence."""
        prompt = (
            f"Create a one-sentence reminder based on the following input:\n"
            f"Input: {input_text}\n"
        )
        if context:
            prompt += f"Context: {context}\n"

        prompt += "Reminder:"

        return await self.call_openai(prompt)

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)  # Cooldown: 1 use per 10 seconds per user
    async def bugme(self, ctx, *, reminder: str = None):
        """Remind the user of the given message at specified intervals.

        Usage:
        `!bugme <reminder>` → Sends a DM reminder at specified intervals for a specified duration.

        Examples:
        - `!bugme tell me to do the dishes every 30 seconds for 10 minutes`
        - `!bugme remind me that I am awesome every 5 minutes for 1 hour`
        """
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("⚠️ This command can only be used in a server channel.")
            return

        if reminder is None:
            await ctx.send("⚠️ Please provide a reminder message.")
            return

        # Search for a relevant message in the channel history
        relevant_message = await self.find_relevant_message(ctx, reminder)

        # Parse the reminder using OpenAI
        parsed_reminder = await self.parse_reminder(reminder)
        if not parsed_reminder:
            await ctx.send("⚠️ I couldn't understand your reminder. Please try again.")
            return

        message = parsed_reminder.get("message", "Reminder")
        interval = parsed_reminder.get("interval", 1800)  # Default to 30 minutes
        duration = parsed_reminder.get("duration", 7200)  # Default to 2 hours

        # Validate interval and duration
        if not isinstance(interval, int) or interval <= 0:
            interval = 1800  # Default to 30 minutes
        if not isinstance(duration, int) or duration <= 0:
            duration = 7200  # Default to 2 hours

        # If a relevant message is found, use it as context for the synthesized reminder
        if relevant_message:
            synthesized_reminder = await self.synthesize_reminder(message, context=relevant_message)
        else:
            synthesized_reminder = await self.synthesize_reminder(message)

        if not synthesized_reminder:
            await ctx.send("⚠️ I couldn't generate a reminder. Please try again.")
            return

        user_id = ctx.author.id

        if user_id in self.active_reminders:
            await ctx.send("⚠️ You already have an active reminder. Use `!bugoff` in your DMs to stop it first.")
            return

        await ctx.send(f"✅ I'll remind you every {interval // 60} minutes: \"{synthesized_reminder}\" for up to {duration // 60} minutes. Use `!bugoff` in your DMs to stop early.")

        self.active_reminders[user_id] = True

        try:
            total_reminders = duration // interval  # Calculate total reminders
            for _ in range(total_reminders):
                if not self.active_reminders.get(user_id):
                    break  # Stop if the user sends "!bugoff"
                user = await self.bot.fetch_user(user_id)  # Fetch user from Discord API
                if user:
                    await user.send(f"⏰ Reminder: {synthesized_reminder}")
                else:
                    await ctx.send("⚠️ I couldn't find your user to send a DM.")
                    break
                await asyncio.sleep(interval)  # Wait for the specified interval
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
    """Load the cog into the bot."""
    await bot.add_cog(BugMe(bot))