import itertools
import re
import functools
from collections.abc import MutableMapping, Iterator

from logger import *

MAX_LRU_CACHE = 128

class ClassList:

    def __init__(self):
        self.__classes = set()

    def add(self, classname):
        assert isinstance(classname, str), "ClassList::add() - classname must be a string"
        self.__classes.add(classname)
        return self

    def contains(self, classname):
        assert isinstance(classname, str), "ClassList::contains() - classname must be a string"
        return classname in self.__classes

    def remove(self, classname):
        assert isinstance(classname, str), "ClassList::remove() - classname must be a string"
        self.__classes.remove(classname)
        return self

    '''
        if classes contain 'classname', removes it
        else adds
    '''
    def toggle(self, classname):
        assert isinstance(classname, str), "ClassList::toggle() - classname must be a string"
        if self.contains(classname):
            self.remove(classname)
        else:
            self.add(classname)


'''
    Just a dict that checks types
    Keys - string
    values - HTMLDomNodes
    Used for quick selection by ID from HTML document
'''
class IdStorage(MutableMapping):

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        assert isinstance(key, str), "IdStorage::set() - key must be a string"
        assert isinstance(value, HTMLDomNode), "IdStorage::set() - value must be a HTMLDomNode"

        if (key in self.store):
            Logger.warning("IdStorage::set() - malformed HTML, id {0} is not unique".format(key))
        self.store[key] = value

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)


'''
    Iterates through passed startElement and its children.
    WARNING: loops only through Elements.
'''
class HTMLDomIterator(Iterator):

    def __init__(self, startElem):
        assert isinstance(startElem, HTMLDomNode), "HTMLDomIterator::__init__() - startElem is not HTMLDomNode"
        self.firstScanned = False
        self.cur = startElem
        self.curIndex = 0
        # stack is a storage of tuples(Element, last index)
        self.stack = []

    def __iter__(self):
        return self

    def __next__(self):
        # extreme case - we need to iterate through first element only once
        if not self.firstScanned:
            self.firstScanned = True
            if(self.cur == None):
                raise StopIteration
            return self.cur
        children = self.cur.children()
        if len(children) != 0:
            self.stack.append((self.cur, self.curIndex + 1))
            self.cur = children[self.curIndex]
            self.curIndex = 0
        else:
            if len(self.stack) != 0:
                self.cur, self.curIndex = self.__popSearch()
        if(self.cur == None):
            raise StopIteration
        return self.cur


    '''
        tries to search for next element, popping from stack and looping through children
        If element is found, returns it, else returns None
    '''
    def __popSearch(self):
        while(len(self.stack) != 0):
            cur, curIndex = self.stack.pop()
            children = cur.children()
            if curIndex >= len(children):
                continue
            # more children available from this element
            self.stack.append((cur, curIndex + 1))
            cur, curIndex = (children[curIndex], 0)

            return (cur, curIndex)
        return (None, None)



