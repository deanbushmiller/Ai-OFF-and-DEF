# Split-model download test (instructor only, temporary)

Downloads the six model parts of the split lab 12 image (`lab12-splittest-amd64`) one at a
time, outside Docker, with a progress bar for each part. Nothing is saved.

Use the copy button at the right of each grey box, then paste into PowerShell
(right-click in the PowerShell window pastes).

## 1. Open PowerShell

Click **Start**, type `PowerShell`, click **Windows PowerShell**.

## 2. Download the test into your Downloads folder

```powershell
[Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -UseBasicParsing -Uri https://raw.githubusercontent.com/deanbushmiller/Ai-OFF-and-DEF/main/testsplit/testsplit.ps1 -OutFile $HOME\Downloads\testsplit.ps1
```

It prints nothing if it worked.

## 3. Run it

First model part only (about 8 minutes at 0.4 MB/s):

```powershell
powershell -ExecutionPolicy Bypass -File $HOME\Downloads\testsplit.ps1 -Parts 1
```

All six parts (about an hour at 0.4 MB/s):

```powershell
powershell -ExecutionPolicy Bypass -File $HOME\Downloads\testsplit.ps1
```

## 4. Read the result

The last line looks like:

```
SPLIT-TEST parts_ok=6/6 attempts=8 total_time=58m10s
```

| Result | Meaning |
|---|---|
| every part **OK** | the split downloads on this network; a stuck `docker pull` is Docker on this machine |
| **CUT**, then **OK** on a retry | GitHub's download link expired mid-part; the retry finished it |
| a part **CUT** 3 times | this network is too slow even for 190 MB parts |

## Mac or Linux

```bash
curl -sL https://raw.githubusercontent.com/deanbushmiller/Ai-OFF-and-DEF/main/testsplit/testsplit.sh | bash -s 1
```
