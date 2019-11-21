
import os
import json
from getpass import getpass

import requests

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
        customer_result = {
            'organizationId': customer['organizationId'],
            'organizationName': customer['organizationName']
        }
        for network in customer['networks']:
            umbrella_allow, dns_deny = 'False', 'False'
            if 'l3FirewallRules' in network:
                for rule in network['l3FirewallRules']:
                    destcidr = rule['destCidr'].split(",")
                    if rule['policy'] == 'allow' \
                            and rule['protocol'] == 'tcp' \
                            and rule['destPort'] == '53' \
                            and (host1 in destcidr and host2 in destcidr):
                        umbrella_allow = 'True'
                    if rule['policy'] == 'allow' \
                            and rule['protocol'] == 'udp' \
                            and rule['destPort'] == '53' \
                            and (host1 in destcidr and host2 in destcidr):
                        umbrella_allow = 'True'
                    if rule['policy'] == 'deny' \
                            and rule['protocol'] == 'tcp' \
                            and rule['destPort'] == '53' \
                            and rule['destCidr'] == 'Any':
                        dns_deny = 'True'
                    if rule['policy'] == 'deny' \
                            and rule['protocol'] == 'udp' \
                            and rule['destPort'] == '53' \
                            and rule['destCidr'] == 'Any':
                        dns_deny = 'True'
            if umbrella_allow is 'True' and dns_deny is 'True':
                customer_result['umbrellaDns'] = 'True'
            else:
                customer_result['umbrellaDns'] = 'False'
        umbrelladns_audit.append(customer_result)
    return umbrelladns_audit


with open('c:\\temp\\fw_rules_test.json', 'r') as read_file:
    rules = json.load(read_file)

audit = audit_umbrelladns(rules)
