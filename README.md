# HTMLParser
HTML parser written in Python

It implements most of needed functions for convenient working with HTML DOM.

## Features
- Parsing from string or from URL(with or without connection);
- All DOM readonly functions;
- CSS query selectors;

## Warnings
When using querySelect, please keep in mind some differences from native CSS selectors:
- when using selectors like querySelectorAll("input[type='text']"), attribute value should always be quoted;
- when using complex selectors like querySelectorAll("div > li > div"), there should be at least one space between each selector and operator.

## Usage
From URL:

```python
  from parser import *
  dom = HTMLDomParser(PARSER_MODE["URL"], "http://my_favourite_web_site.zzz")
  doc = dom.getDocument()
  divs = doc.getElementsByTagName("div")
  firstDiv = divs[0]
  firstDivFirstChild = firstDiv.firstElementChild()
  secondDiv = divs[1]
  secondDiv2 = firstDiv.nextElementSibling()

  navs = doc.getElementsByClassName("nav")

  classyDivs = doc.querySelectorAll("div[class]")
  divLiDiv = doc.querySelectorAll("div > li > div")

  ...
```

Or from string:

```python
  from parser import *
  dom = HTMLDomParser(PARSER_MODE["RAW"], "<html><head>...</head><body>...</body></html>")
```


