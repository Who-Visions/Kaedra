"""
KAEDRA v0.0.6 - Free Tools Module
Zero-cost API integrations for NYX and BLADE
"""

from typing import Dict, Any, Optional
import subprocess
import platform
import json
from datetime import datetime


class FreeToolsRegistry:
    """Registry of all free tool calls (no API keys, no cost)"""
    
    # ============================================
    # PUBLIC FREE APIs (No Auth Required)
    # ============================================
    
    @staticmethod
    def get_crypto_price(coin_id: str = "bitcoin") -> Dict[str, Any]:
        """
        Fetch crypto price from CoinGecko (FREE)
        
        Args:
            coin_id: Coin identifier (bitcoin, ethereum, etc.)
            
        Returns:
            Price data with USD value and 24h change
        """
        try:
            import requests
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            return {
                "coin": coin_id,
                "price_usd": data[coin_id]["usd"],
                "change_24h": data[coin_id].get("usd_24h_change", 0),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except ImportError:
            return {"status": "error", "message": "requests module not installed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def get_exchange_rate(base: str = "USD", target: str = "EUR") -> Dict[str, Any]:
        """
        Get currency exchange rates (FREE)
        
        Args:
            base: Base currency code
            target: Target currency code
            
        Returns:
            Exchange rate data
        """
        try:
            import requests
            url = f"https://api.exchangerate-api.com/v4/latest/{base}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            return {
                "base": base,
                "target": target,
                "rate": data["rates"].get(target, 0),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def get_hacker_news_trends(limit: int = 5) -> Dict[str, Any]:
        """
        Fetch top tech stories from Hacker News (FREE)
        
        Args:
            limit: Number of stories to fetch
            
        Returns:
            List of top stories with titles and scores
        """
        try:
            import requests
            # Get top story IDs
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(url, timeout=5)
            story_ids = response.json()[:limit]
            
            stories = []
            for story_id in story_ids:
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                story_data = requests.get(story_url, timeout=5).json()
                if story_data:
                    stories.append({
                        "title": story_data.get("title", ""),
                        "score": story_data.get("score", 0),
                        "url": story_data.get("url", ""),
                        "by": story_data.get("by", "")
                    })
            
            return {
                "stories": stories,
                "count": len(stories),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def get_weather(location: str = "London") -> Dict[str, Any]:
        """
        Fetch weather from wttr.in (FREE - no API key!)
        
        Args:
            location: City name or coordinates
            
        Returns:
            Current weather conditions
        """
        try:
            import requests
            url = f"https://wttr.in/{location}?format=j1"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            current = data["current_condition"][0]
            return {
                "location": location,
                "temp_c": current["temp_C"],
                "temp_f": current["temp_F"],
                "condition": current["weatherDesc"][0]["value"],
                "humidity": current["humidity"],
                "wind_kmh": current["windspeedKmph"],
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def get_random_advice() -> Dict[str, Any]:
        """Get random advice (FREE)"""
        try:
            import requests
            url = "https://api.adviceslip.com/advice"
            response = requests.get(url, timeout=5)
            data = response.json()
            return {
                "advice": data["slip"]["advice"],
                "id": data["slip"]["id"],
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def get_random_quote() -> Dict[str, Any]:
        """Get inspirational quote (FREE)"""
        try:
            import requests
            url = "https://api.quotable.io/random"
            response = requests.get(url, timeout=5)
            data = response.json()
            return {
                "quote": data["content"],
                "author": data["author"],
                "tags": data.get("tags", []),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # ============================================
    # LOCAL SYSTEM COMMANDS (Blade1TB)
    # ============================================
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """
        Get local system information (FREE - no API)
        
        Returns:
            System details including OS, hostname, architecture
        """
        try:
            if platform.system() == "Windows":
                # Run systeminfo and parse key data
                result = subprocess.run(
                    ["systeminfo"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                info = {
                    "platform": platform.system(),
                    "hostname": platform.node(),
                    "architecture": platform.machine(),
                    "python_version": platform.python_version(),
                }
                
                # Parse systeminfo output
                for line in result.stdout.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        if key in ['OS Name', 'OS Version', 'System Type', 'Total Physical Memory']:
                            info[key] = value.strip()
                
                return {
                    "system": info,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                }
            else:
                # Linux/Mac
                return {
                    "system": {
                        "platform": platform.system(),
                        "hostname": platform.node(),
                        "os": platform.platform(),
                        "architecture": platform.machine(),
                        "python_version": platform.python_version(),
                    },
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def get_disk_info() -> Dict[str, Any]:
        """Get disk space information (FREE - local command)"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "logicaldisk", "get", "caption,size,freespace"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    encoding='utf-8',
                    errors='ignore'
                )
                return {
                    "disk_info": result.stdout,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                }
            else:
                result = subprocess.run(["df", "-h"], capture_output=True, text=True, timeout=5)
                return {
                    "disk_info": result.stdout,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def get_running_processes(limit: int = 10) -> Dict[str, Any]:
        """Get running processes (FREE - local command)"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["tasklist"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    encoding='utf-8',
                    errors='ignore'
                )
                lines = result.stdout.split('\n')[:limit + 5]  # Header + limit
                return {
                    "processes": '\n'.join(lines),
                    "count": limit,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                }
            else:
                result = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
                lines = result.stdout.split('\n')[:limit + 1]
                return {
                    "processes": '\n'.join(lines),
                    "count": limit,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def get_network_info() -> Dict[str, Any]:
        """Get network adapter information (FREE - local command)"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["ipconfig"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    encoding='utf-8',
                    errors='ignore'
                )
            else:
                result = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=5)
            
            return {
                "network_info": result.stdout,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # ============================================
    # UTILITY FUNCTIONS
    # ============================================
    
    @staticmethod
    def get_current_time() -> Dict[str, Any]:
        """Get current timestamp (FREE - no external call)"""
        now = datetime.now()
        return {
            "timestamp": now.isoformat(),
            "unix": int(now.timestamp()),
            "date": now.date().isoformat(),
            "time": now.time().isoformat(),
            "status": "success"
        }
    
    @staticmethod
    def calculate(expression: str) -> Dict[str, Any]:
        """
        Safe calculator (FREE - no external call)
        
        Args:
            expression: Mathematical expression to evaluate
            
        Returns:
            Calculation result
        """
        try:
            # Safe eval - only allow numbers and operators
            allowed_chars = set("0123456789+-*/(). ")
            if not all(c in allowed_chars for c in expression):
                return {"status": "error", "message": "Invalid characters in expression"}
            
            result = eval(expression)
            return {
                "expression": expression,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


# ============================================
# Tool Registry Export
# ============================================

# Import Google tools
try:
    from .google_tools import GOOGLE_TOOLS
    google_tools_available = True
except ImportError:
    GOOGLE_TOOLS = {}
    google_tools_available = False

FREE_TOOLS = {
    # Market & Finance
    "crypto_price": FreeToolsRegistry.get_crypto_price,
    "exchange_rate": FreeToolsRegistry.get_exchange_rate,
    
    # News & Trends
    "hacker_news": FreeToolsRegistry.get_hacker_news_trends,
    
    # Weather
    "weather": FreeToolsRegistry.get_weather,
    
    # Utilities
    "advice": FreeToolsRegistry.get_random_advice,
    "quote": FreeToolsRegistry.get_random_quote,
    "time": FreeToolsRegistry.get_current_time,
    "calculate": FreeToolsRegistry.calculate,
    
    # System (Blade1TB)
    "system_info": FreeToolsRegistry.get_system_info,
    "disk_info": FreeToolsRegistry.get_disk_info,
    "processes": FreeToolsRegistry.get_running_processes,
    "network_info": FreeToolsRegistry.get_network_info,
}

# Add Google tools if available
if google_tools_available:
    FREE_TOOLS.update(GOOGLE_TOOLS)


# ============================================
# NYX-Specific Tools
# ============================================

def nyx_scan_timeline_signal() -> Dict[str, Any]:
    """
    NYX: Scan quantum signals from free APIs + Google Cloud APIs
    Analyzes market data + tech trends + news to assess timeline convergence
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "signals": {}
    }
    
    # Market signal (CoinGecko)
    btc_data = FreeToolsRegistry.get_crypto_price("bitcoin")
    if btc_data["status"] == "success":
        results["signals"]["bitcoin"] = {
            "price_usd": btc_data["price_usd"],
            "momentum": "BULLISH" if btc_data["change_24h"] > 0 else "BEARISH",
            "change_24h": btc_data["change_24h"]
        }
    
    # Tech trends (Hacker News)
    hn_data = FreeToolsRegistry.get_hacker_news_trends(3)
    if hn_data["status"] == "success":
        results["signals"]["tech_trends"] = hn_data["stories"]
    
    # Google News (if available)
    if google_tools_available and "google_news" in GOOGLE_TOOLS:
        try:
            news_data = GOOGLE_TOOLS["google_news"]("AI technology", 3)
            if news_data.get("status") == "success":
                results["signals"]["google_news"] = news_data["articles"]
        except:
            pass  # Failsafe - continue without Google News
    
    # YouTube Trends (if available)
    if google_tools_available and "youtube_trending" in GOOGLE_TOOLS:
        try:
            yt_data = GOOGLE_TOOLS["youtube_trending"]("28", 3)  # Science & Tech category
            if yt_data.get("status") == "success":
                results["signals"]["youtube_trending"] = [
                    {"title": v["title"], "views": v["viewCount"]} 
                    for v in yt_data.get("videos", [])[:3]
                ]
        except:
            pass  # Failsafe
    
    # Convergence assessment
    convergence = "STRONG" if btc_data.get("change_24h", 0) > 1 else "MODERATE"
    results["convergence"] = convergence
    results["status"] = "success"
    
    return results


# ============================================
# BLADE-Specific Tools
# ============================================

def blade_system_diagnostic() -> Dict[str, Any]:
    """
    BLADE: Full system diagnostic on Blade1TB
    Checks system health, resources, and operational status
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "diagnostics": {}
    }
    
    # System info
    sys_data = FreeToolsRegistry.get_system_info()
    if sys_data["status"] == "success":
        results["diagnostics"]["system"] = sys_data["system"]
    
    # Disk info
    disk_data = FreeToolsRegistry.get_disk_info()
    if disk_data["status"] == "success":
        results["diagnostics"]["disk"] = "Available"
    
    # Process count
    proc_data = FreeToolsRegistry.get_running_processes(5)
    if proc_data["status"] == "success":
        results["diagnostics"]["processes"] = "Active"
    
    # Overall status
    results["status"] = "GREEN" if all(
        d != "error" for d in results["diagnostics"].values()
    ) else "YELLOW"
    
    return results


# Export all
__all__ = [
    'FreeToolsRegistry',
    'FREE_TOOLS',
    'nyx_scan_timeline_signal',
    'blade_system_diagnostic'
]
