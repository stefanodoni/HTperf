from HTMLParser import HTMLParser
import sys
import os

__author__ = 'francesco'

if len(sys.argv) < 2:
    print("Need csv file param!")
    sys.exit()

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        print "Encountered a start tag:", tag
    def handle_endtag(self, tag):
        print "Encountered an end tag :", tag
    def handle_data(self, data):
        print "Encountered some data  :", data

# instantiate parser
parser = MyHTMLParser()
rootdir = sys.argv[1]

for subdir, dirs, files in os.walk(rootdir):
    dirs.sort()
    i = 0
    for file in files:
        if file.endswith(".html"):
            print(i, os.path.join(subdir, file))
            i = i +1
            #f = open(os.path.join(subdir, file), 'r').read()
            # feed parser with file
            #parser.feed(f)