
import os
import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio
from discord.ext import tasks
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

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

@bot.event
async def on_voice_state_update(member, before, after):
    voice_client = member.guild.voice_client
    if not voice_client:
        return
    
    if len(voice_client.channel.members) == 1:
        await asyncio.sleep(60)
        
        if len(voice_client.channel.members) == 1:
            await voice_client.disconnect()
            
            text_channel = discord.utils.get(member.guild.text_channels, name="bot-commands")
            if text_channel:
                await text_channel.send("Going to sleep.")

@tasks.loop(hours=24)
async def check_free_games():

    channel = discord.utils.get(bot.get_all_channels(), name="whats-free-to-play")
    if not channel:
        return

    # Epic
    try:
        epic_url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        response = requests.get(epic_url).json()
        games = response['data']['Catalog']['searchStore']['elements']
        
        for game in games:
            promotions = game.get('promotions')
            if promotions and promotions.get('promotionalOffers'):
                offers = promotions['promotionalOffers'][0]['promotionalOffers']
                if any(offer.get('discountSetting', {}).get('discountPercentage') == 0 for offer in offers):
                    title = game['title']
                    slug = game['catalogNs']['mappings'][0]['pageSlug']
                    link = f"https://store.epicgames.com/en-US/p/{slug}"
                    await channel.send(f"🎮 **Epic Games FREEBIE:** {title}\n{link}")
    except Exception as e:
        print(f"Epic Error: {e}")

    # Steam
    try:
        steam_search_url = "https://store.steampowered.com/search/?maxprice=free&category1=998&specials=1"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(steam_search_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        search_results = soup.find('div', id='search_resultsRows')
        if search_results:
            game_links = search_results.find_all('a')
            for game in game_links:
                title = game.find('span', class_='title').text
                link = game['href'].split('?')[0] 
                await channel.send(f"♨️ **Steam FREEBIE (Limited Time):** {title}\n{link}")
    except Exception as e:
        print(f"Steam Error: {e}")

@check_free_games.before_loop
async def before_check_free_games():
    await bot.wait_until_ready()

check_free_games.start()

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected.")

bot.run(TOKEN)

