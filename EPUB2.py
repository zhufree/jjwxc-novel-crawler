import requests
from lxml import etree
import sys
import re
import os
import zipfile
import html as html_utils
import uuid
from datetime import datetime, timezone


class epubfile():
    version = '2.0'
    # 创建epub文件格式信息
    author = ''
    title = ''
    description = ''
    TOC = ''
    csstext = ''
    htmlvol = 0

    def create_vol(self, epub, path, index, rollSign):
        nav_info = '''<?xml version="1.0" encoding="utf-8"?>
    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
    <head><title></title>
    <meta charset="utf-8"/>
    <link href="sgc-nav.css" rel="stylesheet" type="text/css"/>
    </head>
    <body>
    <nav epub:type="toc" id="toc" role="doc-toc"><h1>目录</h1>
        <ol>
        '''
        sig = 0
        sigr = 0
        nav_info += '''<li><a href="info.xhtml">''' + self.title + '-' + self.author + '''</a>
    <ol>'''
        for html in sorted(os.listdir(path)):
            basename = os.path.basename(html)
            if basename.endswith('html'):
                if basename != 'C.xhtml' and basename != 'info.xhtml':
                    if sig < len(index) or sigr < len(rollSign):
                        if "vol" in basename:
                            # rollSign[sigr] = re.sub(r'</?\w+[^>]*>', '', rollSign[sigr])
                            nav_info += '''</ol></li>
        <li><a href="''' + basename + '''">
        ''' + rollSign[sigr] + '''</a>
        <ol>'''
                            sigr += 1
                        else:
                            # index[sig] = re.sub(r'</?\w+[^>]*>', '', index[sig])
                            nav_info += '''<li><a href="''' + basename + '''">''' + index[sig] + '''</a></li>
        '''
                            sig += 1
        nav_info += '''</ol></li></ol></nav></body></html>'''
        epub.writestr('OEBPS/nav.xhtml', nav_info, compress_type=zipfile.ZIP_STORED)

    def create_mimetype(self, epub):
        epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)

    def create_container(self, epub):
        container_info = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
