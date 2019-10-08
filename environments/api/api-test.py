"""
Script to call the Meraki API and return a list of customer customer sites with 2fa disabled on @symplexity.com users.
The script prompts for a location to save the list and prompts for the Symplexity API key

"""

import json, os
import requests
from getpass import getpass

orgs_url = 'https://api.meraki.com/api/v0/organizations/'
file_output_dir = input("Where would you like to save the output? ")

if not os.path.isdir(file_output_dir):
    os.makedirs(file_output_dir)


def auth_meraki_api():
    """Asks for api key and returns the token and headers for a request."""
    token = getpass("API Key: ")
    headers = {
        'Accept': '*/*',
        'X-Cisco-Meraki-API-Key': token
    }
    return (token, headers)

token, headers = auth_meraki_api()


def get_symp_meraki_customers(token, headers):
    """Accepts token and headers variables. Returns a list of dicts of customer organizations"""
    print("Retrieving customer list.")
    response = requests.get(url=orgs_url, headers=headers)
    customers_json = response.json()  # List of dicts
    return customers_json

customers = get_symp_meraki_customers(token, headers)


def get_customers_admins(customers):
    """Takes customers list and retrieves a dict of admins for each customer"""
    print("Retrieving admin lists.")
    customer_admins = []
    for customer in customers:
        admin_url = orgs_url + customer['id'] + '/admins'
        response_admins = requests.get(url=admin_url, headers=headers)
        admins_json = response_admins.json()
        customer_admins.append({'name': customer['name'], 'id': customer['id'], 'admins': admins_json})
    return customer_admins

customer_admins = get_customers_admins(customers)


def parse_admins(customer_list):
    """Takes a list of customer admins and writes a file of symplexity logins where 2fa is not enabled"""
    print("Checking for MFA and API access")
    symp_2fa_disabled = []
    for customer in customer_list:
        for admin in customer['admins']:
            try:
                if len(admin['email']) > 15:
                    email = admin['email'][admin['email'].find('@'):]
                    if email == '@symplexity.com' and admin['twoFactorAuthEnabled'] is False:
                        symp_2fa_disabled.append({'name': customer['name'],
                                                  'user': admin['name'],
                                                  'twoFactorAuthEnabled': admin['twoFactorAuthEnabled']})
            except TypeError:
                error = 'To make requests you must first enable API access'
                if customer['admins']['errors'][0][0:49] == error:
                    symp_2fa_disabled.append({'name': customer['name'],
                                              'error': error})
    with open((file_output_dir + '\\meraki_2fa_disabled.json'), 'w') as mfa_file:
        json.dump(symp_2fa_disabled, mfa_file, indent=4)
    return symp_2fa_disabled

parse_admins(customer_admins)
