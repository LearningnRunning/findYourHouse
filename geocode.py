import pandas as pd
from geopy.geocoders import Nominatim

# Load your DataFrame
df = pd.read_csv("./DB_raw.csv")

# Initialize the geocoder
geolocator = Nominatim(user_agent="my-application")

# Iterate through the rows of the DataFrame
for index, row in df.iterrows():
    # Get the address from the 'address' column
    address = row["address"]

    # Use the geocoder to get the latitude and longitude of the address
    location = geolocator.geocode(address)
    if location:
        # If the geocoder returns a result, add the latitude and longitude to the DataFrame
        df.loc[index, "latitude"] = location.latitude
        df.loc[index, "longitude"] = location.longitude
    else:
        # If the geocoder doesn't return a result, set the latitude and longitude to NaN
        df.loc[index, "latitude"] = float("nan")
        df.loc[index, "longitude"] = float("nan")

# Save the updated DataFrame to a new CSV file
df.to_csv("./DB.csv", index=False)
