#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, urljoin
import logging
import pkg_resources

version = pkg_resources.require("hbz.cdntools")[0].version
logger = logging.getLogger('cdnparse')

# link with following rels are not added to the precrawl list but to the hostnames
IGNORE_RELS = ('dns-prefetch', 'preconnect', 'alternate', 'search', 'shortlink')
DEFAULT_LOGFILE = "cdnparse.log"
HOSTNAMES_FILE = "hostnames.txt"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
SITE ="site.html"

def rels_in_ignored_rels(rels):
    """Return True if any of the rels attributes is in the IGNORE_RELS list"""

    result = False
    for rel in rels:
        if rel in IGNORE_RELS:
            result = True
            break
    return result



class CDN:

    def __init__(self, url, keep, cookies, useragent, no_check_certificate):

        logger.info("received %s" % url)
        headers = {
            'User-Agent': useragent,
        }
        if cookies:
            logger.info("Using Cookies: %s" % cookies)
            headers['Cookies'] = cookies

        if no_check_certificate:
            self.ssl_verify=False
        else:
            self.ssl_verify=True

        r = requests.get(url, headers=headers, verify=self.ssl_verify)
        url_final = r.url
        logger.info("parsing %s" % url_final)
        if keep:
            html = open(SITE, "w")
            html.write(r.text)
            logger.info("saving file as %s" % SITE)

        self.site = urlparse(url_final)

        self.url = urlparse(url)

        self.scheme = self.site.scheme
        self.netloc = self.site.netloc
        self.path = self.site.path
        self.soup = BeautifulSoup(r.text, features="html.parser")
        self.files = []

    def is_valid_url(self, url):
        """Return True if string is a valid url
        
        Valid URLs have a scheme and a netloc (Domain). Sometimes css
        backgrounds only contain file names
        """
        result = urlparse(url)
        return all([result.scheme, result.netloc])


    def extract_urls_from_css(self, css_address):
        """Return URL found in stylesheets

        CSS files may contain links to background images. Since we crawl unrecursivley
        we have to find them manually and put them in the cdn.txt
        """
        if not self.is_valid_url(css_address):
            logger.warning(f"Invalid URL: {css_address}")
            return None

        response = requests.get(css_address, verify=self.ssl_verify)
        
        if response.status_code == 200:
            css_content = response.text
            # This regex matches URLs inside url() functions
            pattern = r'url\((.*?)\)'
            urls = re.findall(pattern, css_content)
        else:
            logger.warning(f"Failed to retrieve the CSS file. Status code: {response.status_code}")
            urls = []

        for url in urls:
            url = url.strip('"\'')
            if not self.is_valid_url(url):
                url = urlunparse((self.scheme, self.netloc, url, '', '', ''))
            if url not in  self.files:
                self.files.append(url)

    def _normalize(self, url):
        """Return full url with hostname of given url.

        If the url is relativ or absolute, but without hostname, it will
        be added. External URLs are passed unchanged.
        """
        u = urlparse(url)
        if u.netloc == '':
            path = urljoin(self.path, u.path)
            url = urlunparse((self.scheme, self.netloc, path, '', '', ''))
            r = requests.head(url)
            logger.info("%s [HTTP %s]" % (url, r.status_code))
            return url
        else:
            return url

    def link(self):
        """Return all CSS files found in the head.

        Not all sites a written well and include proper rel="stylesheet" and
        type="text/css" attributes. It's safer to scrape everything and
        exclude certain rel-attributes.
        """
        head = self.soup.head
        # css_files = head.find_all(css_filter, type="text/css")
        link_files = head.find_all("link")

        for link_file in link_files:
            if link_file.has_attr('href'):
                href = link_file.attrs['href']
                logger.info("found %s" % href)
                rel = link_file.attrs.get('rel', [])      # rel is a list
                if not rels_in_ignored_rels(rel):
                    url = self._normalize(href)
                    self.files.append(url)
                    logger.info("added %s to cdn files [rel=%s]" % (url, ' '.join(rel)))
                    self.extract_urls_from_css(url)
                else:
                    logger.info("ignored %s [rel=%s]" % (href, ' '.join(rel)))

    def js(self):
        """Return all JS files in head and body.

        Javascript can be everywhere, not just the head.
        type="text/javascript" is not always properly used.
        """
        js_files = self.soup.find_all("script")
        for js_file in js_files:
            if js_file.has_attr('src'):
                src = js_file.attrs['src']
                logger.info("found %s" % src)
                url = self._normalize(src)
                self.files.append(url)
                logger.info("added %s to cdn files" % url)

    def style(self):
        """Return CSS files which are included via @include

        everything between ( and ) ist considered an url
        <!-- @import url(https:...css; --></style>
        """
        styles = self.soup.find_all("style")
        for style in styles:
            src = style.text.split(')')[0].split('(')[-1]
            url = self._normalize(src)
            self.extract_urls_from_css(url)
            self.files.append(url)

    def hostname(self):
        """Extract external hostnames von img tags in the body and link tags in the head
           and collect them in a separate file.
        """
        imgs = self.soup.find_all("img")
        hostnames = []
        for img in imgs:
            if img.has_attr('src'):
                src = img.attrs['src']
                url = urlparse(src)
                logger.info("found %s" % src)
                if url.netloc:
                    if url.netloc not in hostnames and url.netloc != self.netloc:
                        logger.info("added %s to hostnames" % url.netloc)
                        hostnames.append(url.netloc)

        head = self.soup.head
        link_files = head.find_all("link")

        for link_file in link_files:
            if link_file.has_attr('href'):
                href = link_file.attrs['href']
                logger.info("found %s" % href)
                rel = link_file.attrs.get('rel', []) # rel is a list
                if rels_in_ignored_rels(rel):
                    url = urlparse(self._normalize(href))
                    if url.netloc:
                        if url.netloc not in hostnames and url.netloc != self.netloc:
                            logger.info("added %s to hostnames" % url.netloc)
                            hostnames.append(url.netloc)
        if hostnames:
            logger.info("writing additional hostnames to %s" % HOSTNAMES_FILE)
            with open(HOSTNAMES_FILE, "w") as f:
                for hostname in hostnames:
                    f.write(hostname + "\n")
        else:
            logger.info("no additional hostnames found")
        


