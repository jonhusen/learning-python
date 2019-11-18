"""
Module to use the Meraki API to perform audit related tasks for an MSP.

Requires requests library

Examples:
    # Get syslog configs for all customers as json file
    headers = auth_meraki_api()
    customers = get_meraki_customers(headers)
    networks = get_networks(customers, headers)
    syslog = get_syslog_servers(networks, headers)
    write_json_to_file(syslog)

    # Get 2fa configuration for admins accounts at each customer
    headers = auth_meraki_api()
    customers = get_meraki_customers(headers)
    admins = get_customers_admins(customers, headers)
    audit = parse_admins(admins)
    write_json_to_file(audit)

Author: Jon Husen
"""


import os
import json
from getpass import getpass

import requests

Api_url = 'https://api.meraki.com/api/v0/'


def auth_meraki_api():
    """Asks for api key and returns the headers for a request."""
    token = getpass("Symplexity API Key: ")
    headers = {
        'Accept': '*/*',
        'X-Cisco-Meraki-API-Key': token
    }
    return headers


def get_meraki_customers(headers):
    """Accepts token and headers variables.
    Returns a json list of dicts of customer organizations
    from the Meraki API"""
    print("Retrieving customer list.")
    customer_url = Api_url + "organizations/"
    response = requests.get(url=customer_url, headers=headers)
    customers_json = response.json()  # List of dicts
    return customers_json


def get_customers_admins(customers_json, headers):
    """Takes customers list and retrieves a dict of admins for each customer"""
    print("Retrieving admin lists.")
    customer_admins_json = []
    for customer in customers_json:
        admin_url = Api_url + "organizations/" + customer['id'] + '/admins'
        response_admins = requests.get(url=admin_url, headers=headers)
        admins_json = response_admins.json()
        customer_admins_json.append({'name': customer['name'],
                                     'id': customer['id'],
                                     'admins': admins_json})
    return customer_admins_json


def parse_admins(customer_admins_json):
    """Takes a list of customer admins and writes a file of symplexity
    logins where 2fa is not enabled"""
    print("Checking for MFA and API access")
    symp_2fa_disabled = []
    for customer in customer_admins_json:
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
    return symp_2fa_disabled


def get_networks(customers_json, headers):
    """Accepts a json list of customers.
    Returns a json list of network information associated with each customer
    Errors of not having the API access enabled will write to an 'error' key
    instead of a 'network' key"""
    print("Retrieving customer networks.")
    networks_list = []
    for customer in customers_json:
        net_url = Api_url + 'organizations/' + customer['id'] + '/networks'
        try:
            response = requests.get(url=net_url, headers=headers)
            networks_json = response.json()
            networks_list.append({'organizationId': customer['id'],
                                  'organizationName': customer['name'],
                                  'networks': networks_json})
        except TypeError:
            error = 'To make requests you must first enable API access'
            if networks_json['errors'][0][0:49] == error:
                networks_list.append({'organizationId': customer['id'],
                                      'organizationName': customer['name'],
                                      'error': error})
    return networks_list


def get_network_l3fwrules(networks_json, headers):
    """Accepts a json list of networks for each organization.
    Returns a json list of network devices for each network"""
    for customer in networks_json:
        if 'networks' in customer:
            for network in customer['networks']:
                if isinstance(network, dict) and 'appliance' in network['productTypes']:
                    network_l3fwrules_url = Api_url \
                                            + 'networks/' \
                                            + network['id'] \
                                            + '/l3FirewallRules'
                    request = requests.get(url=network_l3fwrules_url, headers=headers)
                    fwrules = request.json()
                    network['l3FirewallRules'] = fwrules
    networks_fwrules_json = networks_json
    return networks_fwrules_json


def audit_umbrelladns(networks_fwrules):
    """Accepts a list of firewall rules for a client
    Checks for rules to allow DNS lookups to Umbrella and
    deny all other DNS lookups.
    Returns a list of clients and a boolean of whether Umbrella DNS
    is configured properly"""
    umbrelladns_audit = []
    host1 = '208.67.222.222/32'
    host2 = '208.67.220.220/32'
    for customer in networks_fwrules:
        for network in customer['networks']:
            umbrella_allow, dns_deny = 'False', 'False'
            if 'l3FirewallRules' in network:
                for rule in network['l3FirewallRules']:
                    destcidr = rule['destCidr'].split(",")
                    if rule['policy'] is 'allow' \
                            and rule['protocol'] is 'tcp' \
                            and rule['destPort'] is '53' \
                            and (host1 in destcidr and host2 in destcidr):
                        umbrella_allow = 'True'
                    if rule['policy'] is 'allow' \
                            and rule['protocol'] is 'udp' \
                            and rule['destPort'] is '53' \
                            and (host1 in destcidr and host2 in destcidr):
                        umbrella_allow = 'True'
                    if rule['policy'] is 'deny' \
                            and rule['protocol'] is 'tcp' \
                            and rule['destPort'] is '53' \
                            and rule['destCidr'] is 'any':
                        dns_deny = 'True'
                    if rule['policy'] is 'deny' \
                            and rule['protocol'] is 'udp' \
                            and rule['destPort'] is '53' \
                            and rule['destCidr'] is 'any':
                        dns_deny = 'True'
            if umbrella_allow is 'True' and dns_deny is 'True':
                umbrelladns_audit.append({
                    'name': network['name'],
                    'organizationId': network['organizationId'],
                    'umbrellaDns': 'True'
                })
            else:
                umbrelladns_audit.append({
                    'name': network['name'],
                    'organizationId': network['organizationId'],
                    'umbrellaDns': 'False'
                })
    return umbrelladns_audit


def get_syslog_servers(networks_json, headers):
    """Accepts a json list of customer networks.
    Returns a json list of customer networks with the syslog server
    configuration appended to the network information"""
    print("Retrieving syslog configuration for each network.")
    for customer in networks_json:
        if 'networks' in customer:
            for network in customer['networks']:
                syslog_url = Api_url \
                             + 'networks/' \
                             + network['id'] \
                             + '/syslogServers'
                response = requests.get(url=syslog_url, headers=headers)
                syslog_json = response.json()
                # Adds syslog config info to the networkId dict
                network['syslogServer'] = syslog_json
    return networks_json


def write_json_to_file(json_output):
    """Accepts json and writes the json input to a file.
    Prompts for output dir and name of file and creates it if necessary"""
    file_output_dir = input("Where would you like to save the output? ")
    file_name = input("What would you like to call the file? ")
    output = file_output_dir + '\\' + file_name + ".json"
    # Checks for existence of the output dir and creates if it does not exist
    if not os.path.isdir(file_output_dir):
        os.makedirs(file_output_dir)
    with open(output, 'w') as json_file:
        json.dump(json_output, json_file, indent=4)


headers = auth_meraki_api()
customers = get_meraki_customers(headers)


# # Get syslog configs for all customers as json file
networks = get_networks(customers, headers)
# syslog = get_syslog_servers(networks, headers)
# write_json_to_file(syslog)
#
rules = get_network_l3fwrules(networks, headers)
write_json_to_file(rules)
# Get 2fa configuration for admins accounts at each customer
# admins = get_customers_admins(customers, headers)
# audit = parse_admins(admins)
# write_json_to_file(audit)
