"""Script to generate binary fixture files (PDF, EPUB, DOCX) for tests.
Run once: python tests/fixtures/create_fixtures.py
"""
import os
import io
import zipfile
from pathlib import Path

FIXTURES = Path(__file__).parent


def create_sample_pdf():
    """Create a minimal 2-page PDF using raw PDF syntax."""
    # Minimal valid PDF with 2 pages of text
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj

2 0 obj
<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>
endobj

3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 5 0 R /Resources << /Font << /F1 6 0 R >> >> >>
endobj

4 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 7 0 R /Resources << /Font << /F1 6 0 R >> >> >>
endobj

5 0 obj
<< /Length 120 >>
stream
BT
/F1 12 Tf
72 720 Td
(Clean Code - Chapter 1: Meaningful Names) Tj
0 -20 Td
(Names should reveal intent and be easy to pronounce.) Tj
ET
endstream
endobj

6 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj

7 0 obj
<< /Length 110 >>
stream
BT
/F1 12 Tf
72 720 Td
(Clean Code - Chapter 2: Functions) Tj
0 -20 Td
(Functions should do one thing and do it well.) Tj
ET
endstream
endobj

xref
0 8
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000417 00000 n
0000000589 00000 n
0000000658 00000 n

trailer
<< /Size 8 /Root 1 0 R >>
startxref
820
%%EOF"""
    (FIXTURES / "sample.pdf").write_bytes(pdf_content)
    print("Created sample.pdf")


def create_scanned_mock_pdf():
    """Create a PDF where all pages have near-empty text (simulates scanned PDF)."""
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj

2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj

3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj

4 0 obj
<< /Length 10 >>
stream
BT ET
endstream
endobj

5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj

xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000244 00000 n
0000000306 00000 n

trailer
<< /Size 6 /Root 1 0 R >>
startxref
381
%%EOF"""
    (FIXTURES / "scanned_mock.pdf").write_bytes(pdf_content)
    print("Created scanned_mock.pdf")


def create_sample_epub():
    """Create a minimal valid EPUB file."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        # mimetype must be first and uncompressed
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip")

        z.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")

        z.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Sample Book</dc:title>
    <dc:identifier id="uid">sample-001</dc:identifier>
  </metadata>
  <manifest>
    <item id="ch1" href="chapter1.html" media-type="application/xhtml+xml"/>
    <item id="ch2" href="chapter2.html" media-type="application/xhtml+xml"/>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="ch1"/>
    <itemref idref="ch2"/>
  </spine>
</package>""")

        z.writestr("OEBPS/chapter1.html", """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body>
  <h1>Chapter 1: Introduction</h1>
  <p>This is the introduction to our sample book about clean code practices.</p>
  <p>Writing clean code is essential for maintaining large software systems.</p>
</body>
</html>""")

        z.writestr("OEBPS/chapter2.html", """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 2</title></head>
<body>
  <h2>Chapter 2: Functions</h2>
  <p>Functions should do one thing and do it well.</p>
  <p>Keep functions small and focused on a single responsibility.</p>
</body>
</html>""")

        z.writestr("OEBPS/toc.ncx", """<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head><meta name="dtb:uid" content="sample-001"/></head>
  <docTitle><text>Sample Book</text></docTitle>
  <navMap>
    <navPoint id="ch1" playOrder="1">
      <navLabel><text>Chapter 1</text></navLabel>
      <content src="chapter1.html"/>
    </navPoint>
    <navPoint id="ch2" playOrder="2">
      <navLabel><text>Chapter 2</text></navLabel>
      <content src="chapter2.html"/>
    </navPoint>
  </navMap>
</ncx>""")

    (FIXTURES / "sample.epub").write_bytes(buf.getvalue())
    print("Created sample.epub")


def create_sample_docx():
    """Create a minimal DOCX file (OOXML ZIP format)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>""")

        z.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>""")

        z.writestr("word/_rels/document.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>""")

        z.writestr("word/styles.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:outlineLvl w:val="0"/></w:pPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:outlineLvl w:val="1"/></w:pPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Normal">
    <w:name w:val="Normal"/>
  </w:style>
</w:styles>""")

        z.writestr("word/document.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
      <w:r><w:t>Chapter 1: Introduction</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>This document covers the principles of clean code. Good code should be readable and maintainable.</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading2"/></w:pPr>
      <w:r><w:t>Why Clean Code Matters</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>Technical debt accumulates over time and slows development velocity significantly.</w:t></w:r>
    </w:p>
  </w:body>
</w:document>""")

    (FIXTURES / "sample.docx").write_bytes(buf.getvalue())
    print("Created sample.docx")


if __name__ == "__main__":
    create_sample_pdf()
    create_scanned_mock_pdf()
    create_sample_epub()
    create_sample_docx()
    print("All fixture files created successfully.")
