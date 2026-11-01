# 🌌 Cosmic ki baddie
### A Complete Discord Server Management & Automation Bot for Side Quest Studio

**Cosmic ki baddie** is a production-ready, modular Discord bot built with `discord.py` and asynchronous `aiosqlite`. It provides an in-Discord management command suite: you never have to edit Python source files to configure moderation policies, support ticket categories, anti-nuke safeguards, autoresponders, or custom command permissions.

---

## ✨ Core Features

1. **Moderation System**: `/kick`, `/ban`, `/unban`, `/timeout`, `/untimeout`, `/warn`, `/warnings`, `/clearwarns`, `/slowmode`, `/lock`, `/unlock`, `/hide`, `/unhide`, `/nick`, `/snipe`, `/editsnipe`, `/modlogs` with interactive confirmation views and strict role hierarchy protection.
2. **Purge Engine**: `/purge` with multi-filter cleaning (by user, phrase, links only, bot messages, or attachments) with 14-day Discord bulk delete compliance.
3. **Support Tickets**: Button-driven ticket creation panel, private channels, staff claim system (`/ticket claim`), transcript archiving to SQLite & `.txt` files, and auto-logging.
4. **Anti-Nuke & Server Protection**: Audit log monitoring against mass channel deletions, mass role purges, and unauthorized bans/kicks within configurable time windows. Includes **Safe Mode**, **Server Protection**, and **Emergency Lockdown**.
5. **Dynamic Role & Permission Management**: Control which roles can use which bot commands without opening code (`/permissions set role:@Moderator command:ban access:true`).
6. **Rule-Based Autoresponder**: Exact, contains, or startswith keyword triggers with cooldowns, channel filters, embed output, and anti-loop guards.
7. **Activity Progression & Roles**: Message count & XP level tracking with automated milestone role rewards and `/leaderboard`.
8. **Interactive Giveaways & Polls**: Persistent giveaway timer loop with enter buttons, rerolls, and multi-choice live percentage progress polls.
9. **Aesthetic Welcome Gate**: Dedicated onboarding embeds with mentions, automatic newcomer roles (autoroles), and member counters.
10. **Interactive Setup Wizard & Dashboard**: `/setup start` and `/dashboard` for instant, code-free configuration directly inside Discord.

---

## 🛠️ Quick Installation

### 1. Requirements
- **Python 3.10+**
- **pip** and **git**

### 2. Clone or Extract
```bash
cd CosmicKiBaddie
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and fill in your Discord credentials:
```env
DISCORD_TOKEN="YOUR_BOT_TOKEN_HERE"
DEFAULT_PREFIX="!"
MAIN_SERVER_NAME="Side Quest Studio"
```

### 5. Launch the Bot
```bash
chmod +x start.sh
./start.sh
# or directly:
python3 main.py
```

---

## 🔑 Discord Developer Portal Setup

To ensure all bot features work properly:
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and select your application.
2. Navigate to the **Bot** tab:
   - Click **Reset Token** to copy your token into `.env`.
   - Scroll down to **Privileged Gateway Intents** and enable:
     - ✅ **Presence Intent**
     - ✅ **Server Members Intent** *(Required for welcome messages, autorole, and moderation)*
     - ✅ **Message Content Intent** *(Required for autoresponder and prefix commands)*
3. Navigate to **OAuth2 -> URL Generator**:
   - Scopes: Select `bot` and `applications.commands`.
   - Bot Permissions: Select `Administrator` (or `Manage Roles`, `Manage Channels`, `Kick Members`, `Ban Members`, `Moderate Members`, `Send Messages`, `Embed Links`, `Attach Files`, `Read Message History`).
   - Copy the generated URL and invite the bot to **Side Quest Studio**.

---

## 🚀 24/7 Hosting Options

### Option A: Linux VPS with systemd
Create a service file `/etc/systemd/system/cosmicki.service`:
```ini
[Unit]
Description=Cosmic ki baddie Discord Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/CosmicKiBaddie
ExecStart=/usr/bin/python3 /home/ubuntu/CosmicKiBaddie/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable cosmicki
sudo systemctl start cosmicki
```

### Option B: Railway / Render / Docker
Add a Procfile:
```
worker: python3 main.py
```
And define the `DISCORD_TOKEN` environment variable in your cloud dashboard.

---

## 📋 Command Directory & Usage Cheatsheet

| Command | Usage Example | Required Permission |
| :--- | :--- | :--- |
| `/setup start` | Launch 3-step interactive onboarding wizard | Administrator |
| `/dashboard` | Open central Discord configuration control room | Administrator |
| `/help` | Interactive category help menu with examples | @everyone |
| `/ban` | `/ban user:@user delete_message_days:1 reason:Rule 1` | Ban Members |
| `/kick` | `/kick member:@user reason:Spam` | Kick Members |
| `/timeout` | `/timeout member:@user minutes:60 reason:Cooldown` | Moderate Members |
| `/purge` | `/purge amount:25 links_only:true` | Manage Messages |
| `/ticket panel` | `/ticket panel channel:#support` | Administrator |
| `/permissions set` | `/permissions set role:@Helper command:warn access:true` | Administrator |
| `/security mode` | `/security mode mode:SAFE_MODE` | Administrator |
| `/giveaway start` | `/giveaway start prize:Nitro duration:1h winners:1` | Manage Server |
| `/poll create` | `/poll create question:"Game Night?" option1:Halo option2:AmongUs` | Manage Messages |
| `/autoresponder add` | `/autoresponder add trigger:rules response:"See #rules!" match_type:exact` | Manage Server |
| `/embed create` | `/embed create channel:#announcements` | Manage Messages |

---

## 🛡️ Architecture & Database Safety

- **Database**: SQLite WAL mode with automatic schema initialization via `database.py`.
- **Modularity**: 16 dedicated extensions in `cogs/` dynamically loaded in `main.py`.
- **Fault-Tolerant**: Unhandled command errors trigger informative user embeds while logging details to standard error.
- **Hierarchy Safe**: Moderators cannot target roles equal to or above their own, protecting server administrators.
