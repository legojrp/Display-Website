from FlightRadar24 import FlightRadar24API

# Initialize the API
fr_api = FlightRadar24API()

# Define the geographic bounds for a small area in the U.S. (example: a part of California)
min_lat = 34.0  # Southern boundary
max_lat = 37.0  # Northern boundary
min_lon = -120.0  # Western boundary
max_lon = -117.0  # Eastern boundary

# Fetch flights in the specified bounds
flights = fr_api.get_flights(bounds=f"{max_lat},{min_lon},{min_lat},{max_lon}")

# Check for flights outside the defined bounds
outside_flights = []

for flight in flights:
    lat, lon = flight.latitude, flight.longitude
    callsign = flight.callsign  # Get the flight's callsign
    
    # Check if the flight is outside the defined bounds
    if lat < min_lat or lat > max_lat or lon < min_lon or lon > max_lon:
        outside_flights.append(callsign)

# Print the callsigns of flights found outside the bounds
if outside_flights:
    print("Flights found outside the defined bounds:")
    for callsign in outside_flights:
        print(callsign)
else:
    print("No flights found outside the defined bounds.")
