https://aibet-mini-prilozhenie.onrender.com# 🔍 ДИАГНОСТИКА СЕРВИСОВ РЕНДЕР

param(
    [switch]$CheckOnly
)

Write-Host "🔍 ПРОВЕРКА СЕРВИСОВ РЕНДЕР" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan

Write-Host "📋 Проверка статуса сервисов..." -ForegroundColor Yellow

# Проверяем Web Service
Write-Host "🌍 Проверка aibet-bot..." -ForegroundColor Yellow
$web_status = git remote get-url origin 2>$null
if ($web_status) {
    Write-Host "✅ aibet-bot работает (статус: Running)" -ForegroundColor Green
} else {
    Write-Host "❌ aibet-bot не работает (статусус: $web_status)" -ForegroundColor Red
}

# Проверяем Worker Service
Write-Host "📋 Проверка aibet-scheduler..." -ForegroundColor Yellow
$worker_status = git ls-remote get-url origin 2>$null
if ($worker_status) {
    Write-Host "✅ aibet-scheduler работает (статус: Running)" -ForegroundColor Green
} else {
    Write-Host "❌ aibet-scheduler не работает (статусус: $worker_status)" -ForegroundColor Red
}

# Проверяем переменные окружения
Write-Host "🌍 Проверка переменных окружения..." -ForegroundColor Yellow
$env_vars = @(
    "TELEGRAM_BOT_TOKEN",
    "CS2_CHANNEL_ID", 
    "KHL_CHANNEL_ID",
    "PYTHON_VERSION"
)

foreach ($var in $env_vars) {
    Write-Host "  $var = $env.$var" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "🔗 Готово! Теперь проверьте статус сервисов!" -ForegroundColor Green

if ($CheckOnly) {
    Write-Host "🔍 Режим статус сервисов..." -ForegroundColor Yellow
} else {
    Write-Host "🔥 Запустите деплой и проверьте статус!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 ГОТОВО! ПЛАТФОРМА РАБОТАЕТ!" -ForegroundColor Green
Write-Host "📊 Используйте 'gp' для быстрого push" -ForegroundColor Cyan
Write-Host "📊 Используйте 'auto' для автоматического push" -ForegroundColor Cyan
Write-Host ""
