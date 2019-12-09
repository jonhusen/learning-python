"""
Script to crawl Sharepoint pages and output Wiki document libraries
as files in a folder structure.

Author: Jon Husen

TODO: Look into using html5lib instead of the built-in html.parser
    https://www.crummy.com/software/BeautifulSoup/bs4/doc/#differences-between-parsers
TODO: evaluate usefulness of "exclusions" url list
TODO: fix browsing back from a "Page not found." Currently does not go back enough times

"""

import os
import sys
import json
import time
import glob
from pathlib import Path

import yaml
import requests
import html5lib
from bs4 import BeautifulSoup
from selenium import webdriver


def crawl_wiki_pages(url):
    """Crawls the pages of a Sharepoint wiki site and creates a tree

    Each page gets a folder for storing the html body of the wiki
    page and other site assets found on the page. Folders for valid
    links found on the page are created and child pages are crawled.
    :param url: URL of the top level page to be crawled
    :return: None
    """
    if browser.current_url != url:
        browser.get(url=url)
        time.sleep(1)
    source = browser.page_source

    soup = BeautifulSoup(source, "html5lib")
    title = soup.find(name="span", id=content_h1_title)
    inner_div = soup.find(name="div", id=content_div_id)
    stripped_title = title.text.lstrip().rstrip()

    # Add folder for page and move cwd into folder
    current_dir = Path.cwd() / stripped_title
    if not os.path.exists(current_dir):
        os.makedirs(current_dir)
    os.chdir(current_dir)

    files_in_cwd = [file for file in glob.glob("*.*")]
    if (stripped_title + ".html") not in files_in_cwd:
        save_page(title, inner_div)

    url_tracker.append(browser.current_url)
    handled.append({
        "page_name": stripped_title,
        "path": Path.cwd() / (stripped_title + ".html"),
        "url": url
        })

    if inner_div is not None:
        links = inner_div.find_all("a")

    if links is None:
        go_back()
    else:
        for link in links:
            # Skip malformed link tags
            if "href" not in link.attrs.keys():
                continue

            # Handle links to Sharepoint/portal homepage
            if link["href"] in exclusions:
                continue

            # Handle case where page links to itself
            if wiki_base_url in link["href"] \
                    and browser.current_url[browser.current_url.find(wiki_base_url):] in \
                    link["href"][link["href"].find(wiki_base_url):]:
                continue

            # Handle links dynamically classified as missing
            if "class" in link.attrs.keys():
                if "ms-missinglink" in link["class"]:
                    continue

            # Handle duplicate links
            if any(item for item in handled if link["href"] in item["url"]):
                item = [item for item in handled if link["href"] in item["url"]][0]
                duplicate_page(item)
                log_message = "DUPLICATE: " + item["page_name"] + " now located at " + str(item["path"])
                write_log(log_message)
            # if any(item for item in url_tracker if link["href"] in item):
            #     continue

            # Takes relative Sharepoint links and rewrites them as full links
            elif link["href"].startswith(wiki_base_url) \
                    and link["href"].endswith(".aspx"):
                fullpath = sharepoint_url + link["href"]
                browser.get(fullpath)
                time.sleep(1)
                if browser.title == "Page not found":
                    while browser.title == "Page not found" or \
                            browser.title == "Error":
                        browser.back()
                elif fullpath not in exclusions:
                    crawl_wiki_pages(fullpath)
                else:
                    write_log("EXCEPTION: " + fullpath)
                    browser.back()
            # elif redirect_url in link["href"]:
            elif link["href"].startswith(redirect_url):
                # Handle legacy url which redirects to Sharepoint
                try:
                    fullpath = link["href"].replace(
                        redirect_url,
                        sharepoint_url
                    )
                    browser.get(fullpath)
                    time.sleep(1)
                    if browser.title == "Page not found":
                        while browser.title == "Page not found" or \
                                browser.title == "Error":
                            browser.back()
                    elif fullpath not in exclusions:
                        crawl_wiki_pages(fullpath)
                    else:
                        write_log("EXCEPTION: " + fullpath)
                        browser.back()
                except:
                    write_log("EXCEPTION: " + fullpath)
                    while browser.title == "Page not found" or \
                            browser.title == "Error":
                        browser.back()
        go_back()


