import os
import re

import yaml
import O365
import html2text
from bs4 import BeautifulSoup


def sharepoint_scrape():
    account = O365.account()


with open("config.yml", 'r') as yml_read:
    config = yaml.load(yml_read, Loader=yaml.BaseLoader)
url = config['sharepoint_url'] + config['wiki_base_url'] + config['wiki_index']
# globals
appid = config['appid']
scrape_recursively = config['scrape_recursively']
content_div_id = config['content_div_id']
sharepoint_url = config['sharepoint_url']
wiki_base_url = config['wiki_base_url']
wiki_index = config['wiki_index']
add_legacy_link = config['add_legacy_link']
handled = []
empties = []
has_images = []


credentials = (appid, '')
account = O365.Account(credentials)
if account.authenticate(scopes=['basic', 'sharepoint']):
   print('Authenticated!')

sharepoint = account.sharepoint()
root_site = sharepoint.get_root_site()

