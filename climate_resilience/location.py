import reverse_geocoder as rg
import folium
import math

def coordinate_check(latitude, longitude):
    """
    Validates that the provided coordinates fall within the European domain,
    then performs a reverse‑geocoding lookup to retrieve the corresponding city and country.
    """
    if latitude >= 34.80 and latitude <= 81.8067 and longitude >= -28.8333 and longitude <= 69.0334:
        coordinates = (latitude, longitude)
        location = rg.search(coordinates)
        country = location[0]['cc']
        city = location[0]['name']
        return city, country
    else:
        raise ValueError("Climate resilience analysis is not supported in the selected region. Please select European coordinates.")

def format_coordinates(coordinate, type="latitude"):
    """
    Converts a decimal coordinate into degrees, minutes, and seconds (DMS) format,
    automatically assigning the correct directional suffix (N/S/E/W) based on value and type.
    """
    abs_degrees = abs(coordinate)
    degrees = math.floor(abs_degrees)
    minutes = math.floor(60*(abs_degrees-degrees))
    seconds = round(3600 * (abs_degrees-degrees) - 60*minutes)
    if type == "latitude":
        if coordinate < 0:
            return """{}° {}' {}" S""".format(degrees, minutes, seconds)
        else:
            return """{}° {}' {}" N""".format(degrees, minutes, seconds)
    else:
        if coordinate < 0:
            return """{}° {}' {}" W""".format(degrees, minutes, seconds)
        else:
            return """{}° {}' {}" E""".format(degrees, minutes, seconds)

def get_map(latitude, longitude, city, country):
    """
    Creates an interactive Folium map centered on the given coordinates, 
    adding a marker with a popup displaying the city, country, and formatted coordinates.
    """
    f = folium.Figure(width=500, height=500)
    m = folium.Map(location=[latitude, longitude], zoom_start=10).add_to(f)
    folium.Marker(
        location=[latitude, longitude],
        popup=folium.Popup('<b>{}, {}</b><br>({} {})'.format(city, country, format_coordinates(latitude, "latitude"), format_coordinates(longitude, "longitude")), max_width=400, min_width=80), # pop-up label for the marker
        icon=folium.Icon()
    ).add_to(m)
    return f
