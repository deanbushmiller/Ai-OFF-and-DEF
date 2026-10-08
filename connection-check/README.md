# Connection check — do this before class

The labs download a language model in parts of up to 190 MB from GitHub. Each part has to
finish within about 5 minutes, or the download is cut off and starts that part again. On a
connection that is too slow, it never finishes.

This 30-second check tells you whether your connection is fast enough. You do not need to
install or download anything for it.

## 1. Run a speed test

Open **<https://www.speedtest.net>**, click **GO**, and wait until it finishes.

## 2. Compare your results with the minimum

| Result | Minimum to take the labs |
|---|---|
| **Download** | **20 Mbps** or more |
| **Ping** | **100 ms** or less |

## 3. What to do

**Both numbers meet the minimum:** you are ready. Nothing to report.

**Either number misses the minimum:** post this line in the class chat **before lab 3**, with
your numbers and your country:

```
SPEEDTEST down=___Mbps up=___Mbps ping=___ms   (country)
```

The model download will not finish on that connection. A wired connection, a different
network, or a location nearer to you usually fixes it — run the test again after changing.

---

## Troubleshooting — only if a lab download keeps restarting

If you met the minimum but a lab's download keeps going back to zero, run this from your
course folder and post the line that starts with `GHCR-TEST` in the class chat. It measures
the exact download the labs use.

**Windows** — in PowerShell:

```
powershell -ExecutionPolicy Bypass -File .\testconnect.ps1
```

**Mac or Linux** — in Terminal:

```
bash testconnect.sh
```
