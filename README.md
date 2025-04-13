# 🔔 Discord Stream Notifier Bot

Un bot completo per Discord che monitora e notifica quando uno streamer è in diretta su **Twitch**, **TikTok** o ha pubblicato un nuovo video su **YouTube**. Inoltre aggiorna i nomi dei canali con il numero di utenti, booster e ruoli personalizzati, e gestisce i ruoli con le reazioni.

## ✨ Funzionalità
- 🔴 Notifiche live da **Twitch** e **TikTok**
- 📺 Notifiche per nuovi video YouTube
- 👥 Aggiornamento automatico dei nomi dei canali (utenti, booster, ruoli)
- 🎭 Sistema di assegnazione/rimozione ruoli con reazioni
- 🔄 Monitoraggio continuo con task asincroni

## 🛠 Requisiti

- Python 3.8 o superiore
- Token bot Discord
- API Key YouTube
- Client ID e Secret Twitch
- Nome utente TikTok

## ⚙️ Configurazione

Alla prima esecuzione viene generato automaticamente un file `config.json` con i campi da compilare:

```json
{
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
    }
  },
  "YOUTUBE_API_KEY": "IL_TUO_API_KEY",
  "YOUTUBE_CHANNEL_ID": "ID_CANALE_YT",
  "TWIITCH_CLIENT_ID": "IL_TUO_ID",
  "TWIITCH_CLIENT_SECRET": "IL_TUO_SECRET",
  "TWIITCH_STREAMER_NAME": "twitch_user",
  "TIKTOK_USERNAME": "tiktok_user",
  "CHECK_INTERVAL": 300
}
```
## ▶️ Avvio
### Installa i pacchetti richiesti:
```txt
pip install -r requirements.txt
```

### Avvia il bot:
```txt
python bot.py
```
### 📝 Il file config.json viene creato automaticamente al primo avvio. (dovrai stoppare il bot, modificare il config.json per poi riavviare il bot)
### 📝 Il file published_video_links.txt viene creato automaticamente per evitare notifiche duplicate di video YouTube.

## 📦 Dipendenze principali

### discord.py – Interazione con l'API Discord

### TikTokLive – Controllo live su TikTok

### google-api-python-client – Accesso ai dati YouTube

### requests – Richieste API per Twitch

📄 Licenza
Questo progetto è rilasciato sotto licenza MIT. Puoi modificarlo e distribuirlo liberamente.

Made with ❤️ by Smokytek
