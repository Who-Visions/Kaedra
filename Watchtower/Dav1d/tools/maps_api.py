#!/usr/bin/env python3
"""
Google Maps Platform Integration for DAV1D
Provides geocoding, places search, and location awareness
"""

import os
from typing import Optional, List, Dict, Any
import googlemaps
from datetime import datetime

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0285887798")


def geocode_address(address: str) -> Dict[str, Any]:
    """
    Convert an address to geographic coordinates (latitude, longitude).
    
    Args:
        address: Address to geocode (e.g., "1600 Amphitheatre Parkway, Mountain View, CA")
        
    Returns:
        dict with coordinates, formatted address, and location details
        
    Example:
        geocode_address("Times Square, New York")
    """
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "GOOGLE_MAPS_API_KEY not set in environment"
            }
        
        gmaps = googlemaps.Client(key=api_key)
        result = gmaps.geocode(address)
        
        if not result:
            return {
                'success': False,
                'error': f'Address not found: {address}'
            }
        
        location = result[0]
        geometry = location['geometry']['location']
        
        return {
            'success': True,
            'address': address,
            'formatted_address': location['formatted_address'],
            'latitude': geometry['lat'],
            'longitude': geometry['lng'],
            'place_id': location['place_id'],
            'location_type': location['geometry']['location_type'],
            'coordinates': f"{geometry['lat']}, {geometry['lng']}"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def reverse_geocode(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Convert coordinates to an address.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        
    Returns:
        dict with formatted address and location details
        
    Example:
        reverse_geocode(40.7580, -73.9855)
    """
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "GOOGLE_MAPS_API_KEY not set"
            }
        
        gmaps = googlemaps.Client(key=api_key)
        result = gmaps.reverse_geocode((latitude, longitude))
        
        if not result:
            return {
                'success': False,
                'error': f'No address found for coordinates: {latitude}, {longitude}'
            }
        
        location = result[0]
        
        return {
            'success': True,
            'coordinates': f"{latitude}, {longitude}",
            'formatted_address': location['formatted_address'],
            'place_id': location['place_id'],
            'types': location['types']
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def search_nearby_places(
    location: str,
    place_type: str = "restaurant",
    radius: int = 5000,
    keyword: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for nearby places around a location.
    
    Args:
        location: Address or place name (will be geocoded)
        place_type: Type of place - "restaurant", "cafe", "gas_station", "atm", etc.
        radius: Search radius in meters (default: 5000m = ~3 miles)
        keyword: Optional keyword to filter results
        
    Returns:
        dict with nearby places including names, addresses, ratings, and distances
        
    Example:
        search_nearby_places("Times Square, NYC", "coffee_shop", radius=1000)
    """
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "GOOGLE_MAPS_API_KEY not set"
            }
        
        gmaps = googlemaps.Client(key=api_key)
        
        # First geocode the location
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            return {
                'success': False,
                'error': f'Location not found: {location}'
            }
        
        coords = geocode_result[0]['geometry']['location']
        
        # Search for nearby places
        places_result = gmaps.places_nearby(
            location=(coords['lat'], coords['lng']),
            radius=radius,
            type=place_type,
            keyword=keyword
        )
        
        places = []
        for place in places_result.get('results', [])[:10]:  # Limit to top 10
            places.append({
                'name': place['name'],
                'address': place.get('vicinity', 'N/A'),
                'rating': place.get('rating', 'N/A'),
                'user_ratings': place.get('user_ratings_total', 0),
                'place_id': place['place_id'],
                'types': place.get('types', []),
                'location': {
                    'lat': place['geometry']['location']['lat'],
                    'lng': place['geometry']['location']['lng']
                },
                'open_now': place.get('opening_hours', {}).get('open_now', None)
            })
        
        return {
            'success': True,
            'search_location': location,
            'coordinates': f"{coords['lat']}, {coords['lng']}",
            'place_type': place_type,
            'radius_meters': radius,
            'places': places,
            'count': len(places)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_directions(origin: str, destination: str, mode: str = "driving") -> Dict[str, Any]:
    """
    Get directions between two locations.
    
    Args:
        origin: Starting location (address or place name)
        destination: Ending location (address or place name)
        mode: Travel mode - "driving", "walking", "bicycling", "transit"
        
    Returns:
        dict with route information including distance, duration, and step-by-step directions
        
    Example:
        get_directions("Grand Central Terminal, NYC", "Times Square, NYC", mode="walking")
    """
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "GOOGLE_MAPS_API_KEY not set"
            }
        
        gmaps = googlemaps.Client(key=api_key)
        
        directions_result = gmaps.directions(
            origin,
            destination,
            mode=mode,
            departure_time=datetime.now()
        )
        
        if not directions_result:
            return {
                'success': False,
                'error': f'No route found from {origin} to {destination}'
            }
        
        route = directions_result[0]
        leg = route['legs'][0]
        
        steps = []
        for step in leg['steps']:
            steps.append({
                'instruction': step['html_instructions'].replace('<b>', '').replace('</b>', ''),
                'distance': step['distance']['text'],
                'duration': step['duration']['text']
            })
        
        return {
            'success': True,
            'origin': leg['start_address'],
            'destination': leg['end_address'],
            'mode': mode,
            'total_distance': leg['distance']['text'],
            'total_duration': leg['duration']['text'],
            'steps': steps,
            'summary': route['summary']
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_distance_matrix(origins: List[str], destinations: List[str], mode: str = "driving") -> Dict[str, Any]:
    """
    Calculate travel distance and time for multiple origin-destination pairs.
    
    Args:
        origins: List of origin addresses
        destinations: List of destination addresses
        mode: Travel mode - "driving", "walking", "bicycling", "transit"
        
    Returns:
        dict with distance and duration matrix
        
    Example:
        get_distance_matrix(
            ["Times Square, NYC", "Central Park, NYC"],
            ["Brooklyn Bridge, NYC", "Statue of Liberty, NYC"]
        )
    """
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "GOOGLE_MAPS_API_KEY not set"
            }
        
        gmaps = googlemaps.Client(key=api_key)
        
        matrix = gmaps.distance_matrix(
            origins,
            destinations,
            mode=mode
        )
        
        results = []
        for i, origin_addr in enumerate(matrix['origin_addresses']):
            for j, dest_addr in enumerate(matrix['destination_addresses']):
                element = matrix['rows'][i]['elements'][j]
                
                if element['status'] == 'OK':
                    results.append({
                        'origin': origin_addr,
                        'destination': dest_addr,
                        'distance': element['distance']['text'],
                        'duration': element['duration']['text'],
                        'distance_meters': element['distance']['value'],
                        'duration_seconds': element['duration']['value']
                    })
        
        return {
            'success': True,
            'mode': mode,
            'pairs': results,
            'count': len(results)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
