# IRC-Log-Viewer
<img width="1853" height="889" alt="image" src="https://github.com/user-attachments/assets/0bd246e3-4696-4984-a59b-92b5185a66b9" />


# #pascal IRC channel history

A small IRC logger and a web page for reading the log.

- **`log.py`** connects to Libera.Chat, joins a channel, and appends everything it sees to a plain-text log.
- **`index.html`** is a static page that loads that log in the browser and shows it as a searchable, live-updating chat history.

There is no backend, database, or build step. Python 3 (standard library only) writes the log, and any web server can serve the page.

## How it works

```
IRC channel ──► log.py ──► pascal.log ──► (web server) ──► index.html in your browser
                   └─────► <web dir>/pascal.log ─────────────┘
```

`log.py` writes every line to a local `pascal.log` and also to a copy inside your web directory. `index.html` fetches that copy every 3 seconds and parses it in the browser.

## Requirements

- Python 3.6 or newer (no third-party packages)
- A web server that can serve static files (nginx, Apache, Caddy, or `python3 -m http.server` for testing)

## Quick start

### 1. Configure the logger

Edit the settings at the top of `log.py`:

```python
SERVER = "irc.libera.chat"
PORT = 6697                 # TLS
NICK = "history-bot"        # must be unique on the network
CHANNEL = "#pascal"
LOG_FILE = "pascal.log"
WEB_LOG_FILE = "/var/www/pascal.sahanaya.net/html/pascal.log"   # copy served to the web page
```

### 2. Prepare the web directory

Copy the page into your web root, and copy any existing log so the history isn't empty:

```bash
cp index.html /var/www/pascal.sahanaya.net/html/
cp pascal.log  /var/www/pascal.sahanaya.net/html/   # only if you already have a log
```

The user running the bot must be able to write to `WEB_LOG_FILE`. If it can't, the bot prints a single `!!! Could not write ...` warning and keeps logging locally. A common fix:

```bash
sudo chown <bot-user>:www-data /var/www/

.com/html/pascal.log
sudo chmod 664 /var/www/pascal.sahanaya.net/html/pascal.log
```

### 3. Start the logger

```bash
python3 -u log.py
```

To keep it running in the background:

```bash
nohup python3 -u log.py > /dev/null 2>&1 &
```

Make sure only one copy is running (`ps aux | grep log.py`). Two instances appending to the same files will produce duplicate or corrupted lines.

### 4. Open the page

Visit `https://example.com/`. The web server serves `index.html` by default, and it reads `pascal.log` from the same folder.

**Testing locally?** From the folder containing both files, run:

```bash
python3 -m http.server 8000
```

then open `http://localhost:8000/`. Opening the HTML file directly (`file://`) will not work, because browsers block `fetch()` on local files.

## Run as a service (recommended)

A systemd service restarts the logger if it crashes and starts it on boot. Create `/etc/systemd/system/pascal-logger.service`:

```ini
[Unit]
Description=IRC channel logger
After=network-online.target
Wants=network-online.target

[Service]
User=<bot-user>
WorkingDirectory=/path/to/this/repo
ExecStart=/usr/bin/python3 -u log.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now pascal-logger
journalctl -u pascal-logger -f      # watch the output
```

`WorkingDirectory` matters because `LOG_FILE` is a relative path.

## Using the web page

- **Live view:** the page shows the latest 200 messages and refreshes every 3 seconds.
- **Search:** type in the box to search the whole log by message text or nick. Matching is fuzzy, so small typos still match.
- **Load older / View full log:** show 200 more messages, or everything at once.
- **Hide events:** hides joins, quits, and connection status lines so only chat remains.
- **Raw log:** downloads `pascal.log`.
- Image links in messages get an inline preview.


Page settings are constants at the top of the script in `index.html`:

| Constant | Default | Purpose |
|---|---|---|
| `LOG_URL` | `'pascal.log'` | Path to the log file, relative to the page |
| `POLL_MS` | `3000` | How often to reload the log (milliseconds) |
| `BUTTONS_DISABLED` | `true` | Master switch for the paging buttons |

## Log format

One event per line, prefixed with a timestamp:

| Line | Meaning |
|---|---|
| `2026-11-12 20:57:33 <aruna> hello` | Chat message |
| `2026-11-12 20:42:15 * aruna waves` | `/me` action |
| `2026-11-12 20:43:12 * _ghostbyte_ (QUIT)` | Join, part, or quit |
| `2026-11-12 20:49:12 * SueD (NICK SueD_)` | Nick change |
| `2026-11-12 20:50:00 * troll (KICK by op)` | Kick |
| `2026-11-12 20:39:36 --- Connecting to irc.libera.chat:6697 ---` | Bot status |

Lines with no timestamp are treated as a continuation of the previous message.

## Troubleshooting

- **Page says "Reconnecting…" or stays empty:** the browser can't fetch `pascal.log`. Check that it sits next to `index.html` and that you're loading the page over `http(s)://`, not `file://`.
- **Web copy isn't updating:** check the bot's output for `!!! Could not write ...` and fix the file permissions.
- **Repeated `Connection closed by server` errors:** another copy of the bot may be running with the same nick, or the server is rejecting the connection. Stop extra instances and check the nick isn't already in use.
- **Slow page with a very large log:** the page downloads the whole file on each refresh. Rotate the log (for example monthly) if it grows past a few MB.

## Privacy

Anything said in the channel ends up in `pascal.log`, and if the log sits in your web root it is publicly readable. Make sure the channel's users know it is logged, and restrict access (basic auth or an IP allow-list) if the history shouldn't be public.
