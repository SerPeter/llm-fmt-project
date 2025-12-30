"""Tests for XML parser."""

import pytest

from llm_fmt.errors import ParseError
from llm_fmt.parsers import XmlParser


class TestXmlParserBasics:
    """Basic parsing tests."""

    def test_simple_element(self) -> None:
        """Parse simple XML element."""
        parser = XmlParser()
        data = b"<root><name>test</name></root>"
        result = parser.parse(data)
        assert result == {"root": {"name": "test"}}

    def test_nested_elements(self) -> None:
        """Parse nested XML structure."""
        parser = XmlParser()
        data = b"""<root>
            <user>
                <name>Alice</name>
                <age>30</age>
            </user>
        </root>"""
        result = parser.parse(data)
        assert result["root"]["user"]["name"] == "Alice"
        assert result["root"]["user"]["age"] == "30"

    def test_array_elements(self) -> None:
        """Parse repeating elements as array."""
        parser = XmlParser()
        data = b"""<root>
            <item>first</item>
            <item>second</item>
        </root>"""
        result = parser.parse(data)
        assert result["root"]["item"] == ["first", "second"]

    def test_attributes(self) -> None:
        """Parse element attributes."""
        parser = XmlParser()
        data = b'<root id="123"><name>test</name></root>'
        result = parser.parse(data)
        assert result["root"]["@id"] == "123"
        assert result["root"]["name"] == "test"

    def test_empty_element(self) -> None:
        """Parse empty root element."""
        parser = XmlParser()
        data = b"<root></root>"
        result = parser.parse(data)
        assert result == {"root": None}

    def test_self_closing_element(self) -> None:
        """Parse self-closing element."""
        parser = XmlParser()
        data = b"<root/>"
        result = parser.parse(data)
        assert result == {"root": None}

    def test_xml_declaration(self) -> None:
        """Parse with XML declaration."""
        parser = XmlParser()
        data = b'<?xml version="1.0" encoding="UTF-8"?><root>value</root>'
        result = parser.parse(data)
        assert result == {"root": "value"}

    def test_text_content(self) -> None:
        """Parse element with text content."""
        parser = XmlParser()
        data = b"<root>Hello World</root>"
        result = parser.parse(data)
        assert result == {"root": "Hello World"}


class TestXmlParserUnicode:
    """Unicode handling tests."""

    def test_unicode_content(self) -> None:
        """Parse Unicode characters."""
        parser = XmlParser()
        data = '<?xml version="1.0" encoding="UTF-8"?><root>日本語</root>'.encode("utf-8")
        result = parser.parse(data)
        assert result == {"root": "日本語"}

    def test_unicode_in_element_name(self) -> None:
        """Parse element with Unicode in content."""
        parser = XmlParser()
        data = "<root><emoji>🎉</emoji></root>".encode("utf-8")
        result = parser.parse(data)
        assert result["root"]["emoji"] == "🎉"


class TestXmlParserErrors:
    """Error handling tests."""

    def test_invalid_xml_raises(self) -> None:
        """Invalid XML raises ParseError."""
        parser = XmlParser()
        with pytest.raises(ParseError, match="Invalid XML"):
            parser.parse(b"<root><unclosed>")

    def test_empty_data_raises(self) -> None:
        """Empty data raises ParseError."""
        parser = XmlParser()
        with pytest.raises(ParseError, match="Invalid XML"):
            parser.parse(b"")

    def test_not_xml_raises(self) -> None:
        """Non-XML data raises ParseError."""
        parser = XmlParser()
        with pytest.raises(ParseError, match="Invalid XML"):
            parser.parse(b"this is not xml")


class TestXmlParserComplex:
    """Complex structure tests."""

    def test_mixed_content(self) -> None:
        """Parse mixed element types."""
        parser = XmlParser()
        data = b"""<config>
            <database host="localhost" port="5432">
                <name>mydb</name>
            </database>
            <features>
                <feature enabled="true">auth</feature>
                <feature enabled="false">cache</feature>
            </features>
        </config>"""
        result = parser.parse(data)
        assert result["config"]["database"]["@host"] == "localhost"
        assert result["config"]["database"]["name"] == "mydb"
        assert len(result["config"]["features"]["feature"]) == 2

    def test_cdata_section(self) -> None:
        """Parse CDATA section."""
        parser = XmlParser()
        data = b"<root><![CDATA[<not> <parsed>]]></root>"
        result = parser.parse(data)
        assert result["root"] == "<not> <parsed>"
