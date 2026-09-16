"""
KAEDRA v0.0.6 - Sun Times Service
Sunrise, sunset, golden hour and civil twilight for shoot planning.

Pure NOAA solar-position arithmetic: no API, no key, no network, no third-party
dependency. This gets asked on a beach with one bar of signal, so it has to
answer from the process itself.

The service reports a WINDOW rather than a moment, because that is the mistake
it exists to prevent: golden hour is golden_evening_start -> sunset, roughly 30
minutes in south Florida, not an hour.
"""

import datetime as dt
import logging
from dataclasses import dataclass, asdict
from math import sin, cos, tan, asin, acos, radians, degrees
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("kaedra.services.suntimes")

# key: (label, latitude, longitude EAST-POSITIVE, utc offset hours)
SITES: Dict[str, Tuple[str, float, float, float]] = {
    "palmbeach": ("Palm Beach Island (Worth Ave)", 26.7056, -80.0364, -4.0),
    "lakeworth": ("Lake Worth Pier", 26.6156, -80.0339, -4.0),
    "lantana": ("Lantana Beach", 26.5875, -80.0364, -4.0),
}

ZENITH_CIVIL = 96.0      # sun 6 deg below horizon
ZENITH_HORIZON = 90.833  # includes refraction + solar radius
ZENITH_GOLDEN = 84.0     # sun 6 deg above horizon


@dataclass
class SunDay:
    """The six solar moments of one day at one place, local clock time."""
    site: str
    date: str
    lat: float
    lon: float
    utc_offset: float
    civil_dawn: Optional[str]
    sunrise: Optional[str]
    golden_morning_end: Optional[str]
    golden_evening_start: Optional[str]
    sunset: Optional[str]
    civil_dusk: Optional[str]

    @property
    def golden_evening(self) -> Optional[str]:
        """The evening golden window as a readable range."""
        if self.golden_evening_start and self.sunset:
            return "%s-%s" % (self.golden_evening_start, self.sunset)
        return None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["golden_evening"] = self.golden_evening
        return d


def _julian_day(y: int, m: int, d: int) -> float:
    if m <= 2:
        y, m = y - 1, m + 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5


def _solar(jd: float) -> Tuple[float, float]:
    """(declination deg, equation of time minutes) for a julian day."""
    t = (jd - 2451545.0) / 36525.0
    l0 = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360
    m = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
    mr = radians(m)
    c = (sin(mr) * (1.914602 - t * (0.004817 + 0.000014 * t))
         + sin(2 * mr) * (0.019993 - 0.000101 * t)
         + sin(3 * mr) * 0.000289)
    omega = 125.04 - 1934.136 * t
    lam = l0 + c - 0.00569 - 0.00478 * sin(radians(omega))
    secs = 21.448 - t * (46.8150 + t * (0.00059 - t * 0.001813))
    eps = 23 + (26 + secs / 60) / 60 + 0.00256 * cos(radians(omega))
    decl = degrees(asin(sin(radians(eps)) * sin(radians(lam))))
    y = tan(radians(eps / 2)) ** 2
    l0r = radians(l0)
    eqt = 4 * degrees(y * sin(2 * l0r) - 2 * e * sin(mr)
                      + 4 * e * y * sin(mr) * cos(2 * l0r)
                      - 0.5 * y * y * sin(4 * l0r)
                      - 1.25 * e * e * sin(2 * mr))
    return decl, eqt


class SunTimesService:
    """
    Sunrise / sunset / golden hour service.

    Features:
    - Saved shoot locations, or any lat/lon
    - Six solar moments per day, local clock time
    - Golden windows rather than bare sunset times
    - Offline and dependency-free
    """

    def __init__(self, default_tz: float = -4.0):
        self.default_tz = default_tz

    # -- core ------------------------------------------------------------
    def _event(self, date: dt.date, lat: float, lon: float,
               zenith: float, rising: bool, tz: float) -> Optional[str]:
        """Local clock time of a solar event, or None if it never occurs."""
        jd = _julian_day(date.year, date.month, date.day)
        minutes = None
        for _ in range(3):  # refine decl/eqt at the event time itself
            j = jd if minutes is None else jd + minutes / 1440.0
            decl, eqt = _solar(j)
            cos_h = (cos(radians(zenith)) / (cos(radians(lat)) * cos(radians(decl)))
                     - tan(radians(lat)) * tan(radians(decl)))
            if cos_h > 1 or cos_h < -1:
                return None  # polar day / polar night
            ha = degrees(acos(cos_h))
            minutes = 720 - 4 * (lon + (ha if rising else -ha)) - eqt
        local = minutes + tz * 60
        return "%02d:%02d" % (int(local // 60) % 24, int(round(local % 60)) % 60)

    def day(self, date: dt.date, lat: float, lon: float,
            tz: Optional[float] = None, label: str = "ad-hoc") -> SunDay:
        """All six moments for one place on one date."""
        tz = self.default_tz if tz is None else tz
        ev = lambda z, r: self._event(date, lat, lon, z, r, tz)
        return SunDay(
            site=label, date=date.isoformat(), lat=lat, lon=lon, utc_offset=tz,
            civil_dawn=ev(ZENITH_CIVIL, True),
            sunrise=ev(ZENITH_HORIZON, True),
            golden_morning_end=ev(ZENITH_GOLDEN, True),
            golden_evening_start=ev(ZENITH_GOLDEN, False),
            sunset=ev(ZENITH_HORIZON, False),
            civil_dusk=ev(ZENITH_CIVIL, False),
        )

    # -- public API ------------------------------------------------------
    def site(self, key: str, date: Optional[dt.date] = None) -> SunDay:
        """Times for a saved location. Raises KeyError on an unknown key."""
        hit = SITES.get(str(key).lower())
        if not hit:
            raise KeyError("Unknown site %r. Known: %s" % (key, ", ".join(SITES)))
        label, lat, lon, tz = hit
        return self.day(date or dt.date.today(), lat, lon, tz, label)

    def all_sites(self, date: Optional[dt.date] = None) -> List[SunDay]:
        """Times for every saved location."""
        date = date or dt.date.today()
        return [self.day(date, la, lo, tz, lbl) for lbl, la, lo, tz in SITES.values()]

    def golden(self, key: str, date: Optional[dt.date] = None) -> Dict[str, Any]:
        """
        The golden windows, which is what a shoot is actually planned around.

        Returns the evening window as from/to. In south Florida that span is
        about 30 minutes, so a call time set against sunset arrives as the
        light ends.
        """
        d = self.site(key, date)
        return {
            "site": d.site,
            "date": d.date,
            "morning": {"from": d.sunrise, "to": d.golden_morning_end},
            "evening": {"from": d.golden_evening_start, "to": d.sunset},
            "warning": ("Golden hour is a WINDOW, not a moment. Plan the call time "
                        "against the evening 'from', not against sunset."),
        }

    def known_sites(self) -> List[Dict[str, Any]]:
        """The saved locations, with the caveat that matters when choosing."""
        return [
            {"key": k, "label": v[0], "lat": v[1], "lon": v[2], "utc_offset": v[3]}
            for k, v in SITES.items()
        ]

    CAVEATS = (
        "Golden hour is golden_evening_start -> sunset; plan against the start.",
        "The saved Florida sites are ~13km apart and identical to the minute - "
        "choosing between them is a background decision, never a lighting one.",
        "They are Atlantic EAST-facing: sunrise is over open ocean, but the sun "
        "SETS INLAND over the Intracoastal.",
        "Astronomical times on a flat horizon - no weather, no terrain. Cloud, "
        "haze, dunes and buildings all shorten the usable window.",
    )
