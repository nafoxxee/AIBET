# Полностью автоматическая настройка GitHub без запросов
# Запускать от имени администратора

param(
    [switch]$Force,
    [switch]$Test
)

# Установка политики выполнения
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

Write-Host "🚀 ПОЛНАЯ АВТОМАТИЗАЦИЯ GITHUB" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "⚡ Больше НИКОГДА не будет запросов пароля!" -ForegroundColor Yellow
Write-Host ""

function Invoke-SilentCommand {
    param([string]$Command)
    try {
        $result = Invoke-Expression $Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            return $true, $result
        } else {
            return $false, $result
        }
    }
    catch {
        return $false, $_.Exception.Message
    }
}

function Set-GitConfig {
    Write-Host "🔧 Настройка Git конфигурации..." -ForegroundColor Yellow
    
    $configs = @{
        "user.name" = "AI BET Platform"
        "user.email" = "aibet@platform.com"
        "credential.helper" = "store"
        "credential.store" = "store"
        "push.default" = "simple"
        "pull.rebase" = "false"
        "core.autocrlf" = "true"
        "init.defaultBranch" = "main"
    }
    
    foreach ($key in $configs.Keys) {
        $value = $configs[$key]
        Invoke-SilentCommand "git config --global $key `"$value`""
    }
    
    Write-Host "✅ Git конфигурация настроена" -ForegroundColor Green
}

function Set-GitHubCredentials {
    Write-Host "🔑 Создание учетных данных GitHub..." -ForegroundColor Yellow
    
    $token = "8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4"
    $credPath = "$env:USERPROFILE\.git-credentials"
    
    # Создаем файл учетных данных
    "https://$token@github.com" | Out-File -FilePath $credPath -Encoding UTF8 -Force
    
    # Устанавливаем права доступа
    $acl = Get-Acl $credPath
    $acl.SetAccessRuleProtection($true, $false)
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($env:USERNAME, "FullControl", "Allow")
    $acl.SetAccessRule($rule)
    Set-Acl $credPath $acl
    
    Write-Host "✅ Учетные данные GitHub сохранены" -ForegroundColor Green
}

function Set-GitRemote {
    Write-Host "📡 Настройка remote..." -ForegroundColor Yellow
    
    $token = "8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4"
    $repoUrl = "https://$token@github.com/nafoxxee/AIBET.git"
    
    Set-Location "c:\AI BET\AI BET\aibet-analytics-platform"
    
    Invoke-SilentCommand "git remote remove origin"
    Invoke-SilentCommand "git remote add origin $repoUrl"
    
    Write-Host "✅ Remote настроен с токеном" -ForegroundColor Green
}

function Set-SSHKeys {
    Write-Host "🔐 Настройка SSH ключей..." -ForegroundColor Yellow
    
    $sshDir = "$env:USERPROFILE\.ssh"
    if (-not (Test-Path $sshDir)) {
        New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    }
    
    $privateKey = "$sshDir\id_rsa_github"
    
    if (-not (Test-Path $privateKey)) {
        # Генерируем SSH ключи
        ssh-keygen -t rsa -b 4096 -C "aibet@platform.com" -f $privateKey -N ""
        
        # Настраиваем SSH config
        $sshConfig = "$sshDir\config"
        $configContent = @"
# GitHub Configuration
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa_github
    IdentitiesOnly yes
    StrictHostKeyChecking no
"@
        
        $configContent | Out-File -FilePath $sshConfig -Encoding UTF8 -Force
        Write-Host "✅ SSH ключи сгенерированы" -ForegroundColor Green
    } else {
        Write-Host "✅ SSH ключи уже существуют" -ForegroundColor Green
    }
}

function New-AutoScripts {
    Write-Host "🤖 Создание скриптов автоматизации..." -ForegroundColor Yellow
    
    # Скрипт автопуша
    $autoPushScript = "$env:USERPROFILE\auto_push.ps1"
    $scriptContent = @'
# Автоматический push в GitHub
param([string]$Message = "")

try {
    Set-Location "c:\AI BET\AI BET\aibet-analytics-platform"
    
    # Добавляем изменения
    git add .
    
    # Проверяем статус
    $status = git status --porcelain
    
    if ($status) {
        if (-not $Message) {
            $Message = "Auto-update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        }
        
        git commit -m $Message
        git push origin main
        
        Write-Host "✅ Автоматический push успешен: $Message" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ Нет изменений для push" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ Ошибка автопуша: $_" -ForegroundColor Red
}
'@
    
    $scriptContent | Out-File -FilePath $autoPushScript -Encoding UTF8 -Force
    
    Write-Host "✅ Скрипты созданы: $autoPushScript" -ForegroundColor Green
}

function Set-GitAliases {
    Write-Host "⚡ Настройка алиасов..." -ForegroundColor Yellow
    
    $aliases = @{
        "gp" = "git push origin main"
        "ga" = "git add ."
        "gc" = "git commit -m"
        "gs" = "git status"
        "gl" = "git pull origin main"
        "auto" = "powershell -ExecutionPolicy Bypass -File `"$env:USERPROFILE\auto_push.ps1`""
    }
    
    foreach ($alias in $aliases.Keys) {
        $command = $aliases[$alias]
        Invoke-SilentCommand "git config --global alias.$alias `"$command`""
    }
    
    Write-Host "✅ Алиасы настроены" -ForegroundColor Green
}

function New-TaskScheduler {
    Write-Host "⏰ Создание планировщика задач..." -ForegroundColor Yellow
    
    try {
        $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$env:USERPROFILE\auto_push.ps1`""
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 30)
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        
        Register-ScheduledTask -TaskName "AI BET Auto Push" -Action $action -Trigger $trigger -Settings $settings -User $env:USERNAME -Force
        
        Write-Host "✅ Планировщик создан (каждые 30 минут)" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ Ошибка планировщика: $_" -ForegroundColor Yellow
    }
}

