import asyncio
import discord
import os
import requests
import json
import logging
import time
from googleapiclient.discovery import build
from discord.ext import commands
from TikTokLive import TikTokLiveClient
from TikTokLive.events import LiveEndEvent, ConnectEvent, DisconnectEvent, FollowEvent
from TikTokLive.client.errors import UserOfflineError
from datetime import datetime

# Nome del file di configurazione
CONFIG_FILE = "config.json"

# Configurazione di default se il file non esiste
def create_default_config():
    default_config = {
        "TOKEN": "IL_TUO_TOKEN",
        "DEBUG": "false",
        "GUILD_ID": 123456789012345678,
        "REACTION": {
        	"message_id": 123456789012345678,
            "role_id": 123456789012345678,
        	"emoji": "🥄"
    	},
        "CHANNELS": {
            "total_members": 123456789012345678,
            "boosters": 123456789012345678,
            "youtube": 123456789012345678,
            "tiktok": 123456789012345678,
            "twitch": 123456789012345678,
            "role_members": {
                "role_id": 123456789012345678,
                "channel_id": 123456789012345678
            },
            
        },
		"YOUTUBE_API_KEY": "IL_TUO_API_KEY",
		"YOUTUBE_CHANNEL_ID": "ID_CANALE_YT",
		"TWIITCH_CLIENT_ID": "IL_TUO_ID",
		"TWIITCH_CLIENT_SECRET": "IL_TUO_SECRET",
		"TWIITCH_STREAMER_NAME": "twitch_user",
        "TIKTOK_USERNAME": "tiktok_user",
        "CHECK_INTERVAL": 300
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(default_config, f, indent=4)

if not os.path.exists(CONFIG_FILE):
    create_default_config()

# Caricamento configurazione
with open(CONFIG_FILE) as f:
    config = json.load(f)

TOKEN = config["TOKEN"]
GUILD_ID = config["GUILD_ID"]
CHANNELS = config["CHANNELS"]
TIKTOK_USERNAME = config["TIKTOK_USERNAME"]
YOUTUBE_API_KEY = config['YOUTUBE_API_KEY']
YOUTUBE_CHANNEL_ID = config['YOUTUBE_CHANNEL_ID']
TWIITCH_CLIENT_ID = config['TWIITCH_CLIENT_ID']
TWIITCH_CLIENT_SECRET = config['TWIITCH_CLIENT_SECRET']
TWIITCH_STREAMER_NAME = config['TWIITCH_STREAMER_NAME']
CHECK_INTERVAL = config['CHECK_INTERVAL']
DEBUG = config['DEBUG']

# Setup YouTube API
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
twitch_live_start_time = None

# Intents e bot Discord
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.reactions = True
latest_video_id = None
latest_streamer_status = None
bot = commands.Bot(command_prefix="!", intents=intents)

# Client TikTok
tiktok_client1 = TikTokLiveClient(unique_id=TIKTOK_USERNAME)
is_live = False
live_start_time = None
# Eventi Discord
@bot.event

async def on_ready():
    print(f"{bot.user} è connesso!")
    bot.loop.create_task(check_new_video())
    bot.loop.create_task(check_twitch_stream())
    bot.loop.create_task(start_tiktok_monitor())
    await update_channel_names()

async def update_channel_names():
    guild = bot.get_guild(config["GUILD_ID"])
    if guild:
        if "total_members" in CHANNELS:
            total_channel = guild.get_channel(CHANNELS["total_members"])
            if total_channel:
                member_count = sum(1 for member in guild.members if not member.bot)
                await total_channel.edit(name=f"Utenti: {member_count}")

        if "boosters" in CHANNELS:
            booster_channel = guild.get_channel(CHANNELS["boosters"])
            if booster_channel:
                booster_count = sum(1 for member in guild.members if member.premium_since)
                await booster_channel.edit(name=f"Booster: {booster_count}")

        if "role_members" in CHANNELS:
            role_id = CHANNELS["role_members"]["role_id"]
            role_channel_id = CHANNELS["role_members"]["channel_id"]
            role_channel = guild.get_channel(role_channel_id)
            role = guild.get_role(role_id)
            if role and role_channel:
                role_count = sum(1 for member in guild.members if role in member.roles)
                await role_channel.edit(name=f"{role.name}: {role_count}")

# Funzione per ottenere il token OAuth di Twitch
def get_twitch_oauth_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWIITCH_CLIENT_ID,
        "client_secret": TWIITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, params=params)
    return response.json().get("access_token")

# Funzione per controllare se lo streamer è live
async def check_twitch_stream():
    global latest_streamer_status, twitch_live_start_time
    channel = bot.get_channel(CHANNELS["twitch"])

    while True:
        try:
            oauth_token = get_twitch_oauth_token()
            headers = {
                "Client-ID": TWIITCH_CLIENT_ID,
                "Authorization": f"Bearer {oauth_token}"
            }
            url = f"https://api.twitch.tv/helix/streams?user_login={TWIITCH_STREAMER_NAME}"
            response = requests.get(url, headers=headers)
            data = response.json()

            if data.get("data"):
                stream_title = data["data"][0]["title"]
                stream_url = f"https://www.twitch.tv/{TWIITCH_STREAMER_NAME}"

                if latest_streamer_status != "live":
                    latest_streamer_status = "live"
                    twitch_live_start_time = datetime.now()  # Salva inizio live

                    await channel.send(
                        f"🎮 Lo streamer **{TWIITCH_STREAMER_NAME}** è ora in live su Twitch!\n📺 {stream_title}\n🔴 {stream_url}"
                    )
            else:
                if latest_streamer_status == "live":
                    latest_streamer_status = "offline"
                    if twitch_live_start_time:
                        duration = datetime.now() - twitch_live_start_time
                        hours, remainder = divmod(duration.total_seconds(), 3600)
                        minutes, _ = divmod(remainder, 60)
                        durata = f"{int(hours)}h {int(minutes)}m" if hours > 0 else f"{int(minutes)}m"
                    else:
                        durata = "Durata sconosciuta"

                    await channel.send(
                        f"📴 **{TWIITCH_STREAMER_NAME}** ha terminato la live su Twitch.\n🕒 Durata live: {durata}"
                    )
                    twitch_live_start_time = None

        except Exception as e:
            print(f"Errore durante il controllo Twitch: {e}")

        await asyncio.sleep(CHECK_INTERVAL)

