import csv
import sys
import xml.etree.ElementTree as ET
from math import sqrt

# Add these constants at the top of your script
TRAM_STOPS = {
    "Hotel Golf": [50.068031,14.346667],
    "Poštovka": [50.06855,14.3543],
    "Kotlářka": [50.069565,14.362923],
    "Kavalírka": [50.070042,14.37063],
    "Klamovka": [50.070702,14.380618]
}

# Define a buffer constant
BUFFER = 50

def get_closest_svg_coordinate(normalized_x, normalized_y, svg_file_path):
    """
    Get the closest SVG path coordinate to the given normalized coordinates.
    
    Args:
    - normalized_x (float): The x-coordinate to compare against.
    - normalized_y (float): The y-coordinate to compare against.
    - svg_file_path (str): The path to the SVG file.

    Returns:
    - tuple (float, float): The closest x and y coordinates from the SVG path.
    """
    
    # Load and parse the SVG file
    tree = ET.parse(svg_file_path)
    root = tree.getroot()

    # Define a function to calculate the Euclidean distance
    def distance(x1, y1, x2, y2):
        return sqrt((x1 - x2)**2 + (y1 - y2)**2)

    closest_x = None
    closest_y = None
    min_distance = float('inf')
    
    # Iterate over all paths in the SVG
    for path in root.findall('.//{http://www.w3.org/2000/svg}path'):
        # Get path data
        d = path.get('d', '')
        
        # Split path data into commands and coordinates, then filter out commands
        coords = [pair for i, pair in enumerate(d.split()) if i % 3 >= 1]
        
        for i in range(0, len(coords), 2):
            x, y = float(coords[i]), float(coords[i + 1])
            
            # Calculate the distance between current SVG point and the given coordinates
            dist = distance(normalized_x, normalized_y, x, y)
            
            if dist < min_distance:
                min_distance = dist
                closest_x, closest_y = x, y

    return closest_x, closest_y

def read_csv_file(filename):
    """Reads CSV data and returns a list of coordinates ordered by shape_pt_sequence."""
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        # Sort coordinates by shape_pt_sequence before converting
        sorted_coords = sorted(reader, key=lambda row: int(row['shape_pt_sequence']))
        coordinates = [(float(row['lat']), float(row['lon'])) for row in sorted_coords]
    return coordinates

def normalize_stop(stop_coord, width, height, min_lat, max_lat, min_lon, max_lon):
    """Normalize the coordinates of a single tram stop."""
    lat, lon = stop_coord
    norm_x = BUFFER + (lon - min_lon) / (max_lon - min_lon) * (width - 2 * BUFFER)
    norm_y = BUFFER + (1 - (lat - min_lat) / (max_lat - min_lat)) * (height - 2 * BUFFER)
    return norm_x, norm_y

def normalize_coordinates(coords, width, height):
    """Normalize a list of (latitude, longitude) to fit within a bounding box."""
    min_lat = min([c[0] for c in coords])
    max_lat = max([c[0] for c in coords])
    min_lon = min([c[1] for c in coords])
    max_lon = max([c[1] for c in coords])

    normalized = []
    for (lat, lon) in coords:
        norm_x = BUFFER + (lon - min_lon) / (max_lon - min_lon) * (width - 2 * BUFFER)
        norm_y = BUFFER + (1 - (lat - min_lat) / (max_lat - min_lat)) * (height - 2 * BUFFER)
        normalized.append((norm_x, norm_y))
    
    return normalized

def get_svg_dimensions(coords, desired_width):
    """Calculate SVG dimensions based on the desired width while maintaining the correct aspect ratio."""
    min_lat = min([c[0] for c in coords])
    max_lat = max([c[0] for c in coords])
    min_lon = min([c[1] for c in coords])
    max_lon = max([c[1] for c in coords])

    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon

    aspect_ratio = lat_range / lon_range

    width = desired_width + 2 * BUFFER
    height = int(desired_width * aspect_ratio) + 2 * BUFFER

    return width, height

def to_svg_path(coords):
    """Converts normalized coordinates into SVG path data."""
    path_data = f"M {coords[0][0]} {coords[0][1]} "  # M starts the path
    for (x, y) in coords[1:]:
        path_data += f"L {x} {y} "  # L creates a line to the coordinate
    return path_data

def normalize_to_svg(lat, lon, desired_width, coords, min_lat, max_lat, min_lon, max_lon):
    SVG_WIDTH, SVG_HEIGHT = get_svg_dimensions(coords, desired_width)

    # normalize latitude (note: SVG's y-coordinate increases from top to bottom)
    svg_y = (1 - (lat - min_lat) / (max_lat - min_lat)) * SVG_HEIGHT
    
    # normalize longitude
    svg_x = ((lon - min_lon) / (max_lon - min_lon)) * SVG_WIDTH
    
    return svg_x, svg_y

def generate_svg(path_data, stops, width, height):
    """Generates an SVG string with given path data and tram stops."""
    svg_template = f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <path d="{path_data}" fill="none" stroke="black" />
    """

    for stop_name, coord in stops.items():
        # Define positions for circle and label
        circle_x = coord[0]
        circle_y = coord[1]
        text_x = circle_x + 11  # Adjust this value to control label distance
        text_y = circle_y + 1   # Adjust this value to control vertical position of label
        rotation_angle = -55  # Angle slightly more vertical than 45 degrees
        
        svg_template += f"""
        <circle cx="{circle_x}" cy="{circle_y}" r="5" fill="black" />
        <text x="{text_x}" y="{text_y}" font-size="12" transform="rotate({rotation_angle}, {circle_x}, {circle_y})">{stop_name}</text>
        """
    
    svg_template += "</svg>"
    return svg_template

def main(input_file, output_file):
    # 1. Read the CSV data
    coords = read_csv_file(input_file)

    # Dynamically determine SVG dimensions
    width, height = get_svg_dimensions(coords, 800)  # 800 is the desired width
    
    # 2. Normalize the coordinates
    normalized_coords = normalize_coordinates(coords, width, height)

    # 2.1 Normalize tram stop coordinates
    min_lat = min([c[0] for c in coords])
    max_lat = max([c[0] for c in coords])
    min_lon = min([c[1] for c in coords])
    max_lon = max([c[1] for c in coords])
    normalized_stops = {name: normalize_stop(coord, width, height, min_lat, max_lat, min_lon, max_lon) for name, coord in TRAM_STOPS.items()}

    # 3. Convert to SVG path
    path_data = to_svg_path(normalized_coords)

    # 4. Generate the SVG and save to file
    svg = generate_svg(path_data, normalized_stops, width, height)
    with open(output_file, 'w') as file:
        file.write(svg)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python script_name.py input.txt output.svg')
    else:
        main(sys.argv[1], sys.argv[2])