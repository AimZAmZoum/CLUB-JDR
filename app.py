import os
import discord
import yt_dlp as youtube_dl
import asyncio
from discord.ext import commands 
import random
from datetime import datetime

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
