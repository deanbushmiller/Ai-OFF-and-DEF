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

## 3. Next step

If you meet the requirements, continue on to [Test 2](#test-2--can-your-computer-download-and-run-a-script).

---

# Test 2 — can your computer download and run a script?

The labs are started by a small script. This test checks, in a few seconds, that your
computer lets you download one and run it. It does **not** need administrator rights and
does not install anything.

**Windows:**

1. Click **Start**, type `PowerShell`, and click **Windows PowerShell**.
   (Do not choose "Run as administrator" — we want to see what a normal window can do.)
2. Click the copy button at the right of the grey box below.
3. In the PowerShell window, **right-click** to paste, then press **Enter**.

```powershell
[Net.ServicePointManager]::SecurityProtocol='Tls12'; irm https://raw.githubusercontent.com/deanbushmiller/Ai-OFF-and-DEF/main/connection-check/check-run.ps1 -OutFile $env:TEMP\check-run.ps1; powershell -ExecutionPolicy Bypass -File $env:TEMP\check-run.ps1
```

**What you should see** ends with:

```
  RESULT: PASS - continue on to the next test.
```

**If you see `RESULT: STOP`, or red error text** such as *"running scripts is disabled on
this system"* or *"cannot be loaded"*: your computer is set up to block scripts, usually by
your organisation. The labs cannot run on it. Tell your instructor before class, or use a
computer you control.

**Mac or Linux:**

1. Open **Terminal**. On a Mac: press **Cmd + Space**, type `Terminal`, press **Enter**.
2. Click the copy button at the right of the grey box below.
3. In the Terminal window, paste (**Cmd + V** on a Mac, **Ctrl + Shift + V** on Linux), then
   press **Enter**. Do not add `sudo`.

```bash
curl -fsSL https://raw.githubusercontent.com/deanbushmiller/Ai-OFF-and-DEF/main/connection-check/check-run.sh -o "${TMPDIR:-/tmp}/check-run.sh" && bash "${TMPDIR:-/tmp}/check-run.sh"
```

**What you should see** ends with:

```
  RESULT: PASS - continue on to the next test.
```

**If you see an error instead** (for example `curl: command not found` or `Could not
resolve host`): copy the error into the class chat before class.
