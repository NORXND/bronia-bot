import re
import pytesseract
from PIL import Image
from os import getenv
from quart import Quart, current_app, redirect, request, url_for
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized

quart = Quart(__name__)

quart.secret_key = bytes(getenv("APP_SECRET"), "utf-8")

quart.config["DISCORD_CLIENT_ID"] = getenv("CLIENT_ID")
quart.config["DISCORD_CLIENT_SECRET"] = getenv("CLIENT_SECRET")
quart.config["DISCORD_REDIRECT_URI"] = getenv("CALLBACK_LINK")

discord_oauth = DiscordOAuth2Session(quart)


@quart.route("/login/")
async def login():
    return await discord_oauth.create_session(scope=["identify"])


@quart.route("/callback/")
async def callback():
    await discord_oauth.callback()
    return redirect(url_for("verify"))


@quart.errorhandler(Unauthorized)
async def redirect_unauthorized(e):
    return redirect(url_for("login"))


@quart.route("/upload", methods=["POST"])
async def upload():
    if "photo" not in (await request.files).keys():
        return "No file uploaded!", 400

    photo = (await request.files)["photo"]
    if photo:
        with photo.stream as image_stream:
            # Open image using PIL
            with Image.open(image_stream) as img:
                # Perform OCR on the image
                extracted_text = pytesseract.image_to_string(
                    img, lang="pol", config="--psm 1"
                )

                words_to_match = [
                    "II",
                    "Liceum",
                    "Ogólnokształcące",
                    "Władysława",
                    "Broniewskiego",
                    "ul.",
                    "Chełmońskiego",
                    "7",
                    "75-631",
                    "Koszalin",
                ]

                school_pattern = (
                    r"\b(?:"
                    + "|".join(re.escape(word) for word in words_to_match)
                    + r")\b"
                )

                school_match = re.findall(school_pattern, extracted_text)

                if len(school_match) != len(words_to_match):
                    return f"Nie mogliśmy znaleźć potrzebnych informacji! Skontaktuj się z członkiem SU."

                # Define regex pattern for Polish name
                name_pattern = (
                    r"\b[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]* [A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]*\b"
                )

                # Find Polish name using regex
                name_match = re.search(name_pattern, extracted_text)
                if name_match:
                    user = await discord_oauth.fetch_user()

                    first_full_name = name_match.group(0)
                    guild = current_app.discord_bot.get_guild(
                        current_app.discord_bot.config.get("guild_id")
                    )
                    member = guild.get_member(user.id)

                    if member == None:
                        return "Nie jesteś jeszcze na naszym serwerze Discord!"

                    await member.edit(nick=first_full_name)

                    await member.add_roles(
                        guild.get_role(
                            current_app.discord_bot.config.get("verified_role_id")
                        )
                    )

                    return f"Weryfikacja przebiegła pomyślnie! Witaj {first_full_name}!"
                else:
                    return f"Nie mogliśmy znaleźć potrzebnych informacji, potwierdziliśmy jednak Twój status ucznia. Skontaktuj się z członkiem SU."

                return f"Nie mogliśmy znaleźć potrzebnych informacji! Skontaktuj się z członkiem SU."

    return "Nie możemy przetworzyć zdjęcia/skanu, spróbuj jeszcze raz!"


@quart.route("/verify/")
@requires_authorization
async def verify():
    user = await discord_oauth.fetch_user()
    return f"""
    <html>
        <head>
            <title>Weryfikacja BroniaBot</title>
        </head>
        <body>
            <h1>Witaj!</h1>
<h3>Teraz zweryfikujemy Twoją tożsamość dla użytkownika {user.name} !</h3>
<p>Jak się zweryfikować:</p>
<p>1. Kliknij poniżej by wybrać lub zrobić zdjęcie przedniej strony swojej legitymacji. Zdjęcie musi być wyraźne, zawierać Twoje pełne imię i nazwisko oraz nazwę i adres szkoły.</p>
<p>2. Gotowe! Zostaniesz zweryfikowany automatycznie</p>
<form action="/upload" method="post" enctype="multipart/form-data">
  <label for="photo">Wybierz zdjęcie lub skan:</label>
  <input type="file" id="photo" name="photo" accept="image/*">
  <br><br>
  <input type="submit" value="Wyślij">
</form>
<p>Kto przechowuje moje zdjęcie / czy jest ono gdzieś zapisywane / kto ma do niego dostęp / RODO:</p>
<p>Nie przechowujemy Twojego zdjęcia, nie zapisujemy go. Jedynie weryfikujemy informacje, nie mamy dostępu do Twoich danych i więc wszystko jest bezpieczne :)</p>
<p>W razie problem&oacute;w, skontaktuj się z członkiem SU.</p>
        </body>
    </html>"""