# Funzione per controllare i nuovi video su YouTube
async def check_new_video():
    global latest_video_id
    channel = bot.get_channel(CHANNELS["youtube"])

    # Funzione per leggere il file di testo con i link dei video pubblicati
    def read_video_links():
        try:
            with open('published_video_links.txt', 'r') as file:
                return file.read().splitlines()
        except FileNotFoundError:
            return []

    # Funzione per scrivere il link nel file
    def write_video_link(video_url):
        with open('published_video_links.txt', 'a') as file:
            file.write(video_url + '\n')

    while True:
        try:
            request = youtube.search().list(
                part="snippet",
                channelId=YOUTUBE_CHANNEL_ID,
                order="date",
                type="video",
                maxResults=1
            )
            response = request.execute()
            
            if response["items"]:
                video_id = response["items"][0]["id"]["videoId"]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                video_title = response["items"][0]["snippet"]["title"]

                # Leggi i link dei video già pubblicati
                published_links = read_video_links()

                # Controlla se il video è già stato pubblicato
                if video_url not in published_links:
                    write_video_link(video_url)  # Salva il nuovo link
                    await channel.send(f"🎥 Nuovo video pubblicato: **{video_title}**\nGuarda ora: {video_url}")
        
        except Exception as e:
            print(f"Errore durante il controllo YouTube: {e}")
        
        await asyncio.sleep(CHECK_INTERVAL)
        
# Notifiche Discord
async def send_discord_notification(message):
    channel_id = CHANNELS.get("tiktok")
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(message)      
        
# Evento: connessione riuscita
@tiktok_client1.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    print(f"✅ Connesso a @{event.unique_id}")
    is_live = True

# Evento: disconnessione
@tiktok_client1.on(DisconnectEvent)
async def on_disconnect(event: DisconnectEvent):
    print("❌ Disconnesso")

    
async def start_tiktok_monitor():
    bot.loop.create_task(check_loop())

# Funzione per controllare se l’utente è live
async def check_loop():
    global is_live, live_start_time
    while True:
        try:
            # Se non è live
            if not await tiktok_client1.is_live():
                if is_live:
                    is_live = False
                    if live_start_time:
                        duration = datetime.now() - live_start_time
                        hours, remainder = divmod(duration.total_seconds(), 3600)
                        minutes, _ = divmod(remainder, 60)
                        durata = f"{int(hours)}h {int(minutes)}m" if hours > 0 else f"{int(minutes)}m"
                    else:
                        durata = "Durata sconosciuta"
                    await send_discord_notification(f"{TIKTOK_USERNAME} ha terminato la diretta su TikTok.\n🕒 Durata live: {durata}")
                    live_start_time = None
                print("❌ Utente offline. Ricontrollo tra 60s.")
                await asyncio.sleep(60)
                continue

            # Se diventa live e non eravamo già connessi
            if not is_live:
                is_live = True
                live_start_time = datetime.now()
                await send_discord_notification(
                    f"<@&937199941644861560>\n**{TIKTOK_USERNAME}** è ora in diretta su TikTok!\nhttps://www.tiktok.com/{TIKTOK_USERNAME}/live 🎥🔥"
                )
                print("✔️ Utente online. Ricontrollo tra 60s.")

            # Se è già live, connetti il client (solo una volta)
            try:
                await tiktok_client1.connect()
            except Exception as e:
                pass

        except Exception as e:
            print(f"⚠️ Errore: {e}")

        await asyncio.sleep(10)  # Delay per evitare spam

async def on_member_join(member):
    await update_channel_names()

@bot.event
async def on_member_remove(member):
    await update_channel_names()

@bot.event
async def on_member_update(before, after):
    if before.premium_since != after.premium_since or before.roles != after.roles:
        await update_channel_names()        

@bot.event
async def on_raw_reaction_add(payload):
    reaction_cfg = config["REACTION"]
    
    if payload.message_id == reaction_cfg["message_id"] and str(payload.emoji.name) == reaction_cfg["emoji"]:
        guild = bot.get_guild(payload.guild_id)

        if guild is None:
            print("❌ Guild non trovata.")
            print("🔍 Guild disponibili:")
            for g in bot.guilds:
                print(f"➡ {g.name} ({g.id})")
            return

        role = guild.get_role(reaction_cfg["role_id"])
        if role is None:
            print("❌ Ruolo non trovato.")
            return

        member = guild.get_member(payload.user_id)
        if member is None or member.bot:
            return

        try:
            if role in member.roles:
                await member.remove_roles(role)
                print(f"🔁 Ruolo '{role.name}' rimosso da {member.display_name}")
            else:
                await member.add_roles(role)
                print(f"✅ Ruolo '{role.name}' assegnato a {member.display_name}")
        except Exception as e:
            print(f"❌ Errore nella gestione del ruolo: {e}")

        try:
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, member)
        except Exception as e:
            print(f"❌ Errore durante la rimozione della reazione: {e}")        
        
bot.run(TOKEN)
