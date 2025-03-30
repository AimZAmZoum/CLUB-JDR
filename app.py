import os
import discord
import yt_dlp as youtube_dl
import asyncio
from discord.ext import commands 
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.reactions = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.temp_channels = {}
playlists = {}

async def play_next(ctx):
    vc = ctx.voice_client
    if ctx.guild.id in playlists and playlists[ctx.guild.id]:
        next_url = playlists[ctx.guild.id].pop(0)
        await play_audio(ctx, next_url)
    else:
        await vc.disconnect()

@bot.command()
async def creer_session(ctx):
    guild = ctx.guild
    category_vocal = discord.utils.get(guild.categories, name="Salons vocaux")
    category_textuel = discord.utils.get(guild.categories, name="Salons textuels")
    category_archives = discord.utils.get(guild.categories, name="Archives")

    if not all([category_vocal, category_textuel, category_archives]):
        await ctx.send("❌ Les catégories 'Salons vocaux', 'Salons textuels' ou 'Archives' n'existent pas !")
        return

    current_date = datetime.now().strftime("%d/%m/%Y")
    voice_channel_name = f"Salon vocal de {ctx.author.display_name} - {current_date}"
    text_channel_name = f"Salon textuel de {ctx.author.display_name} - {current_date}"

    voice_channel = await guild.create_voice_channel(name=voice_channel_name, category=category_vocal)
    text_channel = await guild.create_text_channel(name=text_channel_name, category=category_textuel)

    msg = await ctx.send(f"Salon vocal créé : {voice_channel.mention} et salon textuel créé : {text_channel.mention} \nCliquez sur ❌ pour supprimer le salon vocal.")
    await msg.add_reaction("❌")

    bot.temp_channels[msg.id] = voice_channel.id
    bot.text_channels[msg.id] = text_channel.id

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    if str(reaction.emoji) == "❌" and reaction.message.id in bot.temp_channels:
        guild = reaction.message.guild
        voice_channel_id = bot.temp_channels.pop(reaction.message.id, None)
        text_channel_id = bot.text_channels.pop(reaction.message.id, None)
        voice_channel = guild.get_channel(voice_channel_id) if voice_channel_id else None
        text_channel = guild.get_channel(text_channel_id) if text_channel_id else None
        if voice_channel:
            await voice_channel.delete()
            await reaction.message.channel.send(f"🗑️ Salon vocal {voice_channel.name} supprimé.")
        if text_channel:
            archive_category = discord.utils.get(guild.categories, name="Archives")
            if archive_category:
                await text_channel.edit(category=archive_category)
                await reaction.message.channel.send(f"📂 Salon textuel {text_channel.name} déplacé dans 'Archives'.")
        await reaction.message.delete()

async def play_audio(ctx, url):
    vc = ctx.voice_client
    if not vc:
        await ctx.send("Le bot n'est pas connecté à un salon vocal.")
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'extractaudio': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']

    def after_playing(error):
        if error:
            print(f"Erreur de lecture : {error}")
        asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)

    vc.play(discord.FFmpegPCMAudio(audio_url), after=after_playing)
    await ctx.send(f"🎶 Lecture : {info['title']}")

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
        await ctx.send(f"🔊 Connecté à {ctx.author.voice.channel}")
    else:
        await ctx.send("🚨 Tu dois être dans un salon vocal !")

@bot.command()
async def play(ctx, *, query):
    vc = ctx.voice_client
    if not vc:
        await join(ctx)
        vc = ctx.voice_client

    if ctx.guild.id not in playlists:
        playlists[ctx.guild.id] = []

    playlists[ctx.guild.id].append(query)

    if not vc.is_playing():
        await play_next(ctx)
    else:
        await ctx.send(f"🎵 Ajouté à la playlist : {query}")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        playlists[ctx.guild.id] = []
        await ctx.send("🚫 Déconnecté et playlist vidée.")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ Chanson suivante...")

@bot.command()
async def playlist(ctx):
    if ctx.guild.id in playlists and playlists[ctx.guild.id]:
        playlist_str = "\n".join(playlists[ctx.guild.id])
        await ctx.send(f"📜 Playlist actuelle :\n{playlist_str}")
    else:
        await ctx.send("📭 La playlist est vide.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if "quoi" in message.content.lower():
        await message.channel.send(f"{message.author.mention} feur!")

    await bot.process_commands(message)

@bot.command()
async def roll(ctx, dice_count: int, dice_faces: int):
    if dice_count < 1 or dice_faces < 1:
        await ctx.send("Le nombre de dés et de faces doit être supérieur ou égal à 1.")
        return

    rolls = [random.randint(1, dice_faces) for _ in range(dice_count)]
    total = sum(rolls)
    await ctx.send(f"{ctx.author.display_name} lance {dice_count} dé(s) à {dice_faces} faces...!\nRésultats : {', '.join(map(str, rolls))}\nTotal : {total}")

@bot.command()
async def clear(ctx, amount: int):
    if amount <= 0:
        await ctx.send("Le nombre de messages à supprimer doit être supérieur à 0.")
        return

    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"{amount} message(s) supprimé(s).", delete_after=5)

@bot.event
async def on_ready():
    bot.temp_channels = {}
    bot.text_channels = {}
    print(f"Connecté en tant que {bot.user}")

TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
