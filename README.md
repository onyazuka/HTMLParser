# HTMLParser
HTML parser written in Python

Just a simple HTML DOM parser that implements most of needed functions for convenient working with HTML DOM.

<h2>Usage</h2>
From URL:

```python
  from parser import *
  dom = HTMLDomParser(PARSER_MODE["URL"], "http://my_favourite_web_site.zzz")
  divs = dom.getElementsByTagName("div")
  firstDiv = divs[0]
  firstDivFirstChild = firstDiv.firstElementChild()
  secondDiv = divs[1]
  secondDiv2 = firstDiv.nextElementSibling()

  navs = dom.getElementsByClassName("nav")
  ...
```

Or from string:

```python
  from parser import *
  dom = HTMLDomParser(PARSER_MODE["RAW"], "<html><head>...</head><body>...</body></html>")
```


