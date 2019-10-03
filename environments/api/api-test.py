import json
import requests
from getpass import getpass

token = getpass("API Key: ")
url = 'https://api.meraki.com/api/v0/organizations/'
headers = {
    'Accept': '*/*',
    'X-Cisco-Meraki-API-Key': token
}

response = requests.get(url, headers = headers)

json_orgs = json.dumps(response.json(), sort_keys=True, indent=4)

print(json_orgs)
