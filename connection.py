import urllib.request as urlreq
from urllib.parse import urlparse
import http.client

class Connection:

    HTTP_PORT = 80
    HTTPS_PORT = 443

    def __init__(self, host):
        self.connection = http.client.HTTPSConnection(host, Connection.HTTPS_PORT)

    def getFromConnection(self, url):
        #making relative url from passed absolute url
        urlParts = urlparse(url)
        relUrl = url.replace(urlParts.scheme, "").replace(urlParts.netloc, "")[3:]
        self.connection.request("GET", relUrl, headers={
            "Connection" : "Keep-Alive"
        })
        resp = self.connection.getresponse()
        return resp.read().decode('utf-8')

    @staticmethod
    def getUrlContentsAsUtf8(url):
        return urlreq.urlopen(url).read().decode('utf-8')
