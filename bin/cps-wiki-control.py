#! /usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2005 Laurent Pelecq <laurent.pelecq@soleil.org>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.

import sys, os
import optparse

import string, re

import urlparse
import urllib
import urllib2
import cookielib
import httplib # For error codes only
import HTMLParser

### Version

version = "1.0"

### Functions

def warn(msg):
    sys.stderr.write(msg)

def die(msg, status=1):
    warn(msg)
    sys.exit(status)

def noop(msg):
    pass

### Parsing command line

usage="""%prog [OPTIONS] ARGS

Possible commands are:

  create WIKI_URL PAGE_NAME [INPUT_FILE]
  create WIKI_URL PAGES_DIR
     Create pages. If pages already exist, an error is reported.

  modify WIKI_URL PAGE_NAME INPUT_FILE
  modify WIKI_URL PAGES_DIR
     Modify pages. If pages doesn't exist, they are created.

  delete WIKI_URL PAGE_NAME ...

  fetch  WIKI_URL PAGE_NAME [OUTPUT_FILE]
     Fetch a single wiki page.

  fetch  WIKI_URL PAGE_NAME DEST_DIR
     Recursively retrieves wiki pages.

Manipulate wiki pages. When command takes a directory as argument, all
files in that directory are considered as pages. Their names must be
equal to the corresponding page name.
"""

option_parser = optparse.OptionParser(usage=usage,
                                      version="%%prog %s"%(version))

option_parser.add_option("-C", "--cookie-file",
                         dest="cookie_file", action="store", default=None,
                         help="cookie file to share between calls.")

option_parser.add_option("--debug",
                         dest="debug", action="store_true", default=False,
                         help="debug mode, for developers only")

option_parser.add_option("--trace",
                         dest="trace", action="store_true", default=False,
                         help="trace mode, for developers only")

option_parser.add_option("-v", "--verbose",
                         dest="verbose", action="store_true", default=False,
                         help="print status messages to stdout")

option_parser.add_option("-n", "--no-act",
                         dest="no_act", action="store_true", default=False,
                         help="print what would be done without"
                         " executing anything")

option_parser.add_option("-u", "--http-user",
                         dest="http_user", action="store", default=None,
                         metavar="USER", help="user name for authentification")

option_parser.add_option("-p", "--http-password",
                         dest="http_password", action="store", default=None,
                         metavar="PW",
                         help="password for authentification (UNSAFE)")

try:
    options, args = option_parser.parse_args()
except optparse.OptionError:
    die('Error: %s\n'%(sys.exc_info()[1]))

verbose = noop
if options.verbose:
    verbose = warn

### HTTP

if options.trace:
    import logging
    logging.basicConfig(level=logging.DEBUG)

def log(title, *msgs):
    if options.trace:
        remaining = 50 - len(title)
        print '== %s %-.*s'%(title, remaining, '='*40)
        for msg in msgs:
            print msg

def log_request(title, request, *extra_args):
    args = [ title, 'Type: %s'%(request.type) ]
    if request.host:
        if request.port:
            args.append('Host: %s:%s'%(request.host, request.port))
        else:
            args.append('Host: %s'%(request.host))
    if request.data:
        args.append('Data: %s'%(request.data))
    headers = request.header_items()
    if headers:
        args.append('Headers:')
        for hname, hval in headers:
            args.append('  %s: %s'%(hname, hval))
    apply(log, tuple(args) + extra_args)

def log_response(title, response):
    log('%s (%s)'%(title, response.msg), str(response.info()))

def log_cookie(title, cookie):
    if (len(cookie) > 0):
        log(title, str(cookie))
    else:
        log(title, 'No cookies')


class HTTPCookieProcessor(urllib2.HTTPCookieProcessor):

    def __init__(self, cookiejar=None):
        urllib2.HTTPCookieProcessor.__init__(self, cookiejar)

    def http_request(self, request):
        req = urllib2.HTTPCookieProcessor.http_request(self, request)
        log_request('Cookie request', req)
        log_cookie('Cookie', self.cookiejar)
        return req

    def http_response(self, request, response):
        resp = urllib2.HTTPCookieProcessor.http_response(self, request, response)
        log_request('Cookie request', request)
        log_response('Cookie response', resp or response)
        log_cookie('Cookie', self.cookiejar)
        return resp

    https_request = http_request
    https_response = http_response


