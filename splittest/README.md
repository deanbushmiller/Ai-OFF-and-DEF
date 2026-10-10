# Split-model test — lab 3 (instructor only, temporary)

Tests the lab 3 image whose 1.09 GB language model downloads in **six parts of up to
190 MB** instead of one piece. Use a normal PowerShell window with Docker Desktop running.

## 1. Start clean

Remove any lab images already on this machine, so the model has to download:

```powershell
docker images ghcr.io/deanbushmiller/seclm-labs -q | Sort-Object -Unique | ForEach-Object { docker image rm -f $_ }
```

## 2. Download the test image — watch the model parts

```powershell
docker pull ghcr.io/deanbushmiller/seclm-labs:lab3-splittest-amd64
```

You should see six large layers of 159–190 MB, each reaching **Pull complete**. If one is
interrupted, Docker retries only that part.

## 3. Run lab 3 automatically

```powershell
docker run --rm --network none ghcr.io/deanbushmiller/seclm-labs:lab3-splittest-amd64 lab 3 --auto
```

It should end without `LAB ERROR`. Check the exit code:

```powershell
$LASTEXITCODE
```

`0` means lab 3 passed on this machine with the split model.

## 4. Report back

- Did the pull finish? Any parts restart?
- The exit code from step 3, and the last few lines it printed.
