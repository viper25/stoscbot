Auto Start the bot with  **process supervision + auto-start on boot**. On modern Ubuntu, the cleanest and most robust 
way is to use **systemd**, not cron or rc.local hacks.

---

## ✅ Recommended: Create a `systemd` service

### 1. Create a service file

```bash
sudo nano /etc/systemd/system/stoscbot.service
```

### 2. Add this configuration

```ini
[Unit]
Description=Stosc Telegram Bot
After=network.target

[Service]
User=vibinjk
WorkingDirectory=/home/vibinjk/bots/stoscbot/workspace

# Start command (no nohup needed, systemd handles it)
ExecStart=/home/vibinjk/.local/bin/uv run python run_stoscbot.py

# Restart automatically if it crashes
Restart=always
RestartSec=5

# Optional: clean stop
KillSignal=SIGINT
TimeoutStopSec=10

[Install]
WantedBy=multi-user.target
```

---

### 3. Reload systemd

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
```

---

### 4. Enable auto-start on boot

```bash
sudo systemctl enable stoscbot
```

---

### 5. Start it now

```bash
sudo systemctl start stoscbot
```

---

### 6. Check status / logs

```bash
sudo systemctl status stoscbot
journalctl -u stoscbot -f
```

---

## 🔑 Key improvements over your script

* ❌ No `kill -9` needed (systemd manages lifecycle cleanly)
* ❌ No `nohup` needed
* ✅ Auto-restarts if the bot crashes
* ✅ Starts automatically on reboot
* ✅ Proper logging via `journalctl`
* ✅ Easier debugging and control

---

## ⚠️ Important note about `uv`

Make sure `uv` is in the PATH for systemd. If not, find it:

```bash
which uv
```

If it returns something like:

```
/home/vibinjk/.local/bin/uv
```

Then change:

```ini
ExecStart=/usr/bin/env uv run python run_stoscbot.py
```

to:

```ini
ExecStart=/home/vibinjk/.local/bin/uv run python run_stoscbot.py
```

---

## 🚫 Alternative (not recommended, but simple)

You *could* use cron:

```bash
crontab -e
```

Add:

```bash
@reboot /home/vibinjk/restart_bot.sh
```

But this:

* Won’t restart if the bot crashes
* Harder to debug
* Less control

---

## Status

```bash
vibinjk@stosc-general:~$ sudo systemctl status stoscbot
🟢 stoscbot.service - Stosc Telegram Bot
     Loaded: loaded (/etc/systemd/system/stoscbot.service; enabled; preset: enabled)
     Active: active (running) since Fri 2026-03-20 08:46:20 +08; 7s ago
   Main PID: 397703 (uv)
      Tasks: 4 (limit: 4613)
     Memory: 241.8M (peak: 241.8M)
        CPU: 2.250s
     CGroup: /system.slice/stoscbot.service
             ├─397703 /home/vibinjk/.local/bin/uv run python run_stoscbot.py
             └─397706 /home/vibinjk/bots/stoscbot/workspace/.venv/bin/python3 run_stoscbot.py

Mar 20 08:46:20 stosc-general systemd[1]: stoscbot.service: Scheduled restart job, restart counter is at 16.
Mar 20 08:46:20 stosc-general systemd[1]: Started stoscbot.service - Stosc Telegram Bot.
```