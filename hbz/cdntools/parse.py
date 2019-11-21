#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# import sys
# from datetime import datetime


#def css_filter(tag):
#    return tag.has_attr('href')

IGNORE_RELS = ('dns-prefetch', 'alternate')


def rels_in_ignored_rels(rels):
    """Return True if any of the rels attributes is in the IGNORE_RELS list"""

    result = False
    for rel in rels:
        if rel in IGNORE_RELS:
            result = True
            break
    return result


class CDN:

    def __init__(self, site):

        self.site = site
        r = requests.get(site)
        self.soup = BeautifulSoup(r.text, features="html.parser")
        self.files = []

    def link(self):
        head = self.soup.head
        #css_files = head.find_all(css_filter, type="text/css")
        link_files = head.find_all("link")

        for link_file in link_files:
            if link_file.has_attr('href'):
                href = link_file.attrs['href']
                rel = link_file.attrs['rel']
                if not rels_in_ignored_rels(rel):
                    self.files.append(href)

    def js(self):

        js_files = self.soup.find_all("script")
        for js_file in js_files:
            if js_file.has_attr('src'):
                #print(js_file)
                src = js_file.attrs['src']
                self.files.append(src)


def main():
    parser = argparse.ArgumentParser(description='CDN gathering')
    parser.add_argument('site', help='URL of website')
    parser.add_argument('-a', '--all', action="store_true", help='include also local css/js')
    args = parser.parse_args()

    all = args.all

    cdn = CDN(args.site)
    cdn.link()
    cdn.js()

    o = urlparse(args.site)
    hostname = o.netloc

    for file in cdn.files:
        o = urlparse(file)
        if o.netloc != hostname:
            print(file)
        elif all:
            print(file)



if __name__ == '__main__':

    url = "https://stadtarchivkoblenz.wordpress.com"
    cdn = CDN(url)
    cdn.link()
    cdn.js()
    for file in cdn.files:
        print(file)
