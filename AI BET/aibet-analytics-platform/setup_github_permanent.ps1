# GitHub Permanent Setup PowerShell Script
# Автоматическая настройка постоянного подключения к GitHub

param(
    [switch]$Auto,
    [string]$Token = "",
    [string]$Name = "AI BET Developer",
    [string]$Email = "aibet@example.com"
)

Write-Host "🚀 Permanente GitHub Setup for AI BET Platform" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green

function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Set-GitCredentials {
    Write-Host "🔧 Настройка учетных данных Git..." -ForegroundColor Yellow
    
    git config --global user.name $Name
    git config --global user.email $Email
    
    Write-Host "✅ Учетные данные настроены: $Name <$Email>" -ForegroundColor Green
}

function Set-GitHubToken {
    Write-Host "🔑 Настройка токена GitHub..." -ForegroundColor Yellow
    
    if (-not $Token) {
        Write-Host "Введите ваш GitHub Personal Access Token:" -ForegroundColor Cyan
        $Token = Read-Host -AsSecureString
        $Token = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Token))
    }
    
    if (-not $Token) {
        Write-Host "❌ Токен не предоставлен" -ForegroundColor Red
        return $false
    }
    
    # Настраиваем remote с токеном
    Set-Location "c:\AI BET\AI BET\aibet-analytics-platform"
    git remote remove origin
    git remote add origin "https://$Token@github.com/nafoxxee/AIBET.git"
    
    # Сохраняем токен в credential helper
    git config --global credential.helper store
    
    # Создаем файл с учетными данными
    $credPath = "$env:USERPROFILE\.git-credentials"
    "https://$Token@github.com" | Out-File -FilePath $credPath -Encoding UTF8
    
    # Устанавливаем права доступа
    $acl = Get-Acl $credPath
    $acl.SetAccessRuleProtection($true, $false)
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($env:USERNAME, "FullControl", "Allow")
    $acl.SetAccessRule($rule)
    Set-Acl $credPath $acl
    
    Write-Host "✅ Токен GitHub сохранен" -ForegroundColor Green
    return $true
}

function Set-SSHKeys {
    Write-Host "🔐 Настройка SSH ключей..." -ForegroundColor Yellow
    
    $sshDir = "$env:USERPROFILE\.ssh"
    if (-not (Test-Path $sshDir)) {
        New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    }
    
    $privateKey = "$sshDir\id_rsa_github"
    $publicKey = "$sshDir\id_rsa_github.pub"
    
    if (Test-Path $privateKey) {
        Write-Host "📋 SSH ключ уже существует:" -ForegroundColor Cyan
        Get-Content $publicKey | Write-Host
        
        $addToConfig = Read-Host "Добавить ключ в SSH config? (y/n)"
        if ($addToConfig -eq 'y') {
            Set-SSHConfig
        }
        return
    }
    
    # Генерируем новый SSH ключ
    Write-Host "🔄 Генерация SSH ключа..." -ForegroundColor Yellow
    ssh-keygen -t rsa -b 4096 -C $Email -f $privateKey -N ""
    
    # Показываем публичный ключ
    $pubKey = Get-Content $publicKey
    Write-Host "`n📋 Ваш публичный SSH ключ:" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Gray
    Write-Host $pubKey -ForegroundColor White
    Write-Host "=" * 50 -ForegroundColor Gray
    
    Write-Host "`n1. Скопируйте ключ выше" -ForegroundColor Yellow
    Write-Host "2. Перейдите на https://github.com/settings/keys" -ForegroundColor Yellow
    Write-Host "3. Нажмите 'New SSH key'" -ForegroundColor Yellow
    Write-Host "4. Вставьте ключ и сохраните" -ForegroundColor Yellow
    
    Read-Host "Нажмите Enter после добавления ключа на GitHub"
    
    Set-SSHConfig
}

function Set-SSHConfig {
    Write-Host "⚙️ Настройка SSH config..." -ForegroundColor Yellow
    
    $sshConfig = "$env:USERPROFILE\.ssh\config"
    
    $configContent = @"
# GitHub Configuration
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa_github
    IdentitiesOnly yes
"@
    
    Add-Content -Path $sshConfig -Value $configContent
    
    Write-Host "✅ SSH config настроен" -ForegroundColor Green
}