class HTTPHandler(urllib2.HTTPHandler):

    def http_open(self, request):
        log_request('HTTP open', request)
        resp = urllib2.HTTPHandler.http_open(self, request)
        log_response('HTTP open', resp)
        return resp

    def http_request(self, request):
        req = urllib2.HTTPHandler.http_request(self, request)
        log_request('HTTP request', req or request)
        return req


class HTTPErrorProcessor(urllib2.HTTPErrorProcessor):

    def http_response(self, request, response):
        log_response('HTTP Response', response)
        return urllib2.HTTPErrorProcessor.http_response(self, request, response)

    https_response = http_response


class HTTPRedirectHandler(urllib2.HTTPRedirectHandler):

    """Redirect handler that can handle URL with parameters."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        (scheme, netloc, base_url, params, query,
         fragment) = urlparse.urlparse(newurl)
        if query:
            newurl = urlparse.urlunparse((scheme, netloc, base_url,
                                          params, None, fragment))
        newreq = urllib2.HTTPRedirectHandler.redirect_request(self, req, fp,
                                                              code, msg,
                                                              headers, newurl)
        if query:
            newreq.add_data(query)
        log_request('Redirect request', newreq, 'New URL: %s'%(newurl))
        return newreq

### HTTP

class WikiLinkList(list):

    """List that finds wiki links in text."""

    U = 'A-Z\xc0-\xdf'
    L = 'a-z\xe0-\xff'
    b = '(?<![%s0-9])' % (U+L)
    bracketedexpr = r'\[([^\n\]]+)\]'
    wikiname1 = r'(?L)%s[%s]+[%s]+[%s][%s]*[0-9]*' % (b,U,L,U,U+L)
    wikiname2 = r'(?L)%s[%s][%s]+[%s][%s]*[0-9]*'  % (b,U,U,L,U+L)
    wikilink  = r'(?:%s|%s|%s)' % (wikiname1,wikiname2,bracketedexpr)
    wikilink_re = re.compile(wikilink)

    def __call__(self, line):
        """Apply a function to all wiki link in a line."""

    def findall(self, s):
        for m in self.wikilink_re.finditer(s):
            self.append(m.group(1) or m.group(0))


class HTMLParserError(Exception):
    pass


class HTMLTextareaParser(HTMLParser.HTMLParser):

    """Parse HTML page that is assumed to contain only one textarea and
    record the text inside."""

    entity = { 'lt': '<', 'gt': '>', 'amp': '&' }

    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.text = ''
        self.in_textarea = False

    def handle_starttag(self, tag, attrs):
        if tag == 'textarea':
            self.in_textarea = True

    def handle_endtag(self, tag):
        if tag == 'textarea':
            self.in_textarea = False

    def handle_data(self, data):
        if self.in_textarea:
            self.text += data

    def handle_entityref(self, name):
        if self.in_textarea:
            if name in self.entity:
                self.text += self.entity[name]
            else:
                raise HTMLParserError("unknown entity: %s"%(name))

    def handle_charref(self, name):
        if self.in_textarea:
            try:
                self.text += chr(int(name, 16))
            except:
                raise HTMLParserError("invalid char ref: %s"%(name))

### Main

class HttpRequester:

    headers = { 'User-agent' : 'Mozilla/5.0 (compatible)' }

    def __init__(self, cookiejar=None):
        cookie_proc = HTTPCookieProcessor(cookiejar)
        redirect_handler = HTTPRedirectHandler()
        self.opener = urllib2.build_opener(redirect_handler, cookie_proc)
        self.data = None
        self.resp_url = None

    def __call__(self, url, **query):
        data = None
        verbose("Request: %s\n"%(url))
        if query:
            data = urllib.urlencode(query)
        try:
            req = urllib2.Request(url, data=data, headers=self.headers)
            resp = self.opener.open(req)
            self.resp_url = resp.url
            self.data = resp.read()
        except urllib2.HTTPError, ex:
            verbose("Status: %s\n"%(ex))
            return ex.code
        verbose("Status: OK\n")
        return httplib.OK


class WikiControl:

    """Create, modify, delete and fetch Wiki pages."""

    latin1 = urllib.unquote("%22%27/%5C%3A%3B%20%26%C0%C1%C2%C3%C4%C5%C7"
                            "%C8%C9%CA%CB%CC%CD%CE%CF%D1%D2%D3%D4%D5%D6%D8"
                            "%D9%DA%DB%DC%DD%E0%E1%E2%E3%E4%E5%E7%E8%E9%EA"
                            "%EB%EC%ED%EE%EF%F1%F2%F3%F4%F5%F6%F8%F9%FA%FB"
                            "%FC%FD%FF")

    ascii = "--------AAAAAACEEEEIIIINOOOOOOUUUUYaaaaaaceeeeiiiinoooooouuuuyy"

    SAFE_CHARS_TRANSLATIONS = string.maketrans(latin1, ascii)

    max_chars = 24

    def __init__(self, wiki_url, cookie_file=None):
        self.wiki_url = wiki_url
        cookiejar = None
        if cookie_file:
            cookiejar = cookielib.LWPCookieJar(cookie_file)
            if os.path.isfile(cookie_file):
                verbose('Loading cookies from %s\n'%(cookie_file))
                cookiejar.load()
        self.cookiejar = cookiejar
        self.request = HttpRequester(cookiejar)

    def close(self):
        if self.cookiejar:
            self.cookiejar.save()

    def authentificate(self, http_user, http_password=None):
        """Fill the site authentification form."""
        if not http_password:
            import getpass
            http_password = getpass.getpass("Password for %s: "%(http_user))
        login_url = self.join_url(self.wiki_url, 'login_form')
        status = self.request(login_url)
        if status == httplib.OK:
            login_url = self.request.resp_url
            scheme = urlparse.urlparse(login_url)[0]
            self.wiki_url = self.replace_url_scheme(scheme, self.wiki_url)
            status = self.request(login_url, __ac_name=http_user,
                                  __ac_password=http_password,
                                  __ac_persistent=0)
            if status != httplib.OK:
                raise Exception("%s: authentification failed"%(http_user))

    def check_response(self):
        if self.request.resp_url:
            path = urlparse.urlparse(self.request.resp_url)[2]
            if path.endswith('/login_form'):
                raise Exception('authentification required')

    def replace_url_scheme(self, scheme, url):
        """Replace URL scheme, ex: http -> https."""
        new_url = (scheme,) + urlparse.urlparse(url)[1:]
        return urlparse.urlunparse(new_url)

    def join_url(self, base_url, *rel_urls):
        return "%s/%s"%(base_url, "/".join(rel_urls))

    def page_url(self, page_name):
        id = page_name.translate(self.SAFE_CHARS_TRANSLATIONS)
        return self.join_url(self.wiki_url, id[:self.max_chars])

    def read_file(self, input_file):
        """Read a file and return the content."""
        text = ''
        fd = file(input_file)
        try:
            text = fd.read()
        finally:
            fd.close()
        return text

    def write_file(self, output_file, text):
        """Write text in file.

        If an error occurs, the file is deleted."""
        outfd = file(output_file, "w")
        try:
            try:
                outfd.write(text)
            finally:
                outfd.close()
        except:
            os.unlink(output_file)
            raise

    def edit_content(self, page_url, content):
        """Change the page content."""
        edit_url = self.join_url(page_url, "edit")
        return self.request(edit_url, source=content)

    def __create_page(self, page_name, page_url, input_file):
        """Create a page.

        The caller is responsible for checking that the page doesn't
        exists."""
        create_url = self.join_url(self.wiki_url, "addPage")
        status = self.request(create_url, title=page_name)
        self.check_response()

        content = ''
        if input_file:
            content = self.read_file(input_file)

        if self.edit_content(page_url, content) != httplib.OK:
            raise Exception("%s: creation failed"%(page_name))

    def create_page(self, page_name, input_file=None):
        """Create a page.

        If no input file is provided, the page is empty."""
        page_url = self.page_url(page_name)

        status = self.request(page_url)

        if status != httplib.NOT_FOUND:
            raise Exception("%s: page exists"%(page_name))

        self.__create_page(page_name, page_url, input_file)

    def modify_page(self, page_name, input_file):
        """Modify a page by copying the input file content.

        If the page doesn't exist, it is created."""
        page_url = self.page_url(page_name)

        status = self.request(page_url)

        if status != httplib.OK:
            self.__create_page(page_name, page_url, input_file)
        else:
            content = self.read_file(input_file)

            if self.edit_content(page_url, content) != httplib.OK:
                raise Exception("%s: modification failed"%(page_name))
            self.check_response()

    def delete_page(self, page_name):
        """Delete a page."""
        page_url = self.page_url(page_name)
        delete_url = self.join_url(page_url, "delete")
        status = self.request(delete_url)
        self.check_response()

        if status == httplib.NOT_FOUND:
            raise Exception("%s: page doesn't exists"%(page_name))

    def fetch_page(self, page_name, output_file=None):
        """Fetch page content and return it as text.

        Content can also be saved in an output file."""
        page_url = self.page_url(page_name)
        edit_url = self.join_url(page_url, "cps_wiki_pageedit")
        status = self.request(edit_url)
        self.check_response()

        if status == httplib.NOT_FOUND:
            raise Exception("%s: page doesn't exists"%(page_name))

        html_parser = HTMLTextareaParser()
        html_parser.feed(self.request.data)
        html_parser.close()

        if output_file:
            self.write_file(output_file, html_parser.text)

        return html_parser.text

    def fetch_wiki(self, front_page_name, dest_dir):
        """Recursively fetch all pages.

        Attachements are not saved."""
        pages = WikiLinkList([ front_page_name ])
        downloaded = {}
        while pages:
            page_name = pages.pop()
            if page_name in downloaded:
                continue
            output_file = os.path.join(dest_dir, page_name)
            try:
                text = self.fetch_page(page_name, output_file)
                downloaded[page_name] = True
                pages.findall(text)
            except Exception, ex:
                warn("Error: %s\n"%(ex))


