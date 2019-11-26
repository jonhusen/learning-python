"""
Script to crawl Sharepoint pages and output Wiki document libraries
as files in a folder structure.

Author: Jon Husen

TODO: Look into using html5lib instead of the built-in html.parser
    https://www.crummy.com/software/BeautifulSoup/bs4/doc/#differences-between-parsers

"""

import os
import sys
import json
import time
import glob
from pathlib import Path

import yaml
import requests
import msal
import html2text
from bs4 import BeautifulSoup
from selenium import webdriver


# Authenticate using O365 module
# credentials = (appid, "")
# account = O365.Account(credentials)
# if account.authenticate(scopes=["basic", "sharepoint"]):
#    print("Authenticated!")

# sharepoint = account.sharepoint()
# root_site = sharepoint.get_root_site()


def o365_auth(clientid, authority, scope):
    """
    Takes the client id of an app registration and the authentication
    url as authority to initiate the device-flow authentication.
    User will need to enter the device code into the authorization site
    to complete authentication.

    :param clientid: AppID/ClientID of the Azure App Registration
    :param authority: Login page used to authenticate
    :param scope: Permissions requested
    :return: Authentication token
    """
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
        print(flow["message"])
        sys.stdout.flush()
        token = app.acquire_token_by_device_flow(flow)

    if "access_token" in token:
        headers = {"Authorization": "Bearer " + token["access_token"]}
        graph_data = requests.get(url=endpoint, headers=headers).json()
        print("Graph API call result = %s" % json.dumps(graph_data, indent=2))
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))
    return token


def crawl_wiki_pages(url):

    browser.get(url=url)
    source = browser.page_source
    handled.append(url)

    soup = BeautifulSoup(source, "html.parser")
    title = soup.find(name="span", id=content_h1_title)
    inner_div = soup.find(name="div", id=content_div_id)
    stripped_title = title.text.lstrip().rstrip()

    # Add folder for page and move into folder
    current_dir = Path.cwd() / stripped_title
    if not os.path.exists(current_dir):
        os.makedirs(current_dir)
    os.chdir(current_dir)

    files_in_cwd = [f for f in glob.glob("*.*")]
    if stripped_title not in files_in_cwd:
        save_page(title, inner_div)

    if inner_div is not None:
        links = inner_div.find_all("a")
        if links is None:
            go_back()
        else:
            for link in links:
                if wiki_base_url in link["href"]:
                    fullpath = sharepoint_url + link["href"]
                    if fullpath not in handled:
                        crawl_wiki_pages(fullpath)


def save_page(title, body):
    """
    Saves body of Sharepoint wiki pages and images to a folder.
    Renames image links to relative links within the folder.

    :param title: HTML Title tag of the current page viewed in selenium
    :param body: Main HTML body of the content found on the page
    :return: No return value
    """
    # Creates note and link to the original Sharepoint site
    title.a.attrs["href"] = config["sharepoint_url"] + title.a.attrs["href"]
    legacy_message = BeautifulSoup(
        "<div><p>This page has been automatically exported from Sharepoint.</p>"
        + "<p>If something doesn't look right you can go to the legacy link:"
        + str(title) + "</p>"
        + "<h1>" + title.text + "</h1>" + "</div>",
        "html.parser"
    )

    # Saves images on the page to the cwd
    images = body.find_all("img")
    if images:
        for img in images:
            img_url = sharepoint_url + img["src"]
            browser.execute_script("window.open('');")
            browser.switch_to.window(browser.window_handles[1])
            browser.get(img_url)
            browser.get_screenshot_as_file(img["alt"])
            time.sleep(3)
            browser.close()
            browser.switch_to.window(browser.window_handles[0])
            img["src"] = img["alt"]

    output = legacy_message.prettify() + "\n" + body.prettify()

    page_name = title.text.rstrip().lstrip() + ".html"
    with open(page_name, "w") as writer:
        writer.write(output)


def go_back():
    """
    Sends the browser back to the previous page.
    Moves to the parent of the current working directory
    :return: None
    """
    browser.back()
    os.chdir(Path.cwd().parent)


# Read YAML config options
with open("config.yml", "r") as yml_read:
    config = yaml.load(yml_read, Loader=yaml.BaseLoader)

# Globals
scrape_recursively = config["scrape_recursively"]
content_h1_title = config["content_h1_title"]
content_div_id = config["content_div_id"]
sharepoint_url = config["sharepoint_url"]
wiki_base_url = config["wiki_base_url"]
wiki_index = config["wiki_index"]
add_legacy_link = config["add_legacy_link"]
appid = config["appid"]
scope = config["scope"]
authority = config["authority"]
endpoint = config["endpoint"]
handled = []
empties = []
has_images = []
headers = None

url = sharepoint_url + wiki_base_url + wiki_index
base_dir = sharepoint_url.lstrip("https://") + wiki_base_url

if not os.path.exists(base_dir):
    os.makedirs(base_dir)
os.chdir(Path.cwd() / base_dir)

# Initialize browser and pause for interactive logon
browser = webdriver.Chrome()
browser.get(url)
browser.implicitly_wait(60)  # Wait for interactive login
