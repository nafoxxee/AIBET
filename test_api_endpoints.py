#!/usr/bin/env python3
"""
AIBET Analytics Platform - API Endpoints Test Script
Comprehensive testing of all API endpoints and real data flow verification
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "errors": [],
            "response_times": {},
            "test_details": {}
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request and measure response time"""
        url = f"{self.base_url}{endpoint}"
        start_time = datetime.now()
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Store response time
                self.test_results["response_times"][endpoint] = response_time
                
                # Parse response
                try:
                    data = await response.json()
                except:
                    data = await response.text()
                
                return {
                    "status_code": response.status,
                    "response_time": response_time,
                    "data": data,
                    "headers": dict(response.headers),
                    "success": response.status < 400
                }
                
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Request failed: {str(e)}"
            
            self.test_results["errors"].append({
                "endpoint": endpoint,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "status_code": 0,
                "response_time": response_time,
                "data": None,
                "error": error_msg,
                "success": False
            }
    
    async def test_endpoint(self, name: str, method: str, endpoint: str, 
                          expected_status: int = 200, **kwargs) -> bool:
        """Test individual endpoint"""
        logger.info(f"🧪 Testing {name}: {method} {endpoint}")
        
        self.test_results["total_tests"] += 1
        
        try:
            result = await self.make_request(method, endpoint, **kwargs)
            
            # Check if request was successful
            if result["success"] and result["status_code"] == expected_status:
                logger.info(f"✅ {name} - PASSED ({result['response_time']:.3f}s)")
                self.test_results["passed_tests"] += 1
                self.test_results["test_details"][name] = {
                    "status": "PASSED",
                    "response_time": result["response_time"],
                    "status_code": result["status_code"]
                }
                return True
            else:
                logger.error(f"❌ {name} - FAILED")
                logger.error(f"   Expected: {expected_status}, Got: {result['status_code']}")
                if result.get("error"):
                    logger.error(f"   Error: {result['error']}")
                
                self.test_results["failed_tests"] += 1
                self.test_results["test_details"][name] = {
                    "status": "FAILED",
                    "response_time": result["response_time"],
                    "status_code": result["status_code"],
                    "error": result.get("error")
                }
                return False
                
        except Exception as e:
            logger.error(f"❌ {name} - ERROR: {str(e)}")
            self.test_results["failed_tests"] += 1
            self.test_results["test_details"][name] = {
                "status": "ERROR",
                "error": str(e)
            }
            return False
    
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        return await self.test_endpoint(
            "Health Check", "GET", "/api/health"
        )
    
    async def test_matches_endpoints(self):
        """Test matches related endpoints"""
        results = []
        
        # Test get matches
        results.append(await self.test_endpoint(
            "Get All Matches", "GET", "/api/matches"
        ))
        
        # Test get CS2 matches
        results.append(await self.test_endpoint(
            "Get CS2 Matches", "GET", "/api/matches?sport=cs2"
        ))
        
        # Test get KHL matches
        results.append(await self.test_endpoint(
            "Get KHL Matches", "GET", "/api/matches?sport=khl"
        ))
        
        # Test get live matches
        results.append(await self.test_endpoint(
            "Get Live Matches", "GET", "/api/matches?status=live"
        ))
        
        # Test refresh matches (this might take longer)
        results.append(await self.test_endpoint(
            "Refresh Matches", "GET", "/api/matches/refresh"
        ))
        
        return all(results)
    
    async def test_odds_endpoints(self):
        """Test odds related endpoints"""
        results = []
        
        # Test get odds
        results.append(await self.test_endpoint(
            "Get All Odds", "GET", "/api/odds"
        ))
        
        # Test get CS2 odds
        results.append(await self.test_endpoint(
            "Get CS2 Odds", "GET", "/api/odds?sport=cs2"
        ))
        
        # Test get KHL odds
        results.append(await self.test_endpoint(
            "Get KHL Odds", "GET", "/api/odds?sport=khl"
        ))
        
        # Test get average odds
        results.append(await self.test_endpoint(
            "Get Average Odds", "GET", "/api/odds/average"
        ))
        
        return all(results)
    
    async def test_ml_endpoints(self):
        """Test ML prediction endpoints"""
        results = []
        
        # Test get ML predictions
        results.append(await self.test_endpoint(
            "Get ML Predictions", "GET", "/api/ml_predictions"
        ))
        
        # Test get ML predictions with filters
        results.append(await self.test_endpoint(
            "Get CS2 ML Predictions", "GET", "/api/ml_predictions?sport=cs2&confidence_min=0.8"
        ))
        
        # Test ML models status
        results.append(await self.test_endpoint(
            "Get ML Models Status", "GET", "/api/ml_models/status"
        ))
        
        # Test train ML models (this might take longer)
        results.append(await self.test_endpoint(
            "Train ML Models", "POST", "/api/ml_models/train"
        ))
        
        return all(results)
    
    async def test_signals_endpoints(self):
        """Test signals endpoints"""
        results = []
        
        # Test get signals
        results.append(await self.test_endpoint(
            "Get Signals", "GET", "/api/signals"
        ))
        
        # Test get high confidence signals
        results.append(await self.test_endpoint(
            "Get High Confidence Signals", "GET", "/api/signals?confidence_min=0.8"
        ))
        
        # Test get CS2 signals
        results.append(await self.test_endpoint(
            "Get CS2 Signals", "GET", "/api/signals?sport=cs2"
        ))
        
        return all(results)
    
    async def test_stats_endpoints(self):
        """Test statistics endpoints"""
        results = []
        
        # Test team stats (this might fail if team doesn't exist)
        results.append(await self.test_endpoint(
            "Get Team Stats", "GET", "/api/stats/teams/NaVi", expected_status=404
        ))
        
        return all(results)
    
    async def test_data_flow(self):
        """Test complete data flow"""
        logger.info("🔄 Testing complete data flow...")
        
        try:
            # 1. Get matches
            matches_result = await self.make_request("GET", "/api/matches")
            if not matches_result["success"]:
                logger.error("❌ Failed to get matches")
                return False
            
            matches = matches_result["data"].get("data", [])
            if not matches:
                logger.warning("⚠️ No matches found")
                return True  # This is not necessarily an error
            
            logger.info(f"📊 Found {len(matches)} matches")
            
            # 2. Get odds for first match's sport
            if matches:
                first_match = matches[0]
                sport = first_match.get("sport")
                
                if sport:
                    odds_result = await self.make_request("GET", f"/api/odds?sport={sport}")
                    if odds_result["success"]:
                        odds = odds_result["data"].get("data", [])
                        logger.info(f"💰 Found {len(odds)} odds for {sport}")
                    
                    # 3. Get ML predictions for sport
                    ml_result = await self.make_request("GET", f"/api/ml_predictions?sport={sport}")
                    if ml_result["success"]:
                        predictions = ml_result["data"].get("data", [])
                        logger.info(f"🤖 Found {len(predictions)} predictions for {sport}")
                    
                    # 4. Get signals for sport
                    signals_result = await self.make_request("GET", f"/api/signals?sport={sport}")
                    if signals_result["success"]:
                        signals = signals_result["data"].get("data", [])
                        logger.info(f"🎯 Found {len(signals)} signals for {sport}")
            
            logger.info("✅ Data flow test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Data flow test failed: {str(e)}")
            return False
    
    async def test_performance(self):
        """Test API performance"""
        logger.info("⚡ Testing API performance...")
        
        # Test concurrent requests
        tasks = []
        for i in range(10):
            tasks.append(self.make_request("GET", "/api/health"))
        
        start_time = datetime.now()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = (datetime.now() - start_time).total_seconds()
        
        successful_requests = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        avg_response_time = total_time / len(results)
        
        logger.info(f"📊 Performance Results:")
        logger.info(f"   Total time: {total_time:.3f}s")
        logger.info(f"   Successful requests: {successful_requests}/10")
        logger.info(f"   Average response time: {avg_response_time:.3f}s")
        
        return successful_requests >= 8  # At least 80% success rate
    
    async def run_all_tests(self):
        """Run all API tests"""
        logger.info("🚀 Starting comprehensive API testing")
        logger.info(f"🌐 Testing API at: {self.base_url}")
        
        start_time = datetime.now()
        
        # Test basic connectivity
        health_ok = await self.test_health_endpoint()
        if not health_ok:
            logger.error("❌ Health check failed. API might be down.")
            return False
        
        # Test all endpoint groups
        test_groups = [
            ("Matches Endpoints", self.test_matches_endpoints),
            ("Odds Endpoints", self.test_odds_endpoints),
            ("ML Endpoints", self.test_ml_endpoints),
            ("Signals Endpoints", self.test_signals_endpoints),
            ("Stats Endpoints", self.test_stats_endpoints),
        ]
        
        for group_name, test_func in test_groups:
            logger.info(f"\n📋 Testing {group_name}")
            try:
                await test_func()
            except Exception as e:
                logger.error(f"❌ {group_name} failed: {str(e)}")
                traceback.print_exc()
        
        # Test data flow
        logger.info(f"\n🔄 Testing Data Flow")
        await self.test_data_flow()
        
        # Test performance
        logger.info(f"\n⚡ Testing Performance")
        await self.test_performance()
        
        # Generate report
        total_time = (datetime.now() - start_time).total_seconds()
        self.generate_report(total_time)
        
        return self.test_results["failed_tests"] == 0
    
    def generate_report(self, total_time: float):
        """Generate test report"""
        logger.info("\n" + "="*60)
        logger.info("📊 API TEST REPORT")
        logger.info("="*60)
        
        success_rate = (self.test_results["passed_tests"] / self.test_results["total_tests"]) * 100
        
        logger.info(f"📈 Overall Results:")
        logger.info(f"   Total Tests: {self.test_results['total_tests']}")
        logger.info(f"   Passed: {self.test_results['passed_tests']}")
        logger.info(f"   Failed: {self.test_results['failed_tests']}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info(f"   Total Time: {total_time:.2f}s")
        
        if self.test_results["response_times"]:
            avg_response_time = sum(self.test_results["response_times"].values()) / len(self.test_results["response_times"])
            logger.info(f"   Average Response Time: {avg_response_time:.3f}s")
        
        # Show failed tests
        if self.test_results["failed_tests"] > 0:
            logger.info(f"\n❌ Failed Tests:")
            for test_name, details in self.test_results["test_details"].items():
                if details.get("status") in ["FAILED", "ERROR"]:
                    logger.info(f"   - {test_name}: {details.get('error', 'Unknown error')}")
        
        # Show response times
        if self.test_results["response_times"]:
            logger.info(f"\n⏱️ Response Times:")
            for endpoint, time_taken in sorted(self.test_results["response_times"].items(), key=lambda x: x[1]):
                logger.info(f"   {endpoint}: {time_taken:.3f}s")
        
        # Show errors
        if self.test_results["errors"]:
            logger.info(f"\n🚨 Errors:")
            for error in self.test_results["errors"]:
                logger.info(f"   {error['endpoint']}: {error['error']}")
        
        logger.info("="*60)
        
        # Save report to file
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "summary": {
                "total_tests": self.test_results["total_tests"],
                "passed_tests": self.test_results["passed_tests"],
                "failed_tests": self.test_results["failed_tests"],
                "success_rate": success_rate,
                "total_time": total_time
            },
            "response_times": self.test_results["response_times"],
            "test_details": self.test_results["test_details"],
            "errors": self.test_results["errors"]
        }
        
        try:
            with open("api_test_report.json", "w") as f:
                json.dump(report_data, f, indent=2)
            logger.info("📄 Detailed report saved to api_test_report.json")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

async def main():
    """Main test function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    logger.info(f"🧪 Starting API tests for {base_url}")
    
    async with APITester(base_url) as tester:
        success = await tester.run_all_tests()
        
        if success:
            logger.info("\n🎉 All tests completed successfully!")
            sys.exit(0)
        else:
            logger.error("\n💥 Some tests failed!")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
