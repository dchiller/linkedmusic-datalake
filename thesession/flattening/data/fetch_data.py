import requests
import os
import time
# List of GitHub raw links
github_raw_links = [
    "https://raw.githubusercontent.com/adactio/TheSession-data/main/csv/aliases.csv",
    "https://raw.githubusercontent.com/adactio/TheSession-data/main/csv/recordings.csv",
    "https://raw.githubusercontent.com/adactio/TheSession-data/main/csv/tune_popularity.csv",
    "https://raw.githubusercontent.com/adactio/TheSession-data/main/csv/tunes.csv"
    # Add more links as needed
]


# Loop through the GitHub raw links and download the files
for link in github_raw_links:
    # Extract the filename from the URL
    filename = link.split("/")[-1]
    
    # Construct the complete path to save the file
    save_path = os.path.join('.', filename)
    
    # Send an HTTP GET request to the URL
    response = requests.get(link)
    
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Save the content of the response to a file
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download {filename}. Status code: {response.status_code}")
    time.sleep(2)
print("Download complete.")