'''
    Just a node, not element(comment, etc)
'''
class HTMLDomNode:

    # regular expression for css selectors
    CssIdentifierRe = r'\-?[_a-zA-Z]+[_a-zA-Z0-9-]*'
    CssPrefixRe = r'[.#]'
    QuotedRe = r'(?:"[^"]*?")|(?:\'[^\']*?\')'
    CssAttrRe = r'\[(?P<attrKey>' + CssIdentifierRe + r')((?P<attrAction>[~|^$*]?=)(?P<attrVal>' + QuotedRe + r'))?\]'
    # precomiling this re, because only this regexp is used mostly always
    CssUnitRe = re.compile(r'(?:^|\s+)(?P<asterisk>\*)|(?P<prefix>' + CssPrefixRe + r')?(?P<identifier>' + CssIdentifierRe + r')(?P<attr>' + CssAttrRe + r')?(?:$|\s+)')

    def __init__(self, document, parent=None, tag="", attrs=None, text=""):
        if attrs is None:
            attrs = []
        assert isinstance(document, HTMLDocument) and \
                  isinstance(tag, str) and \
                  isinstance(attrs, list) and \
                  isinstance(text, str), "HTMLDomNode: invalid arg types"
        if parent is not None:
            assert isinstance(parent, HTMLDomNode), "HTMLDomNode: parent must be a HTMLDomNode instance"
        self.__document = document
        self.__parent = parent
        self.__previousElementSibling = None
        self.__previousSibling = None
        self.__nextElementSibling = None
        self.__nextSibling = None
        self.__tag = tag
        self.__attrs = {}
        self.__childNodes = []
        self.__children = []
        self.__classList = ClassList()
        self.__text = text

        self.__makeAttrs(attrs)
        self.__processAttrs()

    def childNodes(self):
        return self.__childNodes

    '''
        returns child ELEMENTS, not only Nodes
        WARNING: may be slow(calculating array in function), but we do not want any before-time optimization
    '''
    def children(self):
        return self.__children

    def classList(self):
        return self.__classList

    def document(self):
        return self.__document

    def firstChild(self):
        if len(self.__childNodes) == 0:
            return None
        return self.__childNodes[0]

    def firstElementChild(self):
        if len(self.__children) == 0:
            return None
        return self.__children[0]

    '''
        WARNING! If 'name' is not a key in attrs dict, returns None
    '''
    def getAttribute(self, name):
        assert isinstance(name, str), "HTMLDomNode::getAttribute() - name must be a string"
        if not(self.hasAttribute(name)):
            return None
        return self.__attrs[name]

    '''
        searches ALL elements with class name 'className', starting from THIS node
        As this operation may be a bit expensive, using lru_cache
    '''
    @functools.lru_cache(MAX_LRU_CACHE)
    def getElementsByClassName(self, className):
        assert isinstance(className, str), "HTMLDomNode::getElementsByClassName() - name must be a string"
        return list(filter(lambda x: x.classList().contains(className), HTMLDomIterator(self)))

    '''
        searches ALL elements with tag name 'tagName', starting from THIS node
        As this operation may be a bit expensive, using lru_cache
    '''
    @functools.lru_cache(MAX_LRU_CACHE)
    def getElementsByTagName(self, tagName):
        assert isinstance(tagName, str), "HTMLDomNode::getElementsByTagName() - name must be a string"
        return list(filter(lambda x: x.tagName() == tagName, HTMLDomIterator(self)))

    def hasAttribute(self, name):
        assert isinstance(name, str), "HTMLDomNode::hasAttribute() - name must be a string"
        return name in self.__attrs

    def lastChild(self):
        if len(self.__childNodes) == 0:
            return None
        return self.__childNodes[-1]

    def lastElementChild(self):
        if len(self.__children) == 0:
            return None
        return self.__children[-1]


    def nextSibling(self):
        return self.__nextSibling

    '''
        returns sibling ELEMENT, not Node
        WARNING: may be slow(calculating in function), but we do not want any before-time optimization
    '''
    def nextElementSibling(self):
        return self.__nextElementSibling

    def parentNode(self):
        return self.__parent

    '''
        returns parent ELEMENT, not Node
        WARNING: may be slow(calculating in function), but we do not want any before-time optimization
    '''
    def parentElement(self):
        curParent = self.parentNode()
        while curParent and not isinstance(curParent, HTMLDomElement):
            curParent = self.parentNode()
        return curParent

    def previousSibling(self):
        return self.__previousSibling

    '''
        returns sibling ELEMENT, not Node
        WARNING: may be slow(calculating in function), but we do not want any before-time optimization
    '''
    def previousElementSibling(self):
        return self.__previousElementSibling

    def querySelector(self, selectors):
        res = self.querySelectorAll(selectors)
        return res[0] if res and len(res) > 0 else None

    @functools.lru_cache(MAX_LRU_CACHE)
    def querySelectorAll(self, selectors):
        # last match elements
        lastMatches = None
        # last match objects
        lastM = None
        for m in HTMLDomNode.CssUnitRe.finditer(selectors):
            newMatches = self.__cssParseSelector(m)
            newMatches = self.__cssParseArgs(m, newMatches)
            if lastMatches:
                # combiner is chars between two selectors
                combiner = selectors[lastM.end(): m.start()].strip()
                #normalizing
                if combiner == '':
                    combiner = ' '
                newMatches = self.__cssCombineMatches(combiner, self.__getIdDictFromList(newMatches), self.__getIdDictFromList(lastMatches))
            lastM = m
            lastMatches = newMatches
        return lastMatches

    '''
        WARNING! Throws if name is not a correct key from 'attrs' dict
    '''
    def setAttribute(self, name, value):
        assert isinstance(name, str), "HTMLDomNode::setAttribute() - name must be a string"
        self.__attrs[name] = value

    def tagName(self):
        return self.__tag

    def text(self):
        return self.__text

    '''
        Helper function for query selector
        Combines two selectors(two groups, new Matches and lastMatches) using combiner
        *Matches is dict as {id(node): node}
    '''
    def __cssCombineMatches(self, combiner, newMatches, lastMatches):
        assert isinstance(newMatches, dict) and isinstance(lastMatches, dict), "HTMLDomNode::__cssCombineMatches() - invalid newMatches or lastMatches, must be a dict"

        # subfunction for ',' combiner
        def updateAndGet(d1, d2):
            d1.update(d2)
            return d1.values()

        actions = {
            ',': lambda: updateAndGet(lastMatches, newMatches),
            ' ': lambda: list(filter(lambda node: True in map(lambda ancestor: id(ancestor) in lastMatches, node.__getAllAncestors()), newMatches.values())),
            '>': lambda: list(filter(lambda node: id(node.parentNode()) in lastMatches , newMatches.values())),
            '+': lambda: list(filter(lambda node: id(node.previousSibling()) in lastMatches, newMatches.values())),
            '~': lambda: list(filter(lambda node: True in map(lambda sibl: id(sibl) in lastMatches, node.__getAllPrevSiblings()), newMatches.values())),
        }
        return actions[combiner]()

    '''
        Helper function for querySelector
        parser attributes in []
    '''
    def __cssParseArgs(self, matchObj, matches):
        if not matchObj['attrKey']:
            return matches
        key = matchObj['attrKey']
        op  = matchObj['attrAction']
        val = matchObj['attrVal']
        # matches [key]
        if not op and not val:
            return list(filter(lambda x: x.hasAttribute(key), matches))
        # unquoting val
        val = val.strip("'\"")
        filters = {
            '='  : lambda x: True if x.getAttribute(key) and x.getAttribute(key) == val else False,
            # contains WORD
            '~=' : lambda x: True if x.getAttribute(key) and val in x.getAttribute(key).split(' ') else False,
            '|=' : lambda x: True if x.getAttribute(key) and x.getAttribute(key).startswith(val) else False,
            '^=' : lambda x: True if x.getAttribute(key) and x.getAttribute(key).startswith(val) else False,
            '$=' : lambda x: True if x.getAttribute(key) and x.getAttribute(key).endswith(val) else False,
            # contains SUBSTRING
            '*=' : lambda x: True if x.getAttribute(key) and val in x.getAttribute(key) else False
        }
        return list(filter(filters[op], matches))

    '''
        Helper function for querySelector.
        Selects needed nodes.
    '''
    def __cssParseSelector(self, matchObj):
        if(matchObj.group('asterisk')):
            return  [self] + self.children()
        # prefix is . or #
        prefix = matchObj.group('prefix')
        identifier = matchObj.group('identifier')
        if not identifier:
            raise ValueError("HTMLDomNode::__parseCss() - invalid Css selector")
        operations = {
            '.': self.getElementsByClassName,
            '#': self.document().getElementById
        }
        if prefix:
            res = operations[prefix](identifier)
            # normalizing result
            if not isinstance(res, list):
                res = [res]
            if len(res) == 1 and res[0] == None:
                res = []
            return res
        return self.getElementsByTagName(identifier)

    def __getAllAncestors(self):
        ancestors = []
        curAncestor = self.parentElement()
        while (curAncestor):
            ancestors.append(curAncestor)
            curAncestor = curAncestor.parentElement()
        return ancestors

    def __getAllPrevSiblings(self):
        siblings = []
        curSibling = self.previousElementSibling()
        while (curSibling):
            siblings.append(curSibling)
            curSibling = curSibling.previousElementSibling()
        return siblings

    def __getIdDictFromList(self, l):
        assert isinstance(l, list), "HTMLDomNode::__getIdDictFromHtmlDomNodeList() - l must be a list"
        return dict(map(lambda x: {id(x), x}, l))

    '''
        Makes from passed list of tuples a dictionary of attributes
    '''
    def __makeAttrs(self, attrs):
        for attr in attrs:
            self.__attrs[attr[0]] = attr[1]

    '''
        Does some operations with attributes.
        For example, splits string value of 'class' attribute to separate values
    '''
    def __processAttrs(self):
        self.__processAttrsClassList()
        self.__processAttrsId()

    '''
        Forming classlist
    '''
    def __processAttrsClassList(self):
        classesStr = self.getAttribute("class")
        if classesStr is None or classesStr == '':
            return
        # spliting by spaces, removing extra spaces, joining
        classList = list(itertools.filterfalse(lambda x: x == '', classesStr.split(' ')))
        for item in classList:
            self.__classList.add(item)

    '''
        Forming ID storage in HTMLDocument
    '''
    def __processAttrsId(self):
        id = self.getAttribute("id")
        if(id is None or id == ''):
            return
        self.document().getIdStorage()[id] = self

    def _setLeftElementSibling(self, sibl):
        assert isinstance(sibl, HTMLDomElement), "HTMLDomNode::_setLeftElementSibling() - sibl is not HTMLDomElement"
        self.__previousElementSibling = sibl

    def _setLeftSibling(self, sibl):
        assert isinstance(sibl, HTMLDomNode), "HTMLDomNode::_setLeftSibling() - sibl is not HTMLDomNode"
        self.__previousSibling = sibl

    def _setRightElementSibling(self, sibl):
        assert isinstance(sibl, HTMLDomElement), "HTMLDomNode::_setRightElementSibling() - sibl is not HTMLDomElement"
        self.__nextElementSibling = sibl

    def _setRightSibling(self, sibl):
        assert isinstance(sibl, HTMLDomNode), "HTMLDomNode::_setRightSibling() - sibl is not HTMLDomNode"
        self.__nextSibling = sibl


class HTMLDomElement(HTMLDomNode):

    def __init__(self, document, parent=None, tag="", attrs=None):
        HTMLDomNode.__init__(self, document, parent, tag, attrs)

    def appendChild(self, child):
        assert isinstance(child, HTMLDomElement) or isinstance(child, HTMLDomNode), "HTMLDomNode: child must be an instance of HTMLDomElement or HTMLDomNode!"
        self.childNodes().append(child)
        if isinstance(child, HTMLDomElement):
            self.children().append(child)



class HTMLDocument(HTMLDomElement):

    def __init__(self):
        HTMLDomNode.__init__(self, self, None, "document", None)
        self.__idStorage = IdStorage()

    def getElementById(self, id):
        if not(id in self.__idStorage):
            return None
        return self.__idStorage[id]

    def getIdStorage(self):
        return self.__idStorage



