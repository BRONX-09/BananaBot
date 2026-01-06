
import os
import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -filter:a "volume=0.5"'
}

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="welcome")
    if channel:
        await channel.send(f"Welcome to the server, {member.mention}! 🚀")

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hey {ctx.author.name}! I'm up and running.")


@bot.command()
async def play(ctx, *, search: str):
    if not ctx.author.voice:
        return await ctx.send("Join a voice channel first!")
    
    vc = ctx.voice_client
    if not vc:
        vc = await ctx.author.voice.channel.connect()

    async with ctx.typing():
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
                url = info['url']
                title = info['title']
                
                audio_source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
                
                source = discord.PCMVolumeTransformer(audio_source)
                
                if vc.is_playing():
                    vc.stop()
                
                vc.play(source)
                await ctx.send(f"🎶 Now playing: **{title}**")
            except Exception as e:
                await ctx.send(f"An error occurred: {e}")
                print(f"Detailed Error: {e}")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected.")

bot.run(TOKEN)

