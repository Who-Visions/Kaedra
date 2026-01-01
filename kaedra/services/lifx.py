"""
LIFX Smart Light Control Service
Allows Kaedra to control LIFX lights via HTTP API.

API Docs: https://api.developer.lifx.com/reference/introduction
"""

import os
import requests
from typing import Optional, Literal
from urllib.parse import quote
from dataclasses import dataclass


@dataclass
class LightState:
    """Current state of a LIFX light."""
    id: str
    label: str
    power: str  # "on" or "off"
    color: dict  # hue, saturation, kelvin
    brightness: float  # 0.0 to 1.0
    connected: bool
    group: Optional[str] = None
    location: Optional[str] = None


class LIFXService:
    """
    Control LIFX lights via HTTP API.
    
    Usage:
        lifx = LIFXService()
        lifx.set_power("all", "on")
        lifx.set_color("all", "blue", brightness=0.5)
        lifx.breathe("all", "red")
    """
    
    BASE_URL = "https://api.lifx.com/v1"
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("LIFX_TOKEN")
        if not self.token:
            raise ValueError("LIFX_TOKEN environment variable not set")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        print(f"[*] LIFXService initialized")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make API request."""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.RequestException as e:
            print(f"[!] LIFX API error: {e}")
            return {"error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════════════════
    # QUERIES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def list_lights(self, selector: str = "all") -> list[LightState]:
        """Get all lights or filtered by selector."""
        data = self._request("GET", f"/lights/{quote(selector)}")
        if isinstance(data, list):
            return [
                LightState(
                    id=light.get("id", ""),
                    label=light.get("label", ""),
                    power=light.get("power", "off"),
                    color=light.get("color", {}),
                    brightness=light.get("brightness", 0),
                    connected=light.get("connected", False),
                    group=light.get("group", {}).get("name"),
                    location=light.get("location", {}).get("name")
                )
                for light in data
            ]
        return []
    
    def get_light_names(self) -> list[str]:
        """Get list of all light labels."""
        lights = self.list_lights()
        return [light.label for light in lights]
    
    def validate_color(self, color_string: str) -> dict:
        """Validate a color string and get HSBK values."""
        return self._request("GET", f"/color?string={color_string}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # POWER
    # ═══════════════════════════════════════════════════════════════════════════
    
    def set_power(self, selector: str = "all", power: Literal["on", "off"] = "on", duration: float = 1.0) -> dict:
        """Turn lights on or off."""
        return self._request("PUT", f"/lights/{quote(selector)}/state", json={
            "power": power,
            "duration": duration
        })
    
    def toggle(self, selector: str = "all", duration: float = 1.0) -> dict:
        """Toggle power state."""
        return self._request("POST", f"/lights/{selector}/toggle", json={
            "duration": duration
        })
    
    def turn_on(self, selector: str = "all", duration: float = 1.0) -> dict:
        """Turn lights on."""
        return self.set_power(selector, "on", duration)
    
    def turn_off(self, selector: str = "all", duration: float = 1.0) -> dict:
        """Turn lights off."""
        return self.set_power(selector, "off", duration)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # COLOR & BRIGHTNESS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def set_state(
        self,
        selector: str = "all",
        power: Optional[str] = None,
        color: Optional[str] = None,
        brightness: Optional[float] = None,
        duration: float = 1.0,
        infrared: Optional[float] = None
    ) -> dict:
        """
        Set light state.
        
        Args:
            selector: Light selector (all, label:Name, group:Name, id:xxx)
            power: "on" or "off"
            color: Color string (see LIFX color docs)
                   Examples: "red", "blue saturation:0.5", "kelvin:2700", "#FF5733"
            brightness: 0.0 to 1.0
            duration: Transition time in seconds
            infrared: 0.0 to 1.0 (for IR-capable lights)
        """
        payload = {"duration": duration}
        if power:
            payload["power"] = power
        if color:
            payload["color"] = color
        if brightness is not None:
            payload["brightness"] = max(0.0, min(1.0, brightness))
        if infrared is not None:
            payload["infrared"] = max(0.0, min(1.0, infrared))
        
        return self._request("PUT", f"/lights/{quote(selector)}/state", json=payload)
    
    def set_color(self, selector: str = "all", color: str = "white", brightness: Optional[float] = None, duration: float = 1.0) -> dict:
        """Set light color."""
        return self.set_state(selector, power="on", color=color, brightness=brightness, duration=duration)
    
    def set_brightness(self, selector: str = "all", brightness: float = 1.0, duration: float = 1.0) -> dict:
        """Set brightness level (0.0 to 1.0)."""
        return self.set_state(selector, brightness=brightness, duration=duration)
    
    def dim(self, selector: str = "all", percent: int = 50, duration: float = 1.0) -> dict:
        """Dim lights to percentage (0-100)."""
        return self.set_brightness(selector, brightness=percent / 100, duration=duration)
    
    def set_states(self, actions: list[dict], duration: float = 1.0) -> dict:
        """
        Set multiple device states in a single API call.
        
        Args:
            actions: List of device state dicts, each containing:
                - selector: LIFX selector (label:Name, id:xxx, etc.)
                - power: "on" or "off" (optional)
                - brightness: 0.0-1.0 (optional)
                - color: color string (optional)
                - kelvin: temperature 1500-9000 (optional, converted to color)
                - fx: effect name (optional, run separately)
            duration: Transition time
        
        Example:
            lifx.set_states([
                {"selector": "label:Eve", "brightness": 0.25, "kelvin": 2700},
                {"selector": "label:Adam", "brightness": 0.70, "kelvin": 7500},
                {"selector": "label:Eden", "brightness": 1.0, "color": "blue", "fx": "Color Cycle"}
            ])
        """
        # Build states array for LIFX API
        states = []
        fx_commands = []  # Effects need separate calls
        
        for action in actions:
            state = {
                "selector": action.get("selector", "all"),
                "duration": duration
            }
            
            if "power" in action:
                state["power"] = action["power"]
            
            if "brightness" in action:
                bri = action["brightness"]
                # Handle percent (0-100) vs decimal (0-1)
                state["brightness"] = bri / 100 if bri > 1 else bri
                # Auto turn on if setting brightness (unless explicit off)
                if "power" not in state:
                    state["power"] = "on"
            
            if "kelvin" in action:
                state["color"] = f"kelvin:{action['kelvin']}"
                # Auto turn on when setting temp
                if "power" not in state:
                    state["power"] = "on"
            
            if "color" in action and "kelvin" not in action:
                state["color"] = action["color"]
                # Auto turn on when setting color
                if "power" not in state:
                    state["power"] = "on"
            
            # Effects are handled separately after state is set
            if "fx" in action:
                fx_commands.append({
                    "selector": action.get("selector", "all"),
                    "fx": action["fx"]
                })
            
            states.append(state)
        
        # Send multi-state request
        result = self._request("PUT", "/lights/states", json={
            "states": states,
            "fast": False
        })
        
        # Run any effects
        for fx_cmd in fx_commands:
            self._run_fx(fx_cmd["selector"], fx_cmd["fx"])
        
        return result
    
    def _run_fx(self, selector: str, fx_name: str) -> dict:
        """Run a named effect on a device."""
        fx_lower = fx_name.lower().replace(" ", "_")
        
        fx_map = {
            "color_cycle": lambda: self.breathe(selector, "rainbow", period=5, cycles=100, persist=True),
            "breathe": lambda: self.breathe(selector, "purple", period=3, cycles=50),
            "pulse": lambda: self.pulse(selector, "white", period=1, cycles=10),
            "flame": lambda: self.flame(selector),
            "morph": lambda: self.morph(selector),
            "move": lambda: self.move(selector),
            "clouds": lambda: self.clouds(selector),
            "twinkle": lambda: self.breathe(selector, "white", period=0.5, cycles=100, persist=True),
            "flicker": lambda: self.breathe(selector, "orange", period=0.3, cycles=100, persist=True),
            "meteor": lambda: self.move(selector, direction="forward", period=0.5, cycles=20),
            "pastels": lambda: self.morph(selector, palette=["pink", "lavender", "mint", "peach"]),
            "random": lambda: self.morph(selector),
            "spooky": lambda: self.breathe(selector, "purple", period=4, cycles=50, persist=True),
            "strobe": lambda: self.pulse(selector, "white", period=0.1, cycles=50),
            "visualizer": lambda: self.morph(selector, period=1),
        }
        
        if fx_lower in fx_map:
            return fx_map[fx_lower]()
        else:
            print(f"[!] Unknown FX: {fx_name}")
            return {}
    
    
    # ═══════════════════════════════════════════════════════════════════════════
    # EFFECTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def breathe(self, selector: str = "all", color: str = "red", period: float = 2.0, cycles: float = 3, persist: bool = False) -> dict:
        """Pulsing breathe effect."""
        return self._request("POST", f"/lights/{selector}/effects/breathe", json={
            "color": color,
            "period": period,
            "cycles": cycles,
            "persist": persist,
            "power_on": True
        })
    
    def pulse(self, selector: str = "all", color: str = "white", period: float = 1.0, cycles: float = 3) -> dict:
        """Flash pulse effect."""
        return self._request("POST", f"/lights/{selector}/effects/pulse", json={
            "color": color,
            "period": period,
            "cycles": cycles,
            "power_on": True
        })
    
    def effects_off(self, selector: str = "all") -> dict:
        """Stop all effects."""
        return self._request("POST", f"/lights/{selector}/effects/off")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STATE DELTA (Relative Changes)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def state_delta(
        self,
        selector: str = "all",
        power: Optional[str] = None,
        brightness: Optional[float] = None,
        hue: Optional[float] = None,
        saturation: Optional[float] = None,
        kelvin: Optional[int] = None,
        duration: float = 1.0
    ) -> dict:
        """
        Change state by relative amounts.
        
        Args:
            brightness: Change by this amount (-1.0 to 1.0)
            hue: Rotate hue by degrees (-360 to 360)
            saturation: Change by this amount (-1.0 to 1.0)
            kelvin: Change by this amount (-6500 to 6500)
        """
        payload = {"duration": duration}
        if power:
            payload["power"] = power
        if brightness is not None:
            payload["brightness"] = brightness
        if hue is not None:
            payload["hue"] = hue
        if saturation is not None:
            payload["saturation"] = saturation
        if kelvin is not None:
            payload["kelvin"] = kelvin
        
        return self._request("POST", f"/lights/{selector}/state/delta", json=payload)
    
    def brighter(self, selector: str = "all", amount: float = 0.1, duration: float = 0.5) -> dict:
        """Make lights brighter by amount (0.0 to 1.0)."""
        return self.state_delta(selector, brightness=amount, duration=duration)
    
    def dimmer(self, selector: str = "all", amount: float = 0.1, duration: float = 0.5) -> dict:
        """Make lights dimmer by amount (0.0 to 1.0)."""
        return self.state_delta(selector, brightness=-amount, duration=duration)
    
    def warmer(self, selector: str = "all", amount: int = 500, duration: float = 0.5) -> dict:
        """Make lights warmer (lower kelvin)."""
        return self.state_delta(selector, kelvin=-amount, duration=duration)
    
    def cooler(self, selector: str = "all", amount: int = 500, duration: float = 0.5) -> dict:
        """Make lights cooler (higher kelvin)."""
        return self.state_delta(selector, kelvin=amount, duration=duration)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ADVANCED EFFECTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def move(self, selector: str = "all", direction: Literal["forward", "backward"] = "forward", period: float = 1.0, cycles: float = 5) -> dict:
        """Move effect for strips/multizone lights."""
        return self._request("POST", f"/lights/{selector}/effects/move", json={
            "direction": direction,
            "period": period,
            "cycles": cycles,
            "power_on": True
        })
    
    def morph(self, selector: str = "all", period: float = 5.0, palette: Optional[list[str]] = None) -> dict:
        """Morph effect for tiles - morphing colors."""
        payload = {"period": period, "power_on": True}
        if palette:
            payload["palette"] = palette
        return self._request("POST", f"/lights/{selector}/effects/morph", json=payload)
    
    def flame(self, selector: str = "all", period: float = 5.0) -> dict:
        """Flame effect for tiles."""
        return self._request("POST", f"/lights/{selector}/effects/flame", json={
            "period": period,
            "power_on": True
        })
    
    def clouds(self, selector: str = "all", duration: float = 0.0, palette: Optional[list[str]] = None) -> dict:
        """Clouds effect - soft color transitions."""
        payload = {"duration_seconds": duration, "power_on": True}
        if palette:
            payload["palette"] = palette
        return self._request("POST", f"/lights/{selector}/effects/clouds", json=payload)
    
    def sunrise(self, selector: str = "all", duration: float = 300.0) -> dict:
        """Sunrise effect - gradual warm wake-up over duration (default 5 min)."""
        return self._request("POST", f"/lights/{selector}/effects/sunrise", json={
            "duration": duration,
            "power_on": True
        })
    
    def sunset(self, selector: str = "all", duration: float = 300.0) -> dict:
        """Sunset effect - gradual dim to off over duration (default 5 min)."""
        return self._request("POST", f"/lights/{selector}/effects/sunset", json={
            "duration": duration,
            "power_on": True
        })
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SCENES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def list_scenes(self) -> list[dict]:
        """Get all saved scenes."""
        data = self._request("GET", "/scenes")
        if isinstance(data, list):
            return [{"uuid": s.get("uuid"), "name": s.get("name")} for s in data]
        return []
    
    def activate_scene(self, scene_uuid: str, duration: float = 1.0) -> dict:
        """Activate a saved scene by UUID."""
        return self._request("PUT", f"/scenes/scene_id:{scene_uuid}/activate", json={
            "duration": duration
        })
    
    def activate_scene_by_name(self, name: str, duration: float = 1.0) -> dict:
        """Activate a scene by name (case-insensitive)."""
        scenes = self.list_scenes()
        for scene in scenes:
            if scene["name"].lower() == name.lower():
                return self.activate_scene(scene["uuid"], duration)
        return {"error": f"Scene '{name}' not found"}
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CYCLE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def cycle(self, selector: str = "all", states: list[dict] = None, direction: str = "forward") -> dict:
        """
        Cycle through a list of states.
        
        Example states:
            [
                {"power": "on", "brightness": 1.0},
                {"power": "on", "brightness": 0.5},
                {"power": "on", "brightness": 0.25},
                {"power": "off"}
            ]
        """
        if not states:
            # Default: cycle through brightness levels
            states = [
                {"power": "on", "brightness": 1.0},
                {"power": "on", "brightness": 0.5},
                {"power": "on", "brightness": 0.25},
                {"power": "off"}
            ]
        return self._request("POST", f"/lights/{selector}/cycle", json={
            "states": states,
            "direction": direction
        })
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PRESETS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def movie_mode(self, selector: str = "all") -> dict:
        """Dim, warm lighting for movies."""
        return self.set_state(selector, power="on", color="kelvin:2200", brightness=0.15, duration=2)
    
    def focus_mode(self, selector: str = "all") -> dict:
        """Bright, cool lighting for focus/work."""
        return self.set_state(selector, power="on", color="kelvin:4000", brightness=0.8, duration=1)
    
    def relax_mode(self, selector: str = "all") -> dict:
        """Warm, medium lighting for relaxation."""
        return self.set_state(selector, power="on", color="kelvin:2700", brightness=0.5, duration=2)
    
    def party_mode(self, selector: str = "all") -> dict:
        """Colorful breathing effect."""
        self.set_state(selector, power="on", color="purple", brightness=1.0)
        return self.breathe(selector, color="blue", period=3, cycles=100, persist=True)
    
    def alert(self, selector: str = "all", color: str = "red") -> dict:
        """Quick attention-grabbing pulse."""
        return self.pulse(selector, color=color, period=0.5, cycles=5)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SNOWZONE ROOM SELECTORS
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Room selectors for Dave's Snowzone setup
    BEDROOM = "label:Eve"          # Eve - LIFX Mini C (white)
    LIVING_ROOM = "group:Living Room"  # Adam + Eden
    
    def bedroom(self, **kwargs) -> dict:
        """Control bedroom (Eve)."""
        return self.set_state(self.BEDROOM, **kwargs)
    
    def living_room(self, **kwargs) -> dict:
        """Control living room (Adam + Eden)."""
        return self.set_state(self.LIVING_ROOM, **kwargs)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # LIFE SETUP SCENES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def photo_mode(self, selector: str = "all") -> dict:
        """Photo/video lighting - bright, neutral, no color cast."""
        return self.set_state(selector, power="on", color="kelvin:5000", brightness=1.0, duration=1)
    
    def chill_mode(self, selector: str = "all") -> dict:
        """Chill vibes - warm amber, low brightness."""
        return self.set_state(selector, power="on", color="kelvin:2400", brightness=0.35, duration=2)
    
    def work_mode(self, selector: str = "all") -> dict:
        """Work/focus - bright daylight."""
        return self.set_state(selector, power="on", color="kelvin:4500", brightness=0.9, duration=1)
    
    def christmas_mode(self, selector: str = "all") -> dict:
        """Christmas vibes - red/green alternating breathe."""
        self.set_state(selector, power="on", color="red", brightness=0.8)
        return self.breathe(selector, color="green", period=4, cycles=50, persist=True)
    
    def warm_ember(self, selector: str = "all") -> dict:
        """Warm ember glow."""
        return self.set_state(selector, power="on", color="kelvin:2200", brightness=0.4, duration=2)


# ═══════════════════════════════════════════════════════════════════════════════
# QUICK TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    lifx = LIFXService()
    
    # List all lights
    lights = lifx.list_lights()
    print(f"\nFound {len(lights)} lights:")
    for light in lights:
        print(f"  - {light.label} ({light.power}, {light.brightness*100:.0f}%)")
    
    # # Test commands
    # lifx.turn_on()
    # lifx.set_color("all", "blue", brightness=0.5)
    # lifx.breathe("all", "purple")
