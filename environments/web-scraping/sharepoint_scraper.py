"""
Script to crawl Sharepoint pages and output Wiki document libraries
as files in a folder structure.

Author: Jon Husen

TODO: Look into using html5lib instead of the built-in html.parser
    https://www.crummy.com/software/BeautifulSoup/bs4/doc/#differences-between-parsers

"""

import os
import sys
import re
import json

import yaml
import requests
import msal
import html2text
from bs4 import BeautifulSoup
from selenium import webdriver



# Authenticate using O365 module
# credentials = (appid, '')
# account = O365.Account(credentials)
# if account.authenticate(scopes=['basic', 'sharepoint']):
#    print('Authenticated!')

# sharepoint = account.sharepoint()
# root_site = sharepoint.get_root_site()


def o365_auth(clientid, authority, scope):
    """Takes the client id of an app registration and the authentication
    url as authority to initiate the device-flow authentication.
    User will need to enter the device code into the authorization site
    to complete authentication.
    Returns the authentication token."""
    global headers

    app = msal.PublicClientApplication(client_id=clientid, authority=authority)
    token = None
    headers = None
    accounts = app.get_accounts()

    if accounts:
        for a in accounts:
            print(a["username"])
            if input("Select this account? y/n") == "y":
                chosen = a
                break
        token = app.acquire_token_silent(scope, account=chosen)

    if not token:
        flow = app.initiate_device_flow(scopes=scope)
        if "user_code" not in flow:
            raise ValueError(
                "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4)
            )
        print(flow['message'])
        sys.stdout.flush()
        token = app.acquire_token_by_device_flow(flow)

    if "access_token" in token:
        headers = {'Authorization': "Bearer " + token['access_token']}
        graph_data = requests.get(url=endpoint, headers=headers).json()
        print("Graph API call result = %s" % json.dumps(graph_data, indent=2))
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))
    return token


def scrape_pages(url):
    browser.get(url=url)
    source = browser.page_source
    handled.append(url)

    soup = BeautifulSoup(source, "html.parser")
    title = soup.find(name="span", id=content_h1_title)
    inner_div = soup.find(name="div", id=content_div_id)
    if inner_div is not None:
        links = inner_div.find_all("a")
        for link in links:
            print(link)
            if wiki_base_url in link['href']:
                newoutput = link['href'].replace(wiki_base_url, "").replace("%20", "+").replace(".aspx", "")
                print(newoutput)


with open("config.yml", 'r') as yml_read:
    config = yaml.load(yml_read, Loader=yaml.BaseLoader)
url = config['sharepoint_url'] + config['wiki_base_url'] + config['wiki_index']
# globals
appid = config['appid']
scrape_recursively = config['scrape_recursively']
content_h1_title = config['content_h1_title']
content_div_id = config['content_div_id']
sharepoint_url = config['sharepoint_url']
wiki_base_url = config['wiki_base_url']
wiki_index = config['wiki_index']
add_legacy_link = config['add_legacy_link']
appid = config['appid']
scope = config['scope']
authority = config['authority']
endpoint = config['endpoint']
handled = []
empties = []
has_images = []
headers = None

# Initialize browser and pause for interactive logon
browser = webdriver.Chrome()
browser.get(url)
browser.implicitly_wait(60)  # Wait for interactive login