function Test-Connection {
    Write-Host "🔍 Тестирование подключения..." -ForegroundColor Yellow
    
    try {
        Set-Location "c:\AI BET\AI BET\aibet-analytics-platform"
        $result = git ls-remote origin
        
        if ($result) {
            Write-Host "✅ Подключение к GitHub успешно!" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Ошибка подключения" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Ошибка теста: $_" -ForegroundColor Red
        return $false
    }
}

function Set-Environment {
    Write-Host "🌍 Настройка окружения..." -ForegroundColor Yellow
    
    # Добавляем в PATH если нужно
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    $gitPath = "C:\Program Files\Git\cmd"
    
    if ($currentPath -notlike "*$gitPath*") {
        [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$gitPath", "User")
        Write-Host "✅ Git добавлен в PATH" -ForegroundColor Green
    }
}

# Основная функция
function Main {
    if (-not $Force) {
        Write-Host "⚠️  Этот скрипт изменит настройки Git и GitHub" -ForegroundColor Red
        Write-Host "   Продолжить? (y/n)" -ForegroundColor Yellow
        $confirm = Read-Host
        if ($confirm -ne "y") {
            Write-Host "👋 Отменено" -ForegroundColor Yellow
            return
        }
    }
    
    try {
        Set-Environment
        Set-GitConfig
        Set-GitHubCredentials
        Set-GitRemote
        Set-SSHKeys
        New-AutoScripts
        Set-GitAliases
        New-TaskScheduler
        
        if (Test-Connection) {
            Write-Host ""
            Write-Host "🎉 ПОЛНАЯ АВТОМАТИЗАЦИЯ GITHUB ЗАВЕРШЕНА!" -ForegroundColor Green
            Write-Host "======================================" -ForegroundColor Green
            Write-Host "✅ Теперь используйте команды:" -ForegroundColor Cyan
            Write-Host "   gp        - git push origin main" -ForegroundColor White
            Write-Host "   ga        - git add ." -ForegroundColor White
            Write-Host "   gc 'msg'  - git commit -m 'msg'" -ForegroundColor White
            Write-Host "   gs        - git status" -ForegroundColor White
            Write-Host "   gl        - git pull origin main" -ForegroundColor White
            Write-Host "   auto      - автоматический push" -ForegroundColor White
            Write-Host ""
            Write-Host "🔓 БОЛЬШЕ НИКОГДА НЕ БУДЕТ ЗАПРОСОВ ПАРОЛЯ!" -ForegroundColor Green
            Write-Host "⏰ Автопуш каждые 30 минут" -ForegroundColor Yellow
        } else {
            Write-Host "❌ Настройка завершена с ошибками" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ Критическая ошибка: $_" -ForegroundColor Red
    }
}

# Запуск
if ($Test) {
    Test-Connection
} else {
    Main
}

Write-Host ""
Write-Host "Нажмите любую клавишу для выхода..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
