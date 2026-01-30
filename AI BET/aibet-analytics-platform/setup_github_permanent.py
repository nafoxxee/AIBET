#!/usr/bin/env python3
"""
GitHub Permanent Setup Script
Настраивает постоянное подключение к GitHub с сохранением учетных данных
"""

import os
import subprocess
import json
from pathlib import Path

def run_command(command, check=True):
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip()

def setup_git_credentials():
    """Настраивает учетные данные Git"""
    print("🔧 Настройка учетных данных Git...")
    
    # Получаем имя пользователя
    name = input("Введите ваше имя для Git: ").strip()
    if not name:
        name = "AI BET Developer"
    
    # Получаем email
    email = input("Введите ваш email для Git: ").strip()
    if not email:
        email = "aibet@example.com"
    
    # Настраиваем глобальные настройки
    run_command(f'git config --global user.name "{name}"')
    run_command(f'git config --global user.email "{email}"')
    
    print(f"✅ Учетные данные настроены: {name} <{email}>")

def setup_github_token():
    """Настраивает токен GitHub для аутентификации"""
    print("\n🔑 Настройка токена GitHub...")
    
    print("1. Перейдите на https://github.com/settings/tokens")
    print("2. Нажмите 'Generate new token (classic)'")
    print("3. Выберите 'repo' permissions")
    print("4. Сгенерируйте токен и скопируйте его")
    
    token = input("Введите ваш GitHub Personal Access Token: ").strip()
    
    if not token:
        print("❌ Токен не введен. Пропускаем настройку.")
        return False
    
    # Сохраняем токен в Git credential helper
    repo_url = "https://github.com/nafoxxee/AIBET.git"
    token_url = f"https://{token}@github.com/nafoxxee/AIBET.git"
    
    # Настраиваем remote с токеном
    run_command("git remote remove origin")
    run_command(f"git remote add origin {token_url}")
    
    # Настраиваем credential helper для сохранения токена
    run_command('git config --global credential.helper store')
    
    # Создаем файл с учетными данными
    cred_file = Path.home() / ".git-credentials"
    with open(cred_file, 'w') as f:
        f.write(f"https://{token}@github.com\n")
    
    # Устанавливаем права доступа к файлу
    os.chmod(cred_file, 0o600)
    
    print("✅ Токен GitHub сохранен")
    return True

def setup_ssh_keys():
    """Настраивает SSH ключи для GitHub"""
    print("\n🔐 Настройка SSH ключей...")
    
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(exist_ok=True)
    
    private_key = ssh_dir / "id_rsa_github"
    public_key = ssh_dir / "id_rsa_github.pub"
    
    if private_key.exists():
        print("📋 SSH ключ уже существует:")
        with open(public_key, 'r') as f:
            print(f"Public key:\n{f.read()}")
        
        add_to_ssh_config = input("Добавить ключ в SSH config? (y/n): ").lower()
        if add_to_ssh_config == 'y':
            setup_ssh_config()
        return
    
    # Генерируем новый SSH ключ
    email = input("Введите email для SSH ключа: ").strip()
    if not email:
        email = "aibet@example.com"
    
    print("🔄 Генерация SSH ключа...")
    run_command(f'ssh-keygen -t rsa -b 4096 -C "{email}" -f "{private_key}" -N ""')
    
    # Показываем публичный ключ
    with open(public_key, 'r') as f:
        pub_key = f.read()
    
    print(f"\n📋 Ваш публичный SSH ключ:")
    print("=" * 50)
    print(pub_key)
    print("=" * 50)
    
    print("\n1. Скопируйте ключ выше")
    print("2. Перейдите на https://github.com/settings/keys")
    print("3. Нажмите 'New SSH key'")
    print("4. Вставьте ключ и сохраните")
    
    input("Нажмите Enter после добавления ключа на GitHub...")
    
    setup_ssh_config()

def setup_ssh_config():
    """Настраивает SSH config"""
    ssh_config = Path.home() / ".ssh" / "config"
    
    config_content = """
# GitHub Configuration
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa_github
    IdentitiesOnly yes
"""
    
    with open(ssh_config, 'a') as f:
        f.write(config_content)
    
    print("✅ SSH config настроен")

