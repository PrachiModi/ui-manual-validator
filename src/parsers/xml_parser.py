"""
XML Parser module for UI Manual Validator

This module provides functionality to parse XML manual test configurations
and convert them into structured data for the validation system.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """Represents a single test case from XML configuration"""
    id: str
    name: str
    description: str
    priority: str
    steps: List[Dict[str, str]]
    expected_result: str
    selectors: List[Dict[str, str]] = None

    def __post_init__(self):
        if self.selectors is None:
            self.selectors = []


@dataclass
class TestSuite:
    """Represents a test suite containing multiple test cases"""
    id: str
    name: str
    description: str
    test_cases: List[TestCase]


@dataclass
class ManualTestConfig:
    """Represents the complete manual test configuration"""
    version: str
    title: str
    description: str
    author: str
    created: str
    tags: List[str]
    test_suites: List[TestSuite]


class XMLParser:
    """Parser for XML manual test configuration files"""

    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize the XML parser
        
        Args:
            schema_path: Optional path to XSD schema for validation
        """
        self.schema_path = schema_path

    def parse_file(self, xml_file_path: str) -> ManualTestConfig:
        """
        Parse an XML manual test configuration file
        
        Args:
            xml_file_path: Path to the XML file to parse
            
        Returns:
            ManualTestConfig object containing parsed data
            
        Raises:
            FileNotFoundError: If the XML file doesn't exist
            ET.ParseError: If the XML is malformed
        """
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            return self._parse_root_element(root)
        except FileNotFoundError:
            logger.error(f"XML file not found: {xml_file_path}")
            raise
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML file {xml_file_path}: {e}")
            raise

    def parse_string(self, xml_content: str) -> ManualTestConfig:
        """
        Parse XML content from a string
        
        Args:
            xml_content: XML content as string
            
        Returns:
            ManualTestConfig object containing parsed data
        """
        try:
            root = ET.fromstring(xml_content)
            return self._parse_root_element(root)
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML content: {e}")
            raise

    def _parse_root_element(self, root: ET.Element) -> ManualTestConfig:
        """Parse the root manualTest element"""
        namespace = self._get_namespace()
        
        # Extract metadata
        metadata = root.find(f'.//{{{namespace}}}metadata')
        if metadata is None:
            metadata = root.find('.//metadata')  # Fallback for no namespace
        
        title = self._get_element_text(metadata, 'title', 'Untitled Test')
        description = self._get_element_text(metadata, 'description', '')
        author = self._get_element_text(metadata, 'author', 'Unknown')
        created = self._get_element_text(metadata, 'created', '')
        
        # Extract tags
        tags = []
        tags_element = metadata.find(f'.//{{{namespace}}}tags') if metadata else None
        if tags_element is None and metadata is not None:
            tags_element = metadata.find('.//tags')  # Fallback
        
        if tags_element is not None:
            for tag in tags_element.findall(f'.//{{{namespace}}}tag'):
                if tag.text:
                    tags.append(tag.text)

        # Extract test suites
        test_suites = []
        test_suites_element = root.find(f'.//{{{namespace}}}testSuites')
        if test_suites_element is None:
            test_suites_element = root.find('.//testSuites')  # Fallback
        
        if test_suites_element is not None:
            for suite_element in test_suites_element.findall(f'.//{{{namespace}}}testSuite'):
                if suite_element is None:
                    suite_element = test_suites_element.findall('.//testSuite')  # Fallback
                
                suite = self._parse_test_suite(suite_element)
                if suite:
                    test_suites.append(suite)

        return ManualTestConfig(
            version=root.get('version', '1.0'),
            title=title,
            description=description,
            author=author,
            created=created,
            tags=tags,
            test_suites=test_suites
        )

    def _parse_test_suite(self, suite_element: ET.Element) -> Optional[TestSuite]:
        """Parse a single test suite element"""
        if suite_element is None:
            return None
            
        namespace = self._get_namespace()
        suite_id = suite_element.get('id', '')
        name = self._get_element_text(suite_element, 'name', 'Unnamed Suite')
        description = self._get_element_text(suite_element, 'description', '')
        
        test_cases = []
        test_cases_element = suite_element.find(f'.//{{{namespace}}}testCases')
        if test_cases_element is None:
            test_cases_element = suite_element.find('.//testCases')  # Fallback
            
        if test_cases_element is not None:
            for case_element in test_cases_element.findall(f'.//{{{namespace}}}testCase'):
                if case_element is None:
                    case_element = test_cases_element.findall('.//testCase')  # Fallback
                
                test_case = self._parse_test_case(case_element)
                if test_case:
                    test_cases.append(test_case)

        return TestSuite(
            id=suite_id,
            name=name,
            description=description,
            test_cases=test_cases
        )

    def _parse_test_case(self, case_element: ET.Element) -> Optional[TestCase]:
        """Parse a single test case element"""
        if case_element is None:
            return None
            
        namespace = self._get_namespace()
        case_id = case_element.get('id', '')
        name = self._get_element_text(case_element, 'name', 'Unnamed Test Case')
        description = self._get_element_text(case_element, 'description', '')
        priority = self._get_element_text(case_element, 'priority', 'medium')
        expected_result = self._get_element_text(case_element, 'expectedResult', '')
        
        # Parse steps
        steps = []
        steps_element = case_element.find(f'.//{{{namespace}}}steps')
        if steps_element is None:
            steps_element = case_element.find('.//steps')  # Fallback
            
        if steps_element is not None:
            for step_element in steps_element.findall(f'.//{{{namespace}}}step'):
                if step_element is None:
                    step_element = steps_element.findall('.//step')  # Fallback
                
                step = self._parse_step(step_element)
                if step:
                    steps.append(step)

        # Parse selectors
        selectors = []
        selectors_element = case_element.find(f'.//{{{namespace}}}selectors')
        if selectors_element is None:
            selectors_element = case_element.find('.//selectors')  # Fallback
            
        if selectors_element is not None:
            for selector_element in selectors_element.findall(f'.//{{{namespace}}}selector'):
                if selector_element is None:
                    selector_element = selectors_element.findall('.//selector')  # Fallback
                
                selector = self._parse_selector(selector_element)
                if selector:
                    selectors.append(selector)

        return TestCase(
            id=case_id,
            name=name,
            description=description,
            priority=priority,
            steps=steps,
            expected_result=expected_result,
            selectors=selectors
        )

    def _parse_step(self, step_element: ET.Element) -> Optional[Dict[str, str]]:
        """Parse a single step element"""
        if step_element is None:
            return None
            
        return {
            'number': step_element.get('number', '1'),
            'action': self._get_element_text(step_element, 'action', ''),
            'target': self._get_element_text(step_element, 'target', ''),
            'data': self._get_element_text(step_element, 'data', '')
        }

    def _parse_selector(self, selector_element: ET.Element) -> Optional[Dict[str, str]]:
        """Parse a single selector element"""
        if selector_element is None:
            return None
            
        return {
            'type': self._get_element_text(selector_element, 'type', 'css'),
            'value': self._get_element_text(selector_element, 'value', ''),
            'description': self._get_element_text(selector_element, 'description', '')
        }

    def _get_element_text(self, parent: ET.Element, tag_name: str, default: str = '') -> str:
        """Safely get text content from a child element"""
        if parent is None:
            return default
            
        # Try with namespace first
        element = parent.find(f'.//{{{self._get_namespace()}}}{tag_name}')
        if element is None:
            # Fallback to no namespace
            element = parent.find(f'.//{tag_name}')
            
        return element.text if element is not None and element.text else default

    def _get_namespace(self) -> str:
        """Get the namespace URI"""
        return "http://ui-manual-validator.com/schema"


def parse_manual_config(file_path: str, schema_path: Optional[str] = None) -> ManualTestConfig:
    """
    Convenience function to parse a manual test configuration file
    
    Args:
        file_path: Path to the XML configuration file
        schema_path: Optional path to XSD schema for validation
        
    Returns:
        ManualTestConfig object containing parsed data
    """
    parser = XMLParser(schema_path)
    return parser.parse_file(file_path)