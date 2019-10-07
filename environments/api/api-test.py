import json
import requests
from getpass import getpass

orgs_url = 'https://api.meraki.com/api/v0/organizations/'

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
    response = requests.get(url=orgs_url, headers=headers)
    customers = response.json()  # List of dicts
    with open(r'c:\test\meraki_customers.json', 'w') as f:
       json.dump(customers, f, indent=4)
    return customers


customers = get_symp_meraki_customers(token, headers)

def get_customers_admins(customers):
    """Takes customers list and retrieves a dict of admins for each customer"""
    customer_admins = []
    for customer in customers:
        admin_url = orgs_url + customer['id'] + '/admins'
        response_admins = requests.get(url=admin_url, headers=headers)
        admins = response_admins.json()
        customer_admins.append({'name': customer['name'], 'id': customer['id'], 'admins': admins})
    with open(r'c:\test\meraki_admins.json', 'w') as a:
        json.dump(customer_admins, a, indent=4)
    return customer_admins