def setup_auto_commit():
    """Настраивает автоматические коммиты"""
    print("\n🤖 Настройка автоматических коммитов...")
    
    # Создаем скрипт для автоматических коммитов
    auto_commit_script = Path.home() / "auto_commit.py"
    
    script_content = '''#!/usr/bin/env python3
"""
Auto Commit Script for AI BET Platform
"""
import subprocess
import datetime
import os

def auto_commit():
    """Автоматический коммит изменений"""
    try:
        # Переходим в директорию проекта
        os.chdir("c:/AI BET/AI BET/aibet-analytics-platform")
        
        # Проверяем есть ли изменения
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        
        if result.stdout.strip():
            # Добавляем все изменения
            subprocess.run(["git", "add", "."], check=True)
            
            # Создаем коммит
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"Auto-commit: {timestamp}"
            
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            
            print(f"✅ Auto-commit successful: {commit_message}")
        else:
            print("ℹ️ No changes to commit")
            
    except Exception as e:
        print(f"❌ Auto-commit failed: {e}")

if __name__ == "__main__":
    auto_commit()
'''
    
    with open(auto_commit_script, 'w') as f:
        f.write(script_content)
    
    print(f"✅ Скрипт автокоммитов создан: {auto_commit_script}")

def create_github_actions():
    """Создает GitHub Actions для автоматического деплоя"""
    print("\n🔄 Создание GitHub Actions...")
    
    workflows_dir = Path("c:/AI BET/AI BET/aibet-analytics-platform/.github/workflows")
    workflows_dir.mkdir(parents=True, exist_ok=True)
    
    deploy_workflow = workflows_dir / "auto-deploy.yml"
    
    workflow_content = '''name: Auto Deploy to Render

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        cd "AI BET/aibet-analytics-platform"
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd "AI BET/aibet-analytics-platform"
        python test_basic.py
    
    - name: Deploy to Render
      run: |
        echo "Triggering Render deployment..."
        curl -X POST "https://api.render.com/v1/services/srv-xxxxxxxxxxxx/deploys" \\
          -H "Authorization: Bearer ${{ secrets.RENDER_API_KEY }}"
'''
    
    with open(deploy_workflow, 'w') as f:
        f.write(workflow_content)
    
    print("✅ GitHub Actions создан")

def main():
    """Главная функция"""
    print("🚀 Permanente GitHub Setup for AI BET Platform")
    print("=" * 50)
    
    # Проверяем что мы в правильной директории
    os.chdir("c:/AI BET/AI BET/aibet-analytics-platform")
    
    while True:
        print("\n📋 Меню настройки:")
        print("1. Настроить учетные данные Git")
        print("2. Настроить токен GitHub (HTTPS)")
        print("3. Настроить SSH ключи")
        print("4. Настроить автокоммиты")
        print("5. Создать GitHub Actions")
        print("6. Проверить подключение")
        print("0. Выход")
        
        choice = input("\nВыберите опцию: ").strip()
        
        if choice == "1":
            setup_git_credentials()
        elif choice == "2":
            setup_github_token()
        elif choice == "3":
            setup_ssh_keys()
        elif choice == "4":
            setup_auto_commit()
        elif choice == "5":
            create_github_actions()
        elif choice == "6":
            test_connection()
        elif choice == "0":
            print("👋 Настройка завершена!")
            break
        else:
            print("❌ Неверная опция")

def test_connection():
    """Тестирует подключение к GitHub"""
    print("\n🔍 Проверка подключения к GitHub...")
    
    # Проверяем SSH подключение
    stdout, stderr = run_command("ssh -T git@github.com")
    if "successfully authenticated" in stderr:
        print("✅ SSH подключение работает")
    else:
        print("❌ SSH подключение не работает")
    
    # Проверяем HTTPS подключение
    stdout, stderr = run_command("git remote -v")
    print(f"📡 Remote URL: {stdout}")
    
    # Проверяем статус репозитория
    stdout, stderr = run_command("git status")
    print(f"📊 Status: {stdout}")

if __name__ == "__main__":
    main()
