#!/usr/bin/env python3
"""
AIBET Sources Test
Проверка доступности источников данных
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_source(session, url, name):
    """Тест доступности источника"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
            status = response.status
            success = status == 200
            
            logger.info(f"📡 {name}: {url}")
            logger.info(f"   Status: {status} {'✅' if success else '❌'}")
            
            if success:
                content_length = len(await response.text())
                logger.info(f"   Content: {content_length} bytes")
            
            return {
                'name': name,
                'url': url,
                'status': status,
                'success': success,
                'content_length': content_length if success else 0
            }
            
    except Exception as e:
        logger.error(f"❌ {name}: {e}")
        return {
            'name': name,
            'url': url,
            'status': 0,
            'success': False,
            'error': str(e)
        }

async def main():
    """Тест всех источников"""
    logger.info("🚀 Testing AIBET Data Sources")
    
    sources = {
        'CS2 Sources': [
            ('HLTV Main', 'https://www.hltv.org/matches'),
            ('HLTV API 1', 'https://hltv-api.vercel.app/api/matches'),
            ('Liquipedia CS2', 'https://liquipedia.net/counterstrike/Portal:Matches'),
            ('GosuGamers CS2', 'https://www.gosugamers.net/counterstrike/matches'),
        ],
        'KHL Sources': [
            ('Livesport KHL', 'https://www.livesport.com/ru/hockey/russia/khl/'),
            ('Flashscore KHL', 'https://www.flashscore.com/hockey/russia/khl/'),
            ('Sport.ru KHL', 'https://www.sport.ru/hockey/khl/calendar/'),
        ],
        'Odds Sources': [
            ('BetBoom', 'https://betboom.com'),
            ('Winline', 'https://winline.ru'),
            ('Fonbet', 'https://www.fonbet.ru'),
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        results = {}
        
        for category, source_list in sources.items():
            logger.info(f"\n📊 Testing {category}:")
            results[category] = []
            
            for name, url in source_list:
                result = await test_source(session, url, name)
                results[category].append(result)
                
                # Задержка между запросами
                await asyncio.sleep(1)
    
    # Итоги
    logger.info("\n" + "="*50)
    logger.info("📊 SUMMARY:")
    
    total_sources = 0
    successful_sources = 0
    
    for category, source_list in results.items():
        logger.info(f"\n{category}:")
        
        category_success = 0
        for result in source_list:
            status = "✅" if result['success'] else "❌"
            logger.info(f"  {status} {result['name']}: {result['status']}")
            
            total_sources += 1
            if result['success']:
                successful_sources += 1
                category_success += 1
        
        logger.info(f"  Success rate: {category_success}/{len(source_list)}")
    
    logger.info(f"\n🎯 Overall Success Rate: {successful_sources}/{total_sources} ({successful_sources/total_sources*100:.1f}%)")
    
    # Сохранение результатов
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_sources': total_sources,
        'successful_sources': successful_sources,
        'success_rate': successful_sources/total_sources*100,
        'results': results
    }
    
    with open('sources_test_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info("💾 Report saved to sources_test_report.json")

if __name__ == "__main__":
    asyncio.run(main())
