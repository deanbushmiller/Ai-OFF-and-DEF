# Connection check — do this before class

The labs download a language model in parts of up to 190 MB from GitHub. Each part has to
finish within about 5 minutes, or the download is cut off and starts that part again.
These two checks tell us, before class, whether your connection can do that.

Paste **both result lines** into the class chat, with your country.

---

## Check 1 — speed test (in your browser, about 30 seconds)

1. Open **<https://www.speedtest.net>**, click **GO**, and wait until it finishes.
2. Read three numbers from the results: **Download**, **Upload** and **Ping**.
3. Paste this line into the chat with your numbers filled in:

```
SPEEDTEST down=___Mbps up=___Mbps ping=___ms
```

### Minimum to take the labs

| | Minimum |
|---|---|
| Download | **20 Mbps** or more |
| Ping | **100 ms** or less |
| Packet loss | **0.5 %** or less (Check 2 measures this) |

If any number misses the minimum, tell your instructor **before** lab 3 — the model download
will not finish on that connection. A wired connection, a different network or a nearer
location usually fixes it.

---

## Check 2 — the real download test (about 1 minute)

This downloads 20 MB of the actual lab model from GitHub, the same way Docker does.

**Windows** — in PowerShell, from your course folder:

```
powershell -ExecutionPolicy Bypass -File .\testconnect.ps1
```

**Mac or Linux** — in Terminal, from your course folder:

```
bash testconnect.sh
```

Paste the line that starts with `GHCR-TEST` into the chat.

---

## Example of what to paste

```
SPEEDTEST down=48Mbps up=12Mbps ping=32ms
GHCR-TEST speed=2.40MB/s latency=30ms loss=0% now=RETRY split=OK   (Germany)
```
