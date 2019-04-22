import unittest
from parser import *

HTML = '''<!DOCTYPE HTML>
<html>

<head>
  <meta charset="utf-8">
  <link href="tree.css" rel="stylesheet">
  <script src="tree.js"></script>
</head>

<body>

  <ul class="tree" id="tree">
    <li class="list animals_list">Animals
      <ul>
        <li>Mammals
          <ul>
            <li>Cows</li>
            <li id="donkeys" name="Saru">Donkeys</li>
            <li name="Wantuz" legs="4">Dogs</li>
            <li>Tigers</li>
          </ul>
        </li>
        <li>Other
          <ul class="list   other_list">
            <li>Snakes</li>
            <li>Birds</li>
            <li>Lizards</li>
          </ul>
        </li>
      </ul>
    </li>
    <li class="list fishes_list">Fishes
      <ul>
        <li>Aquarium
          <ul>
            <li>Guppy</li>
            <li>Angelfish</li>
          </ul>
        </li>
        <li>Sea
          <ul>
            <li>Sea trout</li>
          </ul>
        </li>
      </ul>
    </li>
  </ul>

</body>

</html>'''


class TestHTMLDomParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        TestHTMLDomParser.document = HTMLDomParser(PARSER_MODE["RAW"], HTML).getDocument()


    def testGetElementById(self):
        doc = TestHTMLDomParser.document

        tree = doc.getElementById("tree")
        self.assertTrue(isinstance(tree, HTMLDomNode))

        donkeys = doc.getElementById("donkeys")
        self.assertTrue(isinstance(donkeys, HTMLDomNode))

        guppy = doc.getElementById("guppy")
        self.assertFalse(isinstance(guppy, HTMLDomNode))


    def testGetElementsByTagName(self):
        doc = TestHTMLDomParser.document

        uls = doc.getElementsByTagName("ul")
        self.assertEqual(len(uls), 7)

        lis = doc.getElementsByTagName("li")
        self.assertEqual(len(lis), 16)

        bodies = doc.getElementsByTagName("body")
        self.assertEqual(len(bodies), 1)

        divs = doc.getElementsByTagName("div")
        self.assertEqual(len(divs), 0)


    def testGetElementsByClassName(self):
        doc = TestHTMLDomParser.document

        lists = doc.getElementsByClassName("list")
        self.assertEqual(len(lists), 3)

        fishlists = doc.getElementsByClassName("fishes_list")
        self.assertEqual(len(fishlists), 1)

        nekolists = doc.getElementsByClassName("neko_list")
        self.assertEqual(len(nekolists), 0)


    def testChildNodesAndChildren(self):
        doc = TestHTMLDomParser.document
        donkeys = doc.getElementById("donkeys")
        self.assertEqual(len(donkeys.childNodes()), 1)
        self.assertEqual(len(donkeys.children()), 0)

        otherList = doc.getElementsByClassName("other_list")[0]
        self.assertEqual(len(otherList.childNodes()), 3)
        self.assertEqual(len(otherList.children()), 3)

    def testFirstLastChild(self):
        doc = TestHTMLDomParser.document
        self.assertEqual(doc.firstChild().tagName(), "html")
        self.assertEqual(doc.lastChild().tagName(), "html")
        self.assertEqual(doc.firstElementChild().tagName(), "html")
        self.assertEqual(doc.lastElementChild().tagName(), "html")

        aquariumUl = doc.getElementsByClassName("fishes_list")[0].firstElementChild().firstElementChild().firstElementChild()
        self.assertEqual(aquariumUl.firstElementChild().firstChild().text(), "Guppy")
        self.assertEqual(aquariumUl.lastElementChild().firstChild().text(), "Angelfish")

    def testNextPrevSibling(self):
        doc = TestHTMLDomParser.document

        donkeys = doc.getElementById("donkeys")
        self.assertEqual(donkeys.nextElementSibling().firstChild().text(), "Dogs")
        self.assertEqual(donkeys.previousElementSibling().firstChild().text(), "Cows")
        self.assertEqual(donkeys.nextSibling().firstChild().text(), "Dogs")
        self.assertEqual(donkeys.previousSibling().firstChild().text(), "Cows")

    def testGetAttribute(self):
        doc = TestHTMLDomParser.document

        donkeys = doc.getElementById("donkeys")
        self.assertEqual(donkeys.getAttribute("name"), "Saru")
        dogs = donkeys.nextElementSibling()
        self.assertEqual(dogs.getAttribute("name"), "Wantuz")
        self.assertEqual(dogs.getAttribute("legs"), "4")
        self.assertEqual(dogs.getAttribute("hands"), None)

if __name__ == '__main__':
    unittest.main()