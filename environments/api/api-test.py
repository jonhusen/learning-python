
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


with open('c:\\temp\\fw_rules_test.json', 'r') as rules_file:
    rules = json.loads(rules_file)

audit = audit_umbrelladns(rules)
