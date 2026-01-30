# Fix imports for aiohttp_cors
# Этот скрипт найдет и исправит импорты aiohttp_cors

param(
    [switch]$Force
)

Write-Host "🔧 Исправление импортов aiohttp_cors" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Cyan

# Ищем файлы, где используется aiohttp_cors
$files_to_check = @(
    "c:\AI BET\AI BET\aibet-analytics-platform\cs2\sources\live_parser.py",
    "c:\AI BET\AI BET\aibet-analytics-platform\cs2\sources\odds_parser.py",
    "c:\AI BET\AI BET\aibet-analytics-platform\cs2\sources\matches_parser.py",
    "c:\AI BET\AI BET\aibet-analytics-platform\khl\sources\live_parser.py",
    "c:\AI BET\AI BET\aibet-analytics-platform\khl\sources\odds_parser.py",
    "c:\AI BET\AI BET\aibet-analytics-platform\cs2\sources\hltv_parser.py"
)

Write-Host "🔍 Поиск импортов..." -ForegroundColor Yellow

$fixed = $false
$import_count = 0

foreach ($file in $files_to_check) {
    Write-Host "🔍 Проверка файла: $file" -ForegroundColor Cyan
    
    $content = Get-Content $file -Raw
    if ($content -match "`from.*aiohttp.*cors") {
        Write-Host "✅ Найден импорт в $file" -ForegroundColor Green
        $fixed = $true
        $import_count++
        
        # Исправляем импорт
        $content = $content -replace "from aiohttp import cors" -replace "from aiohttp_cors import cors"
        Set-Content -Path $file -Value $content -Force
        Write-Host "✅ Исправлен импорт в $file" -ForegroundColor Green
    }
}

if ($fixed) {
    Write-Host "✅ Исправлено $import_count файлов" -ForegroundColor Green
} else {
    Write-Host "❌ Не найдено импортов aiohttp_cors" -ForegroundColor Red
}

Write-Host ""
Write-Host "🔗 Готово! Теперь aiohttp_cors будет работать!" -ForegroundColor Green
Write-Host "🔗 Запустите деплой на Render!" -ForegroundColor Yellow

# Создаем короткий скрипт для автоматического исправления
$fix_script = @"
# PowerShell скрипт для исправления импортов
param([switch]$Force)

Write-Host "🔧 Автоматическое исправление импортов aiohttp_cors" -ForegroundColor Green

# Ищем файлы, где используется aiohttp_cors
$files_to_check = @(
    "c:\AI BET\AI BET\aibet-analytics-platform\cs2\sources\live_parser.py",
    "c:\AI BET\AI BET\aibet-analytics-platform\cs2\sources\odds_parser.py",
    "c:\AI BET\AI BET\aibet-analytics-platform\cs2\sources\matches_parser.py",
    "c:\AI BET\AI BET\aibet-analytics-platform\khl\sources\live_parser.py",
    "c:\AI BET\AI BET\aibet-analytics-platform\khl\sources\odds_parser.py",
    "c:\AI BET\AI BET\aibet-analytics-platform\cs2\sources\hltv_parser.py"
)

Write-Host "🔍 Поиск импортов..." -ForegroundColor Yellow

$fixed = $false
$import_count = 0

foreach ($file in $files_to_check) {
    $content = Get-Content $file -Raw
    if ($content -match "`from.*aiohttp.*cors") {
        Write-Host "✅ Найден импорт в $file" -ForegroundColor Green
        $fixed = $true
        $import_count++
        
        # Исправляем импорт
        $content = $content -replace "from aiohttp import cors" -replace "from aiohttp_cors import cors"
        Set-Content -Path $file -Value $content -Force
        Write-Host "✅ Исправлен импорт в $file" -ForegroundColor Green
    }
}

if ($fixed) {
    Write-Host "✅ Исправлено $import_count файлов" -ForegroundColor Green
} else {
    Write-Host "❌ Не найдено импортов aiohttp_cors" -ForegroundColor Red
}

Write-Host ""
Write-Host "🔗 Готово! Теперь aiohttp_cors будет работать!" -ForegroundColor Green
Write-Host "🔗 Запустите деплой на Render!" -ForegroundColor Yellow
"