def main():

    parser = argparse.ArgumentParser(description='CDN gathering')
    parser.add_argument('url', help='URL of website')
    parser.add_argument('-a', '--all', action="store_true", help='include also local css/js')
    parser.add_argument('-k', '--keep', action="store_true", help='keep the downloaded HTML file')
    parser.add_argument('-n', '--no-check-certificate', action="store_true", help='do not validate SSL certificates')
    parser.add_argument('-c', '--cookies', help='Cookiestring')
    parser.add_argument('-u', '--useragent', help='User Agent (default: Google Chrome)')
    parser.add_argument('-l', '--logfile', default="cdnparse.log", help='Name of the logfile (default: %s)' % DEFAULT_LOGFILE)
    parser.add_argument('--version', action='version', version=version)

    args = parser.parse_args()
    logfile = args.logfile
        
    all = args.all
    
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    fh = logging.FileHandler(logfile)
    fh.setFormatter(formatter)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    cdn = CDN(args.url, args.keep, args.cookies, args.useragent, args.no_check_certificate)
    cdn.link()
    cdn.js()
    cdn.style()
    cdn.hostname()

    for url in cdn.files:
        o = urlparse(url)
        if o.netloc != cdn.netloc or all:
            print(url)


if __name__ == '__main__':

    # url = "https://stadtarchivkoblenz.wordpress.com"
    # url = "https://www.vg-lingenfeld.de/vg_lingenfeld/Startseite/"
    # url = "https://www.languageatinternet.org/"
    url = "https://www.xella.com/"

    cdn = CDN(url, False, False, DEFAULT_USER_AGENT, False)
    #cdin.link()
    #cdn.js()
    #cdn.style()
    #cdn.hostame()
    u = cdn.extract_urls_from_css("https://www.afrikanistik-aegyptologie-online.de/portal_css/DiPPThemeNG/ploneStyles5838.css")
    print(u)
    for file in cdn.files:
        print(file)
