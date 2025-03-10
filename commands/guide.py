import discord
from discord.ext import commands
import openai
import os
from commands.bot_errors import BotErrors  # Import the error handler


class Guide(commands.Cog):
    """Cog for providing a server guide and welcoming new users."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @commands.command()
    @BotErrors.require_role("Peoples")  # Restrict command usage to users with the "Peoples" role
    async def guide(self, ctx):
        """Provides a dynamically generated guide to the most popular channels based on their descriptions and recent activity."""

        if await BotErrors.check_forbidden_channel(ctx):  # Prevents command use in #general
            return

        guide_message = "**Here’s a guide to the community channels!** 🏡\n\n"

        summaries = []
        for channel in ctx.guild.text_channels:
            try:
                channel_summary = channel.topic if channel.topic else f"A channel for discussions related to {channel.name.replace('-', ' ')}."

                messages = []
                async for message in channel.history(limit=50):
                    if not message.author.bot:
                        messages.append(f"{message.author.name}: {message.content}")

                if messages:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Summarize the following recent Discord messages."},
                            {"role": "user", "content": "\n".join(messages)}
                        ]
                    )
                    recent_activity = response.choices[0].message.content
                else:
                    recent_activity = "No recent activity."

                summaries.append(f"**#{channel.name}**\n📌 {channel_summary}\n🔍 *Lately, users in this channel have been discussing:* {recent_activity}\n")

            except discord.Forbidden:
                continue  

        guide_message += "\n".join(summaries)

        max_length = 2000
        parts = [guide_message[i:i + max_length] for i in range(0, len(guide_message), max_length)]

        for part in parts:
            await ctx.send(part)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Sends a fun but informative DM to new members, introducing the bot and explaining server expectations."""
        welcome_message = (
            f"**Beep boop! 🤖 Welcome, {member.name}, to {member.guild.name}!** 🎉\n\n"
            "I am your friendly server bot, here to help (and definitely not plotting world domination 🤫).\n\n"
            "To get started, you need to **check in and get the 'Peoples' role** before you can use bot commands.\n\n"
            "Once you have the 'Peoples' role, you'll be able to use helpful commands, like viewing a guide to the server channels!\n\n"
            "**Here’s a quick overview of key channels:**\n"
        )

        for channel in member.guild.text_channels:
            if len(welcome_message) > 1500:  
                break
            topic = channel.topic if channel.topic else f"A channel for discussions related to {channel.name.replace('-', ' ')}."
            welcome_message += f"**#{channel.name}** - {topic}\n"

        welcome_message += (
            "\n🔹 **First Steps:**\n"
            "✔️ Check in and get the 'Peoples' role.\n"
            "✔️ Say hi in **#general** and get to know the community!\n\n"
            "Enjoy your stay, and remember—I'm always watching. 👀 (Just kidding… or am I? 😏)"
        )

        try:
            await member.send(welcome_message)
        except discord.Forbidden:
            print(f"Could not send a DM to {member.name}.")


async def setup(bot):
    await bot.add_cog(Guide(bot))
