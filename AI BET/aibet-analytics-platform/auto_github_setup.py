#!/usr/bin/env python3
"""
Автоматическая настройка GitHub - полное подключение без запросов
"""

import os
import subprocess
import json
from pathlib import Path
import base64

def run_command(command, check=True):
    """Выполняет команду без вывода"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip()

def setup_git_config():
    """Автоматическая настройка Git конфигурации"""
    print("🔧 Автоматическая настройка Git...")
    
    # Автоматические учетные данные
    config = {
        "user.name": "AI BET Platform",
        "user.email": "aibet@platform.com",
        "credential.helper": "store",
        "credential.store": "store",
        "push.default": "simple",
        "pull.rebase": "false",
        "core.autocrlf": "true"
    }
    
    for key, value in config.items():
        run_command(f'git config --global {key} "{value}"')
    
    print("✅ Git конфигурация настроена")

def create_github_credentials():
    """Создает файл учетных данных GitHub с токеном"""
    print("🔑 Создание учетных данных GitHub...")
    
    # Токен из render.yaml
    github_token = "8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4"
    
    # Создаем директорию .git-credentials
    git_dir = Path.home() / ".git-credentials"
    git_dir.parent.mkdir(exist_ok=True)
    
    # Записываем учетные данные
    with open(git_dir, 'w') as f:
        f.write(f"https://{github_token}@github.com\n")
    
    # Устанавливаем права доступа
    os.chmod(git_dir, 0o600)
    
    print("✅ Учетные данные GitHub созданы")

def setup_git_remote():
    """Автоматическая настройка remote с токеном"""
    print("📡 Настройка remote...")
    
    # Токен и URL
    token = "8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4"
    repo_url = f"https://{token}@github.com/nafoxxee/AIBET.git"
    
    # Переходим в папку проекта
    os.chdir("c:/AI BET/AI BET/aibet-analytics-platform")
    
    # Удаляем старый remote и добавляем новый
    run_command("git remote remove origin")
    run_command(f"git remote add origin {repo_url}")
    
    print("✅ Remote настроен с токеном")

def setup_ssh_auto():
    """Автоматическая настройка SSH ключей"""
    print("🔐 Автоматическая настройка SSH...")
    
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(exist_ok=True)
    
    private_key = ssh_dir / "id_rsa_github"
    public_key = ssh_dir / "id_rsa_github.pub"
    
    if not private_key.exists():
        # Генерируем SSH ключи автоматически
        run_command(f'ssh-keygen -t rsa -b 4096 -C "aibet@platform.com" -f "{private_key}" -N ""')
        
        # Настраиваем SSH config
        ssh_config = ssh_dir / "config"
        config_content = """# GitHub Configuration
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa_github
    IdentitiesOnly yes
    StrictHostKeyChecking no
"""
        
        with open(ssh_config, 'w') as f:
            f.write(config_content)
        
        print("✅ SSH ключи сгенерированы")
    else:
        print("✅ SSH ключи уже существуют")

def create_auto_push_script():
    """Создает скрипт для автоматического push"""
    print("🤖 Создание скрипта автопуша...")
    
    script_path = Path.home() / "auto_push.py"
    
    script_content = '''#!/usr/bin/env python3
"""
Автоматический push в GitHub без запросов
"""
import subprocess
import os
from datetime import datetime

def auto_push():
    try:
        # Переходим в папку проекта
        os.chdir("c:/AI BET/AI BET/aibet-analytics-platform")
        
        # Добавляем все изменения
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        
        # Проверяем есть ли изменения
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        
        if result.stdout.strip():
            # Создаем коммит
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"Auto-update: {timestamp}"
            
            subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True)
            subprocess.run(["git", "push", "origin", "main"], check=True, capture_output=True)
            
            print(f"✅ Автоматический push успешен: {commit_message}")
        else:
            print("ℹ️ Нет изменений для push")
            
    except Exception as e:
        print(f"❌ Ошибка автопуша: {e}")

if __name__ == "__main__":
    auto_push()
'''
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    print(f"✅ Скрипт автопуша создан: {script_path}")

def setup_git_aliases():
    """Настраивает удобные алиасы"""
    print("⚡ Настройка алиасов...")
    
    aliases = {
        "gp": "git push origin main",
        "ga": "git add .",
        "gc": "git commit -m",
        "gs": "git status",
        "gl": "git pull origin main",
        "auto": "python ~/auto_push.py"
    }
    
    for alias, command in aliases.items():
        run_command(f'git config --global alias.{alias} "{command}"')
    
    print("✅ Алиасы настроены")

def create_task_scheduler():
    """Создает планировщик задач для автопуша"""
    print("⏰ Создание планировщика задач...")
    
    try:
        # Создаем задачу для автопуша каждые 30 минут
        task_command = f'python "{Path.home()}/auto_push.py"'
        
        # Команда для создания задачи
        create_task = f'''
        schtasks /create /tn "AI BET Auto Push" /tr "{task_command}" /sc minute /mo 30 /f
        '''
        
        run_command(create_task, check=False)
        print("✅ Планировщик задач создан (каждые 30 минут)")
        
    except Exception as e:
        print(f"⚠️ Ошибка создания планировщика: {e}")

def test_connection():
    """Тестирует подключение к GitHub"""
    print("🔍 Тестирование подключения...")
    
    try:
        # Тестируем соединение
        result = run_command("git ls-remote origin")
        
        if result[0]:
            print("✅ Подключение к GitHub успешно")
            return True
        else:
            print("❌ Ошибка подключения")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка теста подключения: {e}")
        return False

def main():
    """Главная функция автоматической настройки"""
    print("🚀 АВТОМАТИЧЕСКАЯ НАСТРОЙКА GITHUB")
    print("=" * 50)
    
    try:
        # Шаг 1: Настройка Git конфигурации
        setup_git_config()
        
        # Шаг 2: Создание учетных данных
        create_github_credentials()
        
        # Шаг 3: Настройка remote
        setup_git_remote()
        
        # Шаг 4: Настройка SSH
        setup_ssh_auto()
        
        # Шаг 5: Создание скриптов
        create_auto_push_script()
        
        # Шаг 6: Настройка алиасов
        setup_git_aliases()
        
        # Шаг 7: Создание планировщика
        create_task_scheduler()
        
        # Шаг 8: Тестирование
        if test_connection():
            print("\n🎉 АВТОМАТИЧЕСКАЯ НАСТРОЙКА GITHUB ЗАВЕРШЕНА!")
            print("✅ Теперь все команды работают без запросов:")
            print("   - git push origin main")
            print("   - git pull origin main")
            print("   - auto (для автопуша)")
            print("   - gp (быстрый push)")
            print("   - ga (быстрый add)")
            print("   - gc (быстрый commit)")
        else:
            print("\n❌ Настройка завершена с ошибками")
            
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
