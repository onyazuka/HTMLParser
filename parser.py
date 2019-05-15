import urllib.request as urlreq
from html.parser import HTMLParser
import http.client
from urllib.parse import urlparse
from dom import *

class UrlReader:

    @staticmethod
    def createConnection(host):
        conn = http.client.HTTPSConnection(host, 443)
        return conn

    @staticmethod
    def getFromConnection(connection, url):
        assert isinstance(connection, http.client.HTTPConnection), 'UrlReader::getFromConnection() - invalid connection passed'
        #making relative url from passed absolute url
        urlParts = urlparse(url)
        relUrl = url.replace(urlParts.scheme, "").replace(urlParts.netloc, "")[3:]
        connection.request("GET", relUrl, headers={
            "Connection" : "Keep-Alive"
        })
        resp = connection.getresponse()
        return resp.read().decode('utf-8')

    @staticmethod
    def getUrlContentsAsUtf8(url):
        return urlreq.urlopen(url).read().decode('utf-8')



PARSER_MODE = {
    "RAW": 0,
    "URL": 1
}


class HTMLDomParser(HTMLParser):

    '''
    tags, that are always empty
    we need to do push and pop in tag start as we see them(if they are not self-closing)
    '''
    EMPTY_TAGS = [
        "area",
        "base",
        "basefont",
        "br",
        "col",
        "frame",
        "hr",
        "img",
        "input",
        "isindex",
        "link",
        "meta",
        "param",
    ]

    def __init__(self, mode, content, connection=None):

        assert mode in PARSER_MODE.values(), \
               "HTMLDomParser mode invalid"
        HTMLParser.__init__(self)
        rawHtml = content if mode == PARSER_MODE["RAW"] else self._fromUrl(content, connection)
        # stack[0] is always a document element
        self.stack = []
        self.stack.append(HTMLDocument())
        self.feed(rawHtml)
        self._siblingify(self.getDocument())

    def getDocument(self):
        assert len(self.stack) > 0, "HTMLDomParser: invalid DOM, stack is empty"
        return self.stack[0]

    def handle_starttag(self, tag, attrs):
        newElem = HTMLDomElement(self.getDocument(), self.stack[-1], tag, attrs)
        self.stack[-1].appendChild(newElem)
        self.stack.append(newElem)
        if(tag in HTMLDomParser.EMPTY_TAGS):
            self.handle_endtag(tag)

    def handle_startendtag(self, tag, attrs):
        self.stack.append(HTMLDomElement(self.getDocument(), self.stack[-1], tag, attrs))
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        self.stack.pop()

    def handle_data(self, data):
        # stripping whitespaces, tabulation, new line chars
        strippedData = data.strip("\n\t ")
        # nothing to do here
        if(len(strippedData) == 0):
            return
        if(len(self.stack) > 0):
            self.stack[-1].appendChild(HTMLDomNode(self.getDocument(), parent=self.stack[-1], text=strippedData))

    '''
        Two modes supported: with alive connection and without it.
        Connection is instance of HTTPConnection
    '''
    def _fromUrl(self, url, connection=None):
        if connection is None:
            rawHtml = UrlReader.getUrlContentsAsUtf8(url)
        else:
            assert isinstance(connection, http.client.HTTPConnection), 'HTMLDomParser::_fromUrl() - invalid connection passed'
            rawHtml = UrlReader.getFromConnection(connection, url)
        return rawHtml

    '''
        Must be called when tree is completed.
        Recursively makes double linked lists from one-level siblings.
    '''
    def _siblingify(self, startElem):
        assert isinstance(startElem, HTMLDomNode), "HTMLDomParser::_siblingify() - 'startElem' is not HTMLDomNode"
        children = startElem.childNodes()
        for i in range(0, len(children)):
            if i != 0:
                children[i]._setLeftSibling(children[i-1])
            self._siblingify(children[i])
            if i != (len(children) - 1):
                children[i]._setRightSibling(children[i+1])

