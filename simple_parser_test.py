#!/usr/bin/env python3
"""
Simple AIBET Parser Test
Базовая проверка источников без внешних зависимостей
"""

import json
import urllib.request
import urllib.error
from datetime import datetime

def test_url(url, name):
    """Тест URL без aiohttp"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.getcode()
            content = response.read()
            
            print(f"✅ {name}: {url}")
            print(f"   Status: {status}")
            print(f"   Content: {len(content)} bytes")
            
            return {
                'name': name,
                'url': url,
                'status': status,
                'success': status == 200,
                'content_length': len(content)
            }
            
    except Exception as e:
        print(f"❌ {name}: {e}")
        return {
            'name': name,
            'url': url,
            'status': 0,
            'success': False,
            'error': str(e)
        }

def main():
    """Основная функция"""
    print("🚀 Testing AIBET Data Sources (Simple)")
    print("="*50)
    
    sources = [
        ('HLTV Main', 'https://www.hltv.org/matches'),
        ('Livesport KHL', 'https://www.livesport.com/ru/hockey/russia/khl/'),
        ('Flashscore KHL', 'https://www.flashscore.com/hockey/russia/khl/'),
        ('BetBoom', 'https://betboom.com'),
        ('Winline', 'https://winline.ru'),
        ('Fonbet', 'https://www.fonbet.ru'),
    ]
    
    results = []
    
    for name, url in sources:
        result = test_url(url, name)
        results.append(result)
        print()
    
    # Итоги
    print("="*50)
    print("📊 SUMMARY:")
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"Success Rate: {successful}/{total} ({successful/total*100:.1f}%)")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['name']}: {result['status']}")
    
    # Сохранение результатов
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_sources': total,
        'successful_sources': successful,
        'success_rate': successful/total*100,
        'results': results
    }
    
    with open('simple_sources_test.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Report saved to simple_sources_test.json")

if __name__ == "__main__":
    main()
