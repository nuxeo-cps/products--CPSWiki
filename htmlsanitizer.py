# inspired from Alex Martelli's "Python Cookbook"
# and adapted for wiki use
import sgmllib
import re
from htmlentitydefs import entitydefs

class HTMLSanitizer(sgmllib.SGMLParser):
    """ clean up entered text to avoid
        dangerous tags like forms, style, etc
    """
    white_list = ('a', 'b', 'i', 'strong', 'br', 'p', 'h1', 'h2', 'h3', 'h4',
                  'h5', 'div')

    tolerant_tags = ('br', 'p')

    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
        self.result = []
        self.endTagList = []

    def handle_data(self, data):
        self.result.append(data)

    def handle_charref(self, name):
        self.result.append('&#%s' % name)

    def handle_entyref(self, name):
        x = ';' * self.entitydefs.has_key(name)
        self.result.append('&%s%s' % (name, x))

    def unknown_starttag(self, tag, attrs):
        """ remove unwanted tag, using white list """
        if tag in self.white_list:
            self.result.append('<%s' % tag)
            for k, v in attrs:
                if k[0:2].lower() != 'on' and v[0:10] != 'javascript':
                    self.result.append(' %s="%s"' % (k, v))
            self.result.append('>')
            if tag not in self.tolerant_tags:
                end_tag = '</%s>' % tag
                self.endTagList.insert(0, end_tag)

    def unknown_endtag(self, tag):
        if tag in self.white_list:
            end_tag = '</%s>' % tag
            self.result.append(end_tag)
            if end_tag in self.endTagList:
                self.endTagList.remove(end_tag)

    def cleanup(self):
        """ append mising closing tag """
        self.result.extend(self.endTagList)


def remove_attributes(html, names):
    current = html
    for name in names:
        splitted = re.split(r'(<.*)(%s\s{0,1}\=\s{0,1}".*"\s{0,1})(>)' % name, current, re.I)
        result = []
        for line in splitted:
            if not line.startswith(name):
                result.append(line)
        current = ''.join(result)
    return current

attributes = ('style', 'class', 'accesskey', 'onclick')

def sanitize(html):
    """ cleans html """
    html = remove_attributes(html, attributes)
    parser = HTMLSanitizer()
    parser.feed(html)
    parser.close()
    parser.cleanup()
    return ''.join(parser.result)

