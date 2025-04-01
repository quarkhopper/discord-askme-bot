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

    async def find_relevant_message(self, ctx, query):
        """Search the last 10 messages in the channel for a relevant message."""
        async for message in ctx.channel.history(limit=10):
            if query.lower() in message.content.lower() and message.id != ctx.message.id:
                return message.content
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

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content.strip()
            return result
        except openai.error.RateLimitError:
            print("Rate limit hit. Retrying after a delay...")
            await asyncio.sleep(10)  # Wait 10 seconds before retrying
            return await self.synthesize_reminder(input_text, context)  # Retry once
        except Exception as e:
            print(f"Error with OpenAI API: {e}")
            return None

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)  # Cooldown: 1 use per 10 seconds per user
    async def bugme(self, ctx, *, reminder: str = None):
        """Remind the user of the given message at specified intervals.

        Usage:
        `!bugme <reminder>` → Sends a DM reminder at specified intervals for a specified duration.

        Examples:
        - `!bugme remind me about the thing above with penguins`
        - `!bugme remind me that I am awesome`
        """
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("⚠️ This command can only be used in a server channel.")
            return

        if reminder is None:
            await ctx.send("⚠️ Please provide a reminder message.")
            return

        # Search for a relevant message in the channel history
        relevant_message = await self.find_relevant_message(ctx, reminder)

        # Synthesize the reminder sentence
        if relevant_message:
            synthesized_reminder = await self.synthesize_reminder(reminder, context=relevant_message)
        else:
            synthesized_reminder = await self.synthesize_reminder(f"something having to do with {reminder}")

        if not synthesized_reminder:
            await ctx.send("⚠️ I couldn't generate a reminder. Please try again.")
            return

        # Default interval and duration
        interval = 30  # Default to 30 minutes
        duration = 2  # Default to 2 hours

        user_id = ctx.author.id

        if user_id in self.active_reminders:
            await ctx.send("⚠️ You already have an active reminder. Use `!bugoff` in your DMs to stop it first.")
            return

        await ctx.send(f"✅ I'll remind you every {interval} minutes: \"{synthesized_reminder}\" for up to {duration} hours. Use `!bugoff` in your DMs to stop early.")

        self.active_reminders[user_id] = True

        try:
            total_reminders = (duration * 60) // interval  # Calculate total reminders
            for _ in range(total_reminders):
                if not self.active_reminders.get(user_id):
                    break  # Stop if the user sends "!bugoff"
                user = await self.bot.fetch_user(user_id)  # Fetch user from Discord API
                if user:
                    await user.send(f"⏰ Reminder: {synthesized_reminder}")
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
    """Load the cog into the bot."""
    await bot.add_cog(BugMe(bot))