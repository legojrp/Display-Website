from FlightRadar24 import FlightRadar24API

# Initialize the API
fr_api = FlightRadar24API("legojrp@gmail.com", "Flypigsfly1")

# Define Indiana's approximate bounding coordinates (latitude and longitude)
indiana_bounds = "37.7719,-88.0979,41.7614,-84.7846"

# Fetch flights within Indiana's bounds
flights_in_indiana = fr_api.get_flights(bounds=indiana_bounds)

# Display flight information
for flight in flights_in_indiana:
    print(f"Flight Call Sign: {flight.callsign}, Airline: {flight.airline_icao}, Aircraft: {flight.aircraft_code}, Altitude: {flight.get_altitude()}, Speed: {flight.get_ground_speed()}")