def get_pages_list(args, allow_empty_content=False):
    """Parse arguments to build the list of pages.

    It returns a dictionary with keys the page names and with value
    corresponding file names."""
    nargs = len(args)
    result = {}
    if nargs == 2:
        result[args[0]] = args[1]
    elif nargs != 1:
        raise Exception("invalid number of arguments")
    elif os.path.isdir(args[0]):
        dir = args[0]
        for page_name in os.listdir(dir):
            result[page_name] = os.path.join(dir, page_name)
    elif allow_empty_content:
        result[args[0]] = None
    else:
        raise Exception("invalid arguments")
    return result


def main(args, options):

    try:
        if len(args) < 2:
            raise Exception("invalid number of arguments")

        action, wiki_url = tuple(args[0:2])

        args = args[2:]

        control = WikiControl(wiki_url, options.cookie_file)

        if options.http_user:
            control.authentificate(options.http_user, options.http_password)

        if action == 'create':
            pages = get_pages_list(args, True)
            for page_name in pages:
                control.create_page(page_name, pages[page_name])
        elif action == 'modify':
            pages = get_pages_list(args)
            for page_name in pages:
                control.modify_page(page_name, pages[page_name])
        elif action == 'delete':
            for page_name in args:
                control.delete_page(page_name)
        elif action == 'fetch':
            page_name = args.pop(0)
            if not args:
                print control.fetch_page(page_name)
            elif len(args) > 1:
                raise Exception("invalid number of arguments")
            elif os.path.isdir(args[0]):
                control.fetch_wiki(page_name, args[0])
            else:
                control.fetch_page(page_name, args[0])

        control.close()
    except:
        if options.debug:
            import traceback
            traceback.print_exc()
        else:
            warn('Error: %s\n'%(sys.exc_info()[1]))
        return 1

    return 0


exit_code = main(args, options)

sys.exit(exit_code)

#  Local Variables: ***
#  mode: python ***
#  End: ***
