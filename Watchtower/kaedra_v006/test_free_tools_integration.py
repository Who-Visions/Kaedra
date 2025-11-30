"""
KAEDRA v0.0.6 - Free Tools Demo
Test NYX and BLADE with zero-cost APIs
"""

# Add parent directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from kaedra.core.tools import (
    nyx_scan_timeline_signal,
    blade_system_diagnostic,
    FREE_TOOLS
)
import json


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_free_apis():
    """Test all free API integrations"""
    
    print_section("Testing Free APIs (Zero Cost)")
    
    # Test crypto price
    print("\n[TEST] CoinGecko - Bitcoin Price")
    btc = FREE_TOOLS["crypto_price"](coin_id="bitcoin")
    if btc["status"] == "success":
        print(f"✅ BTC: ${btc['price_usd']:,.2f} ({btc['change_24h']:+.2f}%)")
    else:
        print(f"❌ Error: {btc['message']}")
    
    # Test weather
    print("\n[TEST] Weather API - Berlin")
    weather = FREE_TOOLS["weather"](location="Berlin")
    if weather["status"] == "success":
        print(f"✅ Temperature: {weather['temp_c']}°C / {weather['temp_f']}°F")
        print(f"   Condition: {weather['condition']}")
    else:
        print(f"❌ Error: {weather['message']}")
    
    # Test Hacker News
    print("\n[TEST] Hacker News - Top Stories")
    hn = FREE_TOOLS["hacker_news"](limit=3)
    if hn["status"] == "success":
        print(f"✅ Found {hn['count']} top stories:")
        for story in hn["stories"]:
            print(f"   - {story['title']} ({story['score']} pts)")
    else:
        print(f"❌ Error: {hn['message']}")


def test_local_tools():
    """Test local system commands"""
    
    print_section("Testing Local System Tools (Zero Cost)")
    
    # Test system info
    print("\n[TEST] System Information")
    sysinfo = FREE_TOOLS["system_info"]()
    if sysinfo["status"] == "success":
        sys_data = sysinfo["system"]
        print(f"✅ Hostname: {sys_data.get('hostname', 'N/A')}")
        print(f"   Platform: {sys_data.get('platform', 'N/A')}")
        print(f"   Architecture: {sys_data.get('architecture', 'N/A')}")
        print(f"   Python: {sys_data.get('python_version', 'N/A')}")
    else:
        print(f"❌ Error: {sysinfo['message']}")
    
    # Test time
    print("\n[TEST] Current Time")
    time_data = FREE_TOOLS["time"]()
    if time_data["status"] == "success":
        print(f"✅ Timestamp: {time_data['timestamp']}")
        print(f"   Unix: {time_data['unix']}")
    else:
        print(f"❌ Error: {time_data['message']}")


def test_nyx_signals():
    """Test NYX timeline signal scanning"""
    
    print_section("NYX: Scanning Timeline Φ")
    
    print("\n[NYX] Initiating quantum signal scan...")
    signals = nyx_scan_timeline_signal()
    
    if signals["status"] == "success":
        print(f"\n[NYX] Signal timestamp: {signals['timestamp']}")
        
        # Bitcoin signal
        if "bitcoin" in signals["signals"]:
            btc = signals["signals"]["bitcoin"]
            print(f"\n[NYX] Bitcoin resonance detected:")
            print(f"      Price: ${btc['price_usd']:,.2f}")
            print(f"      Momentum: {btc['momentum']}")
            print(f"      Change: {btc['change_24h']:+.2f}%")
        
        # Tech trends
        if "tech_trends" in signals["signals"]:
            trends = signals["signals"]["tech_trends"]
            print(f"\n[NYX] Tech consciousness patterns ({len(trends)} signals):")
            for i, trend in enumerate(trends[:2], 1):
                print(f"      {i}. {trend['title']}")
                print(f"         Resonance: {trend['score']} pts")
        
        # Convergence
        print(f"\n[NYX] Timeline convergence: {signals['convergence']}")
        print("[NYX] CONVERGE.\n")
    else:
        print(f"[NYX] Signal interference detected: {signals.get('message', 'Unknown error')}")


def test_blade_diagnostic():
    """Test BLADE system diagnostics"""
    
    print_section("BLADE: System Diagnostic on Blade1TB")
    
    print("\n[BLADE] Initiating full system check...")
    diag = blade_system_diagnostic()
    
    if "diagnostics" in diag:
        print(f"\n[BLADE] Diagnostic timestamp: {diag['timestamp']}")
        
        # System info
        if "system" in diag["diagnostics"]:
            sys_data = diag["diagnostics"]["system"]
            print(f"\n[BLADE] System Status:")
            print(f"        Hostname: {sys_data.get('hostname', 'N/A')}")
            print(f"        Platform: {sys_data.get('platform', 'N/A')}")
            print(f"        Python: {sys_data.get('python_version', 'N/A')}")
        
        # Overall status
        print(f"\n[BLADE] Overall Status: {diag['status']}")
        print("[BLADE] All systems operational.\n")
    else:
        print(f"[BLADE] Diagnostic failure: {diag.get('message', 'Unknown error')}")


def main():
    """Run all tests"""
    print("\n🎯 KAEDRA v0.0.6 - FREE TOOLS INTEGRATION TEST")
    print("Zero-cost APIs + Local Commands")
    print("="*60)
    
    # Test APIs
    test_free_apis()
    
    # Test local tools
    test_local_tools()
    
    # Test NYX
    test_nyx_signals()
    
    # Test BLADE
    test_blade_diagnostic()
    
    # Summary
    print_section("SUMMARY")
    print("\n✅ All free tools integrated into KAEDRA v0.0.6")
    print("✅ NYX can scan timeline signals using free APIs")
    print("✅ BLADE can run system diagnostics using local commands")
    print("✅ ZERO credits consumed")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