</rootfiles></container>'''
        epub.writestr('META-INF/container.xml', container_info, compress_type=zipfile.ZIP_STORED)

    def create_content(self, epub, path):
        opf_ns = 'http://www.idpf.org/2007/opf'
        dc_ns = 'http://purl.org/dc/elements/1.1/'
        package = etree.Element('{' + opf_ns + '}package', nsmap={None: opf_ns},
                                version=self.version, **{'unique-identifier': 'BookId'})
        metadata = etree.SubElement(package, 'metadata', nsmap={'dc': dc_ns})
        etree.SubElement(metadata, '{' + dc_ns + '}identifier', id='BookId').text = 'urn:uuid:' + str(uuid.uuid4())
        etree.SubElement(metadata, '{' + dc_ns + '}title').text = html_utils.unescape(self.title)
        etree.SubElement(metadata, '{' + dc_ns + '}creator').text = html_utils.unescape(self.author)
        etree.SubElement(metadata, '{' + dc_ns + '}language').text = 'zh'
        if self.version == '3.0':
            etree.SubElement(metadata, 'meta', property='dcterms:modified').text = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        manifest = etree.SubElement(package, 'manifest')
        etree.SubElement(manifest, 'item', id='ncx', href='toc.ncx', **{'media-type': 'application/x-dtbncx+xml'})
        etree.SubElement(manifest, 'item', id='css', href='sgc-nav.css', **{'media-type': 'text/css'})
        spine = etree.SubElement(package, 'spine', toc='ncx')
        files = sorted(os.listdir(path))
        if self.version == '3.0' or self.htmlvol:
            attrs = {'properties': 'nav'} if self.version == '3.0' else {}
            etree.SubElement(manifest, 'item', id='nav.xhtml', href='nav.xhtml',
                             **{'media-type': 'application/xhtml+xml', **attrs})
        for filename in files:
            if filename.endswith('.xhtml'):
                etree.SubElement(manifest, 'item', id=filename, href=filename,
                                 **{'media-type': 'application/xhtml+xml'})
                etree.SubElement(spine, 'itemref', idref=filename)
            elif filename.endswith('.jpg'):
                attrs = {'properties': 'cover-image'} if self.version == '3.0' and filename == 'zp.jpg' else {}
                etree.SubElement(manifest, 'item', id=filename, href=filename,
                                 **{'media-type': 'image/jpeg', **attrs})
        if self.version == '3.0' or self.htmlvol:
            spine.insert(2 if 'C.xhtml' in files else 1, etree.Element('itemref', idref='nav.xhtml'))
        if 'zp.jpg' in files:
            etree.SubElement(metadata, 'meta', name='cover', content='zp.jpg')
        if self.version == '2.0' and 'C.xhtml' in files:
            guide = etree.SubElement(package, 'guide')
            etree.SubElement(guide, 'reference', type='cover', title='Cover', href='C.xhtml')
        epub.writestr('OEBPS/content.opf', etree.tostring(package, encoding='utf-8', xml_declaration=True),
                      compress_type=zipfile.ZIP_DEFLATED)

    def create_info(self, epub, path, index, rollSign):
        tox_info = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
<head><meta name="dtb:uid" content="" />
<meta name="dtb:depth" content="2" />
<meta name="dtb:totalPageCount" content="0" />
<meta name="dtb:maxPageNumber" content="0" />
</head><docTitle><text>''' + self.title + '''</text></docTitle><navMap>'''
        sig = 0
        sigr = 0
        count = 1
        tox_info += '''<navPoint id="0" playOrder="0">
            <navLabel><text>''' + self.title + '-' + self.author + '''</text></navLabel><content src="info.xhtml"/>'''
        for html in sorted(os.listdir(path)):
            basename = os.path.basename(html)
            if basename.endswith('html'):
                if basename != 'C.xhtml' and basename != 'info.xhtml':
                    iii = 0
                    if sig < len(index) or sigr < len(rollSign):
                        if "vol" in basename:
                            rollSign[sigr] = re.sub(r'</?\w+[^>]*>', '', rollSign[sigr])
                            tox_info += '''</navPoint><navPoint id="''' + str(count) + '''" playOrder="''' + str(
                                count) + '''">
                <navLabel><text>''' + rollSign[sigr] + '''</text></navLabel><content src="''' + basename + '''"/>'''
                            sigr += 1
                            count += 1
                        else:
                            index[sig] = re.sub(r'</?\w+[^>]*>', '', index[sig])
                            tox_info += '''<navPoint id="''' + str(count) + '''" playOrder="''' + str(count) + '''">
                                            <navLabel><text>''' + index[
                                sig] + '''</text></navLabel><content src="''' + basename + '''"/></navPoint>'''
                            sig += 1
                            count += 1
        tox_info += '''</navPoint></navMap></ncx>'''
        epub.writestr('OEBPS/toc.ncx', tox_info, compress_type=zipfile.ZIP_STORED)

    def create_stylesheet(self, epub):
        css_info = self.csstext
        epub.writestr('OEBPS/sgc-nav.css', css_info, compress_type=zipfile.ZIP_STORED)

    def createEpub(self, epub, xaut, xtitle, ti, index, rollSign, path):
        self.author = html_utils.escape(xaut)
        self.title = html_utils.escape(xtitle)
        self.create_mimetype(epub)
        self.create_container(epub)
        ppp = os.path.abspath(os.path.join(path, ti))
        if self.htmlvol:
            self.create_vol(epub, ppp, index, rollSign)
        self.create_content(epub, ppp)
        self.create_info(epub, ppp, index, rollSign)
        self.create_stylesheet(epub)
        for html in sorted(os.listdir(ppp)):
            basename = os.path.basename(html)
            if basename.endswith('jpg'):
                epub.write(os.path.join(ppp, basename), "OEBPS/" + basename, compress_type=zipfile.ZIP_DEFLATED)
            if basename.endswith('html'):
                epub.write(os.path.join(ppp, basename), "OEBPS/" + basename, compress_type=zipfile.ZIP_DEFLATED)
