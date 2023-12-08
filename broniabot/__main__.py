import sys
import time
from os import getenv
from pathlib import Path

import discord
from discord.ext.commands import Bot
from dotenv import load_dotenv

load_dotenv()
from broniabot.httpserver import quart

# Intents
intents = discord.Intents.default()
intents.members = True


# Bot base
class BroniaBot(Bot):
    def __init__(self):
        super().__init__(
            intents=intents,
            command_prefix="!",
        )

        # Version
        self.bot_version = "1.0"

        # Modules
        self.modules = [
            "events.join_verify"
        ]

        # Config
        self.config = {
            "guild_id": int(getenv("GUILD_ID")),
            "verified_role_id": int(getenv("VERIFIED_ROLE_ID")),
        }


bot = BroniaBot()


@bot.event
async def on_ready():
    bot.loop.create_task(quart.run_task())
    print(f"* Logged in {bot.user.name}#{bot.user.discriminator}!")
    await bot.wait_until_ready()
    bot.bot_start_time = time.time()
    print("* Internal cache ready!")

    print("* Started status loop")

    print("* Loading modules...")
    for module in bot.modules:
        print(f"     - Loading {module}")
        await bot.load_extension(module)
        print(f"     - Loaded {module}")
    print("* Loaded modules")

    await bot.tree.sync(guild=discord.Object(id=bot.config.get("guild_id")))
    print("* Synced tree")
    print(
        f"* Running on {bot.user.name}#{bot.user.discriminator} in guild {bot.config.get("guild_id")}"
    )


quart.discord_bot = bot

bot.run(getenv("DISCORD_TOKEN"))
