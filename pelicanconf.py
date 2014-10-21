#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'GoDataDriven'
SITENAME = u'GoDataDrivenBlog'
SITEURL = ''

TIMEZONE = 'Europe/Amsterdam'
DEFAULT_LANG = u'en'
DATE_FORMAT = { 'en': '%B %d, %Y' }
DEFAULT_DATE_FORMAT = '%B %d, %Y'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None

# Blogroll
SECTIONS = [
    ('about', 'pages/about-go-data-driven.html'),
    ('rss', 'feeds/rss.xml')
]

DEFAULT_PAGINATION = 5

# Uncomment following line if you want document-relative URLs when developing
RELATIVE_URLS = True

THEME = 'godatadriven-template'

STATIC_PATHS = ["images", "resources"]
OUTPUT_PATH = 'output'
FILES_TO_COPY = []

MD_EXTENSIONS = ['codehilite(css_class=codehilite)','extra']

DIRECT_TEMPLATES = ('blog',)
PAGINATED_DIRECT_TEMPLATES = ('blog',)
BLOG_SAVE_AS = 'index.html'

FEED_DOMAIN = 'http://blog.godatadriven.com'

FEED_ATOM = None
FEED_RSS = None
FEED_ALL_ATOM = 'feeds/atom.xml'
FEED_ALL_RSS = 'feeds/rss.xml'
CATEGORY_FEED_ATOM = None
CATEGORY_FEED_RSS = None
TAG_FEED_ATOM = None
TAG_FEED_RSS = None

DELETE_OUTPUT_DIRECTORY = True

OFFICE_ADDRESS = "Utrechtseweg 49, Hilversum, The Netherlands"
OFFICE_PHONE = "+31 (0)35 672 9069"
OFFICE_EMAIL = "signal@godatadriven.com"

GA_UA = 'UA-40578233-4'
GA_DOMAIN = 'blog.godatadriven.com'

PLUGIN_PATH = "plugins"
PLUGINS = ["latex"]
LATEX = 'article'
