# Auto Nexent deployment after reboot.
# Runs elevated via scheduled task CodexNexentDeploy (ONLOGON).

$ErrorActionPreference = "Continue"

$LogPath = "D:\nexent-deploy.log"
$StatusPath = "D:\nexent-deploy-status.json"
$RepoPath = "D:\nexent"
$TaskName = "CodexNexentDeploy"

function Write-Log($message) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $message
    Write-Output $line
    Add-Content -LiteralPath $LogPath -Value $line -Encoding utf8
}

function Set-Status($phase, $ok, $message) {
    $payload = @{
        phase = $phase
        ok = [bool]$ok
        message = $message
        timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
        log = $LogPath
    }
    $payload | ConvertTo-Json | Out-File -FilePath $StatusPath -Encoding utf8
}

try {
    Write-Log "Auto deployment started."

    # 1) Ensure required Windows features (DISM is idempotent after reboot)
    Write-Log "Checking/enabling Windows features..."
    $features = @("VirtualMachinePlatform", "Microsoft-Windows-Subsystem-Linux")
    foreach ($feature in $features) {
        $check = & dism.exe /online /get-featureinfo /featurename:$feature 2>&1 | Out-String
        if ($check -match "Enabled|启用") {
            Write-Log "$feature already enabled."
            continue
        }
        Write-Log "Enabling $feature ..."
        & dism.exe /online /enable-feature /featurename:$feature /all /norestart 2>&1 |
            ForEach-Object { Write-Log ($_ | Out-String).Trim() }
        $retry = & dism.exe /online /get-featureinfo /featurename:$feature 2>&1 | Out-String
        if ($retry -notmatch "Enabled|启用") {
            Write-Log "$feature NOT enabled after attempt. Check DISM log."
        }
    }

    # 2) Wait for network
    Write-Log "Waiting for network..."
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $null = Test-NetConnection -ComputerName "github.com" -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
            break
        } catch {
            Start-Sleep -Seconds 10
        }
    }

    # 3) Install Docker Desktop via winget
    $dockerExe = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path $dockerExe)) {
        Write-Log "Downloading Docker Desktop installer..."
        $installer = "D:\DockerDesktopInstaller.exe"
        $downloadUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
        try {
            Invoke-WebRequest -Uri $downloadUrl -OutFile $installer -UseBasicParsing `
                -TimeoutSec 600 -ErrorAction Stop
            Write-Log "Running Docker Desktop installer (quiet, wsl-2, accept-license)..."
            $installProc = Start-Process -FilePath $installer `
                -ArgumentList "install", "--quiet", "--accept-license", "--backend=wsl-2" `
                -Wait -PassThru -WindowStyle Hidden
            Write-Log "Docker Desktop installer exit code: $($installProc.ExitCode)"
        } catch {
            Write-Log "Installer download/install failed: $($_.Exception.Message); falling back to winget"
            $winget = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\winget.exe"
            & $winget install -e --id Docker.DockerDesktop --silent `
                --accept-package-agreements --accept-source-agreements --disable-interactivity 2>&1 |
                ForEach-Object { Write-Log ($_ | Out-String).Trim() }
        }
    }
    if (-not (Test-Path $dockerExe)) {
        $candidates = @(
            "C:\Program Files\Docker\Docker\Docker Desktop.exe",
            (Join-Path $env:LOCALAPPDATA "Docker\Docker Desktop.exe")
        )
        $dockerExe = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    }
    if (-not $dockerExe) {
        throw "Docker Desktop executable not found after installation."
    }
    Write-Log "Docker Desktop found: $dockerExe"

    # 4) Start Docker Desktop and wait for engine
    Write-Log "Starting Docker Desktop..."
    if (-not (Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue)) {
        Start-Process -FilePath $dockerExe -WindowStyle Hidden | Out-Null
    }
    $dockerCli = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
    if (-not (Test-Path $dockerCli)) {
        $dockerCli = (Get-Command docker -ErrorAction SilentlyContinue).Source
    }
    $engineReady = $false
    for ($i = 0; $i -lt 120; $i++) {
        if ($dockerCli -and (Test-Path $dockerCli)) {
            & $dockerCli info 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $engineReady = $true
                break
            }
        }
        Start-Sleep -Seconds 10
    }
    if (-not $engineReady) {
        throw "Docker engine did not become ready within 20 minutes."
    }
    Write-Log "Docker engine is ready."

    # 5) Clone/pull Nexent
    Write-Log "Preparing Nexent repository at $RepoPath ..."
    if (-not (Test-Path (Join-Path $RepoPath ".git"))) {
        & git clone --depth 1 https://github.com/ModelEngine-Group/nexent.git $RepoPath 2>&1 |
            ForEach-Object { Write-Log ($_ | Out-String).Trim() }
    } else {
        Push-Location $RepoPath
        & git pull --ff-only 2>&1 | ForEach-Object { Write-Log ($_ | Out-String).Trim() }
        Pop-Location
    }

    # 6) Run official Docker deployment (non-interactive defaults)
    Write-Log "Deploying Nexent with deploy.sh docker --defaults (this can take 10+ minutes)..."
    Set-Status "deploying" $false "Nexent deployment in progress."
    $bash = "C:\Program Files\Git\bin\bash.exe"
    if (-not (Test-Path $bash)) {
        throw "Git Bash not found; cannot run deploy.sh"
    }
    $outLog = "D:\nexent-deploy-stdout.log"
    $errLog = "D:\nexent-deploy-stderr.log"
    $deployProc = Start-Process -FilePath $bash -WorkingDirectory $RepoPath `
        -ArgumentList "-lc", "./deploy.sh docker --defaults" `
        -RedirectStandardOutput $outLog -RedirectStandardError $errLog `
        -PassThru -WindowStyle Hidden
    if (-not $deployProc.WaitForExit(1800000)) {
        Stop-Process -Id $deployProc.Id -Force -ErrorAction SilentlyContinue
        throw "Nexent deployment timed out after 30 minutes."
    }
    Write-Log "deploy.sh exit code: $($deployProc.ExitCode)"
    Get-Content $outLog -ErrorAction SilentlyContinue | ForEach-Object { Write-Log $_ }
    Get-Content $errLog -ErrorAction SilentlyContinue | ForEach-Object { Write-Log $_ }
    if ($deployProc.ExitCode -ne 0) {
        throw "Nexent deploy.sh failed with exit code $($deployProc.ExitCode)"
    }

    # 7) Health check
    $healthy = $false
    for ($i = 0; $i -lt 60; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing `
                -TimeoutSec 15 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) {
                $healthy = $true
                break
            }
        } catch {
            Start-Sleep -Seconds 10
        }
    }
    if (-not $healthy) {
        throw "Nexent frontend did not become healthy at http://localhost:3000"
    }

    Write-Log "Nexent is healthy at http://localhost:3000"
    Set-Status "completed" $true "Nexent deployed and healthy at http://localhost:3000"
} catch {
    $message = $_.Exception.Message
    Write-Log "FATAL: $message"
    Set-Status "failed" $false $message
} finally {
    # Remove the one-shot task so it does not run on every logon
    & schtasks.exe /Delete /TN $TaskName /F 2>&1 | Out-Null
}
