import os
import json
import requests
from getpass import getpass

Api_url = 'https://api.meraki.com/api/v0/'
File_output_dir = input("Where would you like to save the output? ")

if not os.path.isdir(File_output_dir):
    os.makedirs(File_output_dir)


def auth_meraki_api():
    """Asks for api key and returns the token and headers for a request."""
    token = getpass("Symplexity API Key: ")
    headers = {
        'Accept': '*/*',
        'X-Cisco-Meraki-API-Key': token
    }
    return token, headers


def get_symp_meraki_customers(token, headers):
    """Accepts token and headers variables.
    Returns a list of dicts of customer organizations"""
    print("Retrieving customer list.")
    cust_url = Api_url + "organizations/"
    response = requests.get(url=cust_url, headers=headers)
    customers_json = response.json()  # List of dicts
    return customers_json

def get_networks(customers):
    networks_list = []
    for customer in customers:
        net_url = Api_url + 'organizations/' + customer['id'] + '/networks'
        response = requests.get(url=net_url, headers=headers)
        networks_json = response.json()
        network_ids = []
        for net in networks_json:
            network_ids.append({
                'networkId': net['id'],
                'networkName': net['name']
            })
        networks_list.append({
            'organizationId': customer['id'],
            'organizationName': customer['name'],
            'networks': network_ids
        })
    return networks_list


