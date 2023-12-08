
import typing
from os import getenv

from discord import Embed
from discord.ext import commands

if typing.TYPE_CHECKING:
    from discord import Member
    from discord.ext.commands import Context
    from broniabot import BroniaBot

embed_template = {
            "title": "Weryfikacja Konta",
            "description": "Cześć! Witaj na naszym Bronkowym serwerze Discord!\n\nBy zapewnić bezpieczną przestrzeń dla Wszystkich, możemy akceptować tylko uczniów naszej szkoły.\nBy móc rozmawiać, musisz poddać swoje konto weryfikacji.\n\nWeryfikacja polega na szybkim skanie 1 strony twojej legitymacji szkolnej. Zdjęcie musi być wyraźnie i zawierać:\n1. Pełną nazwę szkoły\n2. Twoje imię i nazwisko\n\nNie zapisujemy i nie zbieramy żadnych danych, a weryfikacja jest automatyczna.\n\nKliknij w powyższy link i podążaj za instrukcjami by zweryfikować swoje dane i status uczniowski.",
            "color": 10096397,
            "fields": [
                {
                    "name": "Zweryfikuj się tutaj:",
                    "value": f"{getenv("VERIFY_LINK")}"
                }
            ],
            "author": {
                "name": "II Liceum Ogólnokształcące im. Władysława Broniewskiego w Koszalinie"
            }
        }

class VerificationMessage(commands.Cog):
    def __init__(self, bot: "BroniaBot") -> None:
        self.bot = bot
        self.guild = bot.get_guild(bot.config.get('guild_id'))

    async def send_verification_message(self, member: "Member"):
        embed = Embed.from_dict(embed_template)
        await member.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: "Member"):
        if member.pending:
            return
        else:
            await self.send_verification_message(member)

    @commands.Cog.listener()
    async def on_member_update(self, _, member: "Member"):
        if (not (self.guild.get_role(self.bot.config.get("verified_role_id")) in member.roles)) and (not member.pending):
            await self.send_verification_message(member)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VerificationMessage(bot))