def save_page(title, body):
    """Saves body of Sharepoint wiki pages, images, and other items to a folder.

    Adds a note to the top of the page with a link to the original Sharepoint
    site. Downloads images on the page to the cwd. Downloads page assets
    from links on the page. Rewrites all links as relative links.
    :param title: HTML Title tag of the current page viewed in selenium
    :param body: Main HTML body of the content found on the page
    :return: No return value
    """
    # Creates note and link to the original Sharepoint site
    title.a.attrs["href"] = sharepoint_url + title.a.attrs["href"]
    legacy_message = BeautifulSoup(
        "<div><p>This page has been automatically exported from Sharepoint.</p>"
        + "<p>If something doesn't look right you can go to the legacy link:"
        + str(title) + "</p><br>"
        + "<h1>" + title.text + "</h1>" + "</div>",
        "html5lib"
    )

    # Saves images on the page to the cwd
    images = body.find_all("img")
    if images:
        for img in images:
            if "src" in img.attrs.keys():
                if wiki_site_assets_url in img["src"]:  # or not img["src"].startswith("http"):
                    img_name = img["src"].rsplit("/")[-1]
                    img_url = sharepoint_url + img["src"]
                    download_content(img_url, img_name)
                    img["src"] = img_name
                elif img["src"].startswith("http"):
                    try:
                        img_name = img["src"].rsplit("/")[-1]
                        download_content(img["src"], img_name)
                        img["src"] = img_name
                    except:
                        pass

    # Saves items in non-page links to cwd
    body_links = body.find_all("a")
    if body_links:
        for link in body_links:
            if "href" in link.attrs.keys() \
                    and link["href"].startswith(wiki_site_assets_url) \
                    and not link["href"].endswith(".aspx"):
                file_url = sharepoint_url + link["href"]
                file_name = link["href"].rsplit("/")[-1]
                download_content(file_url, file_name)
                link["href"] = file_name

    output = legacy_message.prettify() + body.prettify()
    page_soup = BeautifulSoup(output, "html5lib")
    page_name = title.text.rstrip().lstrip() + ".html"
    with open(page_name, "wb") as writer:
        writer.write(page_soup.prettify(encoding="utf-8"))

    # Open html page to rewrite wiki links to relative references
    # This allows the original list of links for the page to still be crawlable
    with open(page_name, "rb") as reader:
        mod_source = reader.read()

    mod_soup = BeautifulSoup(mod_source, "html5lib")
    mod_body = mod_soup.find(name="div", id=content_div_id)
    mod_links = mod_body.find_all("a")

    for link in mod_links:
        if "href" in link.attrs.keys() \
                and link["href"].startswith(wiki_base_url):
            link["href"] = "./" + link["href"].split("/")[-1].replace(".aspx", "") \
                           + "/" + link["href"].split("/")[-1].replace(".aspx", ".html")

    with open(page_name, "wb") as writer:
        writer.write(mod_soup.prettify(encoding="utf-8"))

    page_count += 1


def duplicate_page(duplicate):
    os_root = str(Path.cwd())[:str(Path.cwd()).find(sharepoint_url.lstrip("https://"))]
    dup_relative_path = str(duplicate["path"])[str(duplicate["path"]).find(sharepoint_url.lstrip("https://")):]
    local_url = os_root + dup_relative_path
    duplicate_message = BeautifulSoup(
        "<div><p>This page is a duplicate.</p>"
        + "<p>The page: \"" + duplicate["page_name"] + "\" is now located at:<br>"
        + "<a href=\"" + local_url + "\">" + local_url + "</a></p><br>"
        + "<p>If something doesn't look right you can go to the legacy link:"
        + "<a href=\"" + duplicate["url"] + "\">" + duplicate["url"] + "</a></p></div>",
        "html5lib"
    )

    page_soup = BeautifulSoup(duplicate_message.prettify(), "html5lib")
    page_name = duplicate["page_name"] + ".html"

    current_dir = Path.cwd() / duplicate["page_name"]
    if not os.path.exists(current_dir):
        os.makedirs(current_dir)
    os.chdir(current_dir)

    with open(page_name, "wb") as writer:
        writer.write(page_soup.prettify(encoding="utf-8"))

    os.chdir(Path.cwd().parent)


def download_content(item_url, item_name):
    """Downloads content of a crawled page.

    Creates a Requests session using cookies from the selenium browser instance.
    Uses the requests session to get urls for item to download.
    Downloads item to cwd.
    :param item_url: URL of item to be downloaded
    :param item_name: Name of item to be created
    :return: None
    """
    cookies = browser.get_cookies()
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie["name"], cookie["value"])
    item_request = session.get(url=item_url)
    with open(item_name, "wb") as item:
        item.write(item_request.content)


def go_back():
    """Takes the environment back one level.

    Sends the browser back to the previous page.
    Adds a delay to allow the page to render in case of delay in processing.
    Moves to the parent of the current working directory
    :return: None
    """
    browser.back()
    time.sleep(1)
    os.chdir(Path.cwd().parent)
    url_tracker.pop()


def write_log(output):
    log_file = Path.joinpath(local_root_dir / wiki_base_dir / "crawl_log.log")
    with open(log_file, "a") as log:
        log.writelines(output + "\n")

# Read YAML config options
with open("config.yml", "r") as yml_read:
    config = yaml.load(yml_read, Loader=yaml.BaseLoader)

# Globals
content_h1_title = config["content_h1_title"]
content_div_id = config["content_div_id"]
sharepoint_url = config["sharepoint_url"]
wiki_base_url = config["wiki_base_url"]
wiki_site_assets_url = config["wiki_site_assets_url"]
wiki_home = config["wiki_home"]
redirect_url = config["redirect_url"]
url_tracker = []
handled = []
exclusions = ["https://corsicatechnologies.sharepoint.com/TST/TST%20Wiki/Home.aspx",
              "https://corsicatechnologies.sharepoint.com/SitePages/Welcome.aspx",
              "https://corsicatechnologies.sharepoint.com/",
              "http://portal.corsicatech.com/",
              "http://portal.corsicatech.com/tst"]
page_count = 0

url = sharepoint_url + wiki_base_url + wiki_home
# url = "https://corsicatechnologies.sharepoint.com/TST/TST%20Wiki/The%20Inn%20at%20Chesapeake%20Bay%20Beach%20Club.aspx"
local_root_dir = Path.cwd()
wiki_base_dir = sharepoint_url.lstrip("https://") + wiki_base_url

# Initialize browser and pause for interactive logon
browser = webdriver.Chrome()
browser.get(url)
time.sleep(60)  # Wait for interactive login

# Creates a local path to mirror the Sharepoint Wiki library path
if not os.path.exists(wiki_base_dir):
    os.makedirs(wiki_base_dir)
os.chdir(local_root_dir / wiki_base_dir)

crawl_wiki_pages(url)

write_log("Page Count: " + page_count + "\n")

# for testing
