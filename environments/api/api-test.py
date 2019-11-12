"""
Use the Meraki API and return a list of customer customer sites.
Checks for 2fa disabled on @symplexity.com users.
Checks for dashboard API access not enabled.
The script prompts for a location to save the list and
prompts for the Symplexity API key

Requires requests library

"""

import os
import json
import requests
from getpass import getpass

Orgs_url = 'https://api.meraki.com/api/v0/organizations/'
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
    response = requests.get(url=Orgs_url, headers=Headers)
    customers_json = response.json()  # List of dicts
    return customers_json


def get_customers_admins(customers):
    """Takes customers list and retrieves a dict of admins for each customer"""
    print("Retrieving admin lists.")
    customer_admins = []
    for customer in customers:
        admin_url = Orgs_url + customer['id'] + '/admins'
        response_admins = requests.get(url=admin_url, headers=Headers)
        admins_json = response_admins.json()
        customer_admins.append({'name': customer['name'],
                                'id': customer['id'],
                                'admins': admins_json})
    return customer_admins


def parse_admins(customer_list):
    """Takes a list of customer admins and writes a file of symplexity
    logins where 2fa is not enabled"""
    print("Checking for MFA and API access")
    symp_2fa_disabled = []
    for customer in customer_list:
        for admin in customer['admins']:
            try:
                if len(admin['email']) > 15:
                    email = admin['email'][admin['email'].find('@'):]
                    if admin['twoFactorAuthEnabled'] is False and \
                            (email == '@symplexity.com'
                             or email == '@ensi.com'):
                        symp_2fa_disabled.append(
                            {'organization': customer['name'],
                             'user': admin['name'],
                             'email': admin['email'],
                             'twoFactorAuthEnabled': admin['twoFactorAuthEnabled']})
            except TypeError:
                error = 'To make requests you must first enable API access'
                if customer['admins']['errors'][0][0:49] == error:
                    symp_2fa_disabled.append({'organization': customer['name'],
                                              'error': error})
    with open((File_output_dir + '\\meraki_2fa_disabled.json'), 'w') as mfa_file:
        json.dump(symp_2fa_disabled, mfa_file, indent=4)
    return symp_2fa_disabled


Token, Headers = auth_meraki_api()
parse_admins(get_customers_admins(get_symp_meraki_customers(Token, Headers)))
