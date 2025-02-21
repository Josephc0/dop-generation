import requests

# Define the URL for the current SEM Almanac (.txt format)

#here you can manually input the yr / archive file number (ranging from 001-999) to select whichever sem you want
#url = "https://www.navcen.uscg.gov/sites/default/files/gps/almanac/2024/Sem/001.al3"

#automatically updates to the current sem_almanac file
url = "https://www.navcen.uscg.gov/sites/default/files/gps/almanac/current_sem.al3"

# Send an HTTP GET request
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Save the content to a local file
    with open("current_sem.txt", "w") as file:
        file.write(response.text)
    print("File downloaded and saved as 'current_sem.txt'")
else:
    print(f"Failed to retrieve the file. Status code: {response.status_code}")
