import os
import json
from getpass import getpass

import requests

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
    return headers


def get_symp_meraki_customers(headers):
    """Accepts token and headers variables.
    Returns a list of dicts of customer organizations"""
    print("Retrieving customer list.")
    customer_url = Api_url + "organizations/"
    response = requests.get(url=customer_url, headers=headers)
    customers_json = response.json()  # List of dicts
    return customers_json


def get_networks(customers):
    """Accepts a json list of customers.
    Returns a list of network information associated with each customer"""
    print("Retrieving customer networks.")
    networks_list = []
    for customer in customers:
        net_url = Api_url + 'organizations/' + customer['id'] + '/networks'
        try:
            response = requests.get(url=net_url, headers=headers)
            networks_json = response.json()
            network_ids = []  # list of dicts
            for network in networks_json:
                network_ids.append({'networkId': network['id'],
                                    'networkName': network['name']})
            networks_list.append({
                'organizationId': customer['id'],
                'organizationName': customer['name'],
                'networks': network_ids
            })
        except TypeError:
            error = 'To make requests you must first enable API access'
            if networks_json['errors'][0][0:49] == error:
                networks_list.append({
                    'organizationId': customer['id'],
                    'organizationName': customer['name'],
                    'error': error
                })
    return networks_list


def get_syslog_servers(networks_list):
    """Accepts a json list of customer networks.
    Returns a list of customer networks with the syslog server configuration
    appended to the network information"""
    print("Retrieving syslog configuration for each network.")
    for customer in networks_list:
        if 'networks' in customer:
            for network in customer['networks']:
                syslog_url = Api_url + 'networks/' + network['networkId'] + '/syslogServers'
                response = requests.get(url=syslog_url, headers=headers)
                syslog_json = response.json()
                # Adds syslog config info to the networkId dict
                network['syslogServer'] = syslog_json
    return networks_list


def write_json_to_file (json_output):
    with open((File_output_dir + '\\json_output.json'), 'w') as json_file:
        json.dump(json_output, json_file, indent=4)


headers = auth_meraki_api()
customers = get_symp_meraki_customers(headers)
networks = get_networks(customers)
syslogServers = get_syslog_servers(networks)
write_json_to_file(syslogServers)
