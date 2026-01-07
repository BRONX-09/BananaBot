
import os
import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio
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

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    if not check_free_games.is_running():
        check_free_games.start()

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
                    description = game.get('description', 'No description available.')
                    slug = game.get('catalogNs', {}).get('mappings', [{}])[0].get('pageSlug') or game.get('urlSlug')
                    link = f"https://store.epicgames.com/en-US/p/{slug}"
                    
                    image_url = None
                    for image in game.get('keyImages', []):
                        if image.get('type') in ['Thumbnail', 'OfferImageWide', 'DieselStoreFrontWide']:
                            image_url = image.get('url')
                            break

                    embed = discord.Embed(
                        title=f"FREE ON EPIC: {title}",
                        url=link,
                        description=description[:200] + "..." if len(description) > 200 else description,
                        color=discord.Color.blue()
                    )
                    if image_url:
                        embed.set_image(url=image_url)
                    embed.set_footer(text="Grab it on Epic Games Store!")
                    await channel.send(embed=embed)
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
                # Extract Steam App ID to get the header image
                app_id = link.split('/')[4]
                img_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"

                steam_embed = discord.Embed(
                    title=f"FREE ON STEAM: {title}",
                    url=link,
                    description="This paid game is currently free to keep on Steam! ♨️",
                    color=discord.Color.dark_gray()
                )
                steam_embed.set_image(url=img_url)
                steam_embed.set_footer(text="Limited time offer on Steam")
                
                await channel.send(embed=steam_embed)
    except Exception as e:
        print(f"Steam Error: {e}")

@check_free_games.before_loop
async def before_check_free_games():
    await bot.wait_until_ready()


@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected.")

bot.run(TOKEN)