function Test-Connection {
    Write-Host "🔍 Проверка подключения к GitHub..." -ForegroundColor Yellow
    
    Set-Location "c:\AI BET\AI BET\aibet-analytics-platform"
    
    # Проверяем статус
    $status = git status --porcelain
    if ($status) {
        Write-Host "📊 Есть изменения для коммита" -ForegroundColor Cyan
    } else {
        Write-Host "📊 Нет изменений" -ForegroundColor Green
    }
    
    # Проверяем remote
    $remote = git remote -v
    Write-Host "📡 Remote URL:" -ForegroundColor Cyan
    Write-Host $remote
    
    # Проверяем подключение
    try {
        $test = git ls-remote origin
        Write-Host "✅ Подключение к GitHub работает" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Ошибка подключения к GitHub" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

function Create-AutoCommitScript {
    Write-Host "🤖 Создание скрипта автокоммитов..." -ForegroundColor Yellow
    
    $scriptPath = "$env:USERPROFILE\auto_commit.ps1"
    
    $scriptContent = @'
# Auto Commit Script for AI BET Platform
param(
    [string]$Message = ""
)

try {
    Set-Location "c:\AI BET\AI BET\aibet-analytics-platform"
    
    # Проверяем есть ли изменения
    $status = git status --porcelain
    
    if ($status) {
        # Добавляем все изменения
        git add .
        
        # Создаем коммит
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        if (-not $Message) {
            $Message = "Auto-commit: $timestamp"
        }
        
        git commit -m $Message
        git push origin main
        
        Write-Host "✅ Auto-commit successful: $Message" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ No changes to commit" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ Auto-commit failed: $_" -ForegroundColor Red
}
'@
    
    $scriptContent | Out-File -FilePath $scriptPath -Encoding UTF8
    
    Write-Host "✅ Скрипт автокоммитов создан: $scriptPath" -ForegroundColor Green
    Write-Host "Использование: .\auto_commit.ps1 -Message 'Ваше сообщение'" -ForegroundColor Cyan
}

function Create-TaskScheduler {
    Write-Host "⏰ Создание планировщика задач..." -ForegroundColor Yellow
    
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$env:USERPROFILE\auto_commit.ps1`""
    $trigger = New-ScheduledTaskTrigger -Daily -At 9am
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    
    Register-ScheduledTask -TaskName "AI BET Auto Commit" -Action $action -Trigger $trigger -Settings $settings -User $env:USERNAME -Force
    
    Write-Host "✅ Планищик задач создан (ежедневно в 9:00)" -ForegroundColor Green
}

# Основной скрипт
if (-not (Test-Command "git")) {
    Write-Host "❌ Git не найден! Установите Git" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Git найден" -ForegroundColor Green

if ($Auto) {
    Write-Host "🤖 Автоматический режим..." -ForegroundColor Yellow
    
    Set-GitCredentials
    Set-GitHubToken
    Test-Connection
    Create-AutoCommitScript
    
    Write-Host "`n🎉 Автоматическая настройка завершена!" -ForegroundColor Green
    Write-Host "Теперь вы можете использовать:" -ForegroundColor Cyan
    Write-Host "  .\auto_commit.ps1 - для ручного коммита" -ForegroundColor White
    Write-Host "  git push origin main - для отправки изменений" -ForegroundColor White
}
else {
    Write-Host "`n📋 Выберите опцию:" -ForegroundColor Cyan
    Write-Host "1. Настроить учетные данные Git" -ForegroundColor White
    Write-Host "2. Настроить токен GitHub (HTTPS)" -ForegroundColor White
    Write-Host "3. Настроить SSH ключи" -ForegroundColor White
    Write-Host "4. Создать скрипт автокоммитов" -ForegroundColor White
    Write-Host "5. Создать планировщик задач" -ForegroundColor White
    Write-Host "6. Проверить подключение" -ForegroundColor White
    Write-Host "7. Полная автоматическая настройка" -ForegroundColor White
    Write-Host "0. Выход" -ForegroundColor White
    
    $choice = Read-Host "`nВыберите опцию"
    
    switch ($choice) {
        "1" { Set-GitCredentials }
        "2" { Set-GitHubToken }
        "3" { Set-SSHKeys }
        "4" { Create-AutoCommitScript }
        "5" { Create-TaskScheduler }
        "6" { Test-Connection }
        "7" { 
            Set-GitCredentials
            Set-GitHubToken
            Test-Connection
            Create-AutoCommitScript
            Write-Host "`n🎉 Полная настройка завершена!" -ForegroundColor Green
        }
        "0" { Write-Host "👋 До свидания!" -ForegroundColor Green }
        default { Write-Host "❌ Неверная опция" -ForegroundColor Red }
    }
}

Write-Host "`nНажмите любую клавишу для выхода..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
