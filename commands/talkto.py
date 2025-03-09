import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
import re  # Regex for extracting IDs
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize
from commands.bot_errors import BotErrors  # Error handler

nltk.download('punkt')  # Ensure tokenization support

class TalkSimulator(commands.Cog):
    """Cog for simulating how a user might respond based on past messages."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def fetch_user_messages(self, ctx, user: discord.Member, limit=10):
        """Fetch the last `limit` messages from the specified user across all channels."""
        messages = []
        for channel in ctx.guild.text_channels:
            if not channel.permissions_for(ctx.guild.me).read_messages:
                continue  # Skip channels the bot can't read
            
            try:
                async for message in channel.history(limit=100):  # Fetch more for filtering
                    if message.author == user:
                        messages.append(message.content)
                        if len(messages) >= limit:
                            return messages
            except discord.Forbidden:
                continue  # Skip channels with permission issues
        return messages

    def extract_topics_and_vocab(self, messages):
        """Extracts frequently used words and topics from user messages."""
        text = " ".join(messages)
        words = word_tokenize(text.lower())  # Tokenize and normalize case
        common_words = Counter(words).most_common(50)  # Get top 50 words

        # Prioritize these words, but don't make them absolute restrictions
        vocabulary = {word for word, count in common_words if word.isalnum()}
        topics = {word for word, count in common_words if count > 1 and len(word) > 3}

        return topics, vocabulary

    async def resolve_member(self, ctx, identifier):
        """Resolves a user by mention, name, or ID."""
        match = re.match(r"<@!?(\d+)>", identifier)
        user_id = int(match.group(1)) if match else None
        if user_id:
            return ctx.guild.get_member(user_id) or await self.bot.fetch_user(user_id)
        return discord.utils.get(ctx.guild.members, name=identifier)

    @commands.command()
    @BotErrors.require_role("Peoples")  # Ensure only authorized roles can use it
    async def talkto(self, ctx, user_mention: str, *, prompt: str):
        """Simulates a user's response based on their last 10 messages, using their vocabulary while allowing flexibility.

        Usage:
        `!talkto @User What do you think about AI?`
        """
        if config.is_forbidden_channel(ctx):
            return
        
        user = await self.resolve_member(ctx, user_mention)
        if not user:
            await ctx.send(f"⚠️ Could not find a user matching `{user_mention}`.")
            return

        waiting_message = await ctx.send(f"⏳ Please wait, generating a response for {user.display_name}...")

        try:
            past_messages = await self.fetch_user_messages(ctx, user)
            if not past_messages:
                await waiting_message.edit(content=f"⚠️ No messages found for {user.display_name}.")
                return

            topics, vocabulary = self.extract_topics_and_vocab(past_messages)

            # Encourage AI to stick to these subjects, but allow flexibility
            relevant_prompt = (
                f"Prioritize responding in a way related to these topics: {', '.join(topics)}. "
                "However, if needed, you may use additional words to make the response understandable."
            )
            vocabulary_hint = (
                f"Try to use words from this set: {', '.join(vocabulary)}, "
                "but you are allowed to use other words if necessary for fluency."
            )

            conversation_history = "\n".join(f"- {msg}" for msg in past_messages)

            prompt_text = f"""
            The following are messages from {user.display_name}:
            {conversation_history}

            {relevant_prompt}
            {vocabulary_hint}
            You are allowed to use metaphors, but they must be relevant to the user’s way of speaking.

            Now, generate a response in their style to this comment: "{prompt}"
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Mimic the style of the provided user messages."},
                    {"role": "user", "content": prompt_text}
                ]
            )

            simulated_response = response.choices[0].message.content.strip()
            await waiting_message.edit(content=f"**{user.display_name} might say:** {simulated_response}")

        except Exception as e:
            config.logger.error(f"Error in !talkto: {e}")
            await waiting_message.edit(content="⚠️ An error occurred while generating a response.")

async def setup(bot):
    await bot.add_cog(TalkSimulator(bot))
