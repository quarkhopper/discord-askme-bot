from discord.ext import commands
import config  # Import shared config

# OpenAI client will be passed during bot setup
def setup(bot, openai_client):
    @bot.command()
    async def mood(ctx, user: commands.MemberConverter = None):
        """Analyze the mood of a specific user or the last 10 messages."""
        if config.is_forbidden_channel(ctx):
            return

        try:
            messages = []
            async for message in ctx.channel.history(limit=100):  # Search up to 100 messages to find 10 from the user
                if user is None or message.author == user:
                    messages.append(f"{message.author.display_name}: {message.content}")
                    if len(messages) >= 10:
                        break

            if not messages:
                await ctx.send("No messages found for the specified user.")
                return

            # Create a prompt for emotion analysis
            prompt = (
                "Analyze the emotions in this conversation and suggest how the participant might be feeling:\n\n" +
                "\n".join(messages) +
                "\n\nGive a concise emotional summary."
            )

            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI that analyzes emotions in conversations."},
                    {"role": "user", "content": prompt}
                ],
            )
            
            mood_analysis = response.choices[0].message.content.strip()
            config.logger.info(f"Mood analysis result: {mood_analysis}")
            await ctx.send(f"💡 Mood Analysis: {mood_analysis}")
        except Exception as e:
            config.logger.error(f"Error analyzing mood: {e}")
            await ctx.send("An error occurred while analyzing the mood.")
