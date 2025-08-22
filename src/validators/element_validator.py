"""
Element Validator module for UI Manual Validator

This module provides validation logic for UI elements, including
accessibility checks, visual validation, and functional testing.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ValidationCategory(Enum):
    """Categories of validation checks"""
    ACCESSIBILITY = "accessibility"
    FUNCTIONALITY = "functionality"
    VISUAL = "visual"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    COMPLIANCE = "compliance"


@dataclass
class ValidationIssue:
    """Represents a validation issue found during element validation"""
    element_selector: str
    issue_type: str
    severity: ValidationSeverity
    category: ValidationCategory
    message: str
    description: str
    recommendation: str
    wcag_guideline: Optional[str] = None
    element_info: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Results of element validation"""
    element_selector: str
    passed: bool
    issues: List[ValidationIssue]
    checks_performed: List[str]
    metadata: Dict[str, Any]
    validation_time: float


class ElementValidator:
    """Validator for UI elements with comprehensive checks"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the element validator
        
        Args:
            config: Configuration dictionary for validation rules
        """
        self.config = config or self._get_default_config()
        self.validation_rules = self._load_validation_rules()

    def validate_element(self, element_info: Dict[str, Any], 
                        checks: Optional[List[str]] = None) -> ValidationResult:
        """
        Validate a single element against multiple criteria
        
        Args:
            element_info: Dictionary containing element information
            checks: Optional list of specific checks to perform
            
        Returns:
            ValidationResult object containing validation results
        """
        import time
        start_time = time.time()
        
        if checks is None:
            checks = list(self.validation_rules.keys())
        
        issues = []
        checks_performed = []
        
        for check_name in checks:
            if check_name in self.validation_rules:
                try:
                    check_issues = self.validation_rules[check_name](element_info)
                    issues.extend(check_issues)
                    checks_performed.append(check_name)
                except Exception as e:
                    logger.error(f"Error performing check '{check_name}': {e}")
        
        validation_time = time.time() - start_time
        passed = len([issue for issue in issues if issue.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH]]) == 0
        
        return ValidationResult(
            element_selector=element_info.get('css_selector', 'unknown'),
            passed=passed,
            issues=issues,
            checks_performed=checks_performed,
            metadata={
                'element_tag': element_info.get('tag_name'),
                'element_id': element_info.get('attributes', {}).get('id'),
                'element_classes': element_info.get('attributes', {}).get('class')
            },
            validation_time=validation_time
        )

    def validate_page_elements(self, elements: List[Dict[str, Any]], 
                              checks: Optional[List[str]] = None) -> List[ValidationResult]:
        """
        Validate multiple elements on a page
        
        Args:
            elements: List of element information dictionaries
            checks: Optional list of specific checks to perform
            
        Returns:
            List of ValidationResult objects
        """
        results = []
        
        for element in elements:
            result = self.validate_element(element, checks)
            results.append(result)
        
        return results

    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Generate a summary of validation results
        
        Args:
            results: List of ValidationResult objects
            
        Returns:
            Dictionary containing validation summary
        """
        total_elements = len(results)
        passed_elements = len([r for r in results if r.passed])
        failed_elements = total_elements - passed_elements
        
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)
        
        issues_by_severity = {}
        issues_by_category = {}
        
        for issue in all_issues:
            # Count by severity
            severity = issue.severity.value
            issues_by_severity[severity] = issues_by_severity.get(severity, 0) + 1
            
            # Count by category
            category = issue.category.value
            issues_by_category[category] = issues_by_category.get(category, 0) + 1
        
        return {
            'total_elements': total_elements,
            'passed_elements': passed_elements,
            'failed_elements': failed_elements,
            'pass_rate': (passed_elements / total_elements * 100) if total_elements > 0 else 0,
            'total_issues': len(all_issues),
            'issues_by_severity': issues_by_severity,
            'issues_by_category': issues_by_category,
            'critical_issues': issues_by_severity.get('critical', 0),
            'high_issues': issues_by_severity.get('high', 0)
        }

    def _load_validation_rules(self) -> Dict[str, callable]:
        """Load validation rules as callable functions"""
        return {
            'accessibility_basic': self._check_accessibility_basic,
            'accessibility_advanced': self._check_accessibility_advanced,
            'form_validation': self._check_form_elements,
            'link_validation': self._check_links,
            'image_validation': self._check_images,
            'interactive_elements': self._check_interactive_elements,
            'text_content': self._check_text_content,
            'visual_layout': self._check_visual_layout,
            'performance': self._check_performance_indicators
        }

    def _check_accessibility_basic(self, element_info: Dict[str, Any]) -> List[ValidationIssue]:
        """Basic accessibility checks"""
        issues = []
        tag_name = element_info.get('tag_name', '').lower()
        attributes = element_info.get('attributes', {})
        selector = element_info.get('css_selector', 'unknown')
        
        # Check for missing alt text on images
        if tag_name == 'img':
            if 'alt' not in attributes or not attributes['alt'].strip():
                issues.append(ValidationIssue(
                    element_selector=selector,
                    issue_type='missing_alt_text',
                    severity=ValidationSeverity.HIGH,
                    category=ValidationCategory.ACCESSIBILITY,
                    message='Image missing alt text',
                    description='Image elements must have alt text for screen readers',
                    recommendation='Add descriptive alt text to the image',
                    wcag_guideline='WCAG 2.1 - 1.1.1 Non-text Content'
                ))
        
        # Check for form labels
        if tag_name == 'input' and attributes.get('type') not in ['submit', 'button', 'hidden']:
            if 'id' not in attributes:
                issues.append(ValidationIssue(
                    element_selector=selector,
                    issue_type='missing_input_id',
                    severity=ValidationSeverity.MEDIUM,
                    category=ValidationCategory.ACCESSIBILITY,
                    message='Form input missing ID for label association',
                    description='Input elements should have IDs for proper label association',
                    recommendation='Add an id attribute to enable label association',
                    wcag_guideline='WCAG 2.1 - 3.3.2 Labels or Instructions'
                ))
        
        # Check for button accessibility
        if tag_name == 'button' or (tag_name == 'input' and attributes.get('type') == 'button'):
            text_content = element_info.get('text_content', '').strip()
            if not text_content and 'aria-label' not in attributes and 'title' not in attributes:
                issues.append(ValidationIssue(
                    element_selector=selector,
                    issue_type='button_no_accessible_name',
                    severity=ValidationSeverity.HIGH,
                    category=ValidationCategory.ACCESSIBILITY,
                    message='Button has no accessible name',
                    description='Buttons must have accessible names for screen readers',
                    recommendation='Add text content, aria-label, or title attribute',
                    wcag_guideline='WCAG 2.1 - 4.1.2 Name, Role, Value'
                ))
        
        return issues

    def _check_accessibility_advanced(self, element_info: Dict[str, Any]) -> List[ValidationIssue]:
        """Advanced accessibility checks"""
        issues = []
        attributes = element_info.get('attributes', {})
        selector = element_info.get('css_selector', 'unknown')
        
        # Check for proper heading hierarchy
        tag_name = element_info.get('tag_name', '').lower()
        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # This would need page context to properly validate hierarchy
            # For now, just check for empty headings
            text_content = element_info.get('text_content', '').strip()
            if not text_content:
                issues.append(ValidationIssue(
                    element_selector=selector,
                    issue_type='empty_heading',
                    severity=ValidationSeverity.MEDIUM,
                    category=ValidationCategory.ACCESSIBILITY,
                    message='Heading element is empty',
                    description='Heading elements should contain descriptive text',
                    recommendation='Add meaningful text content to the heading',
                    wcag_guideline='WCAG 2.1 - 2.4.6 Headings and Labels'
                ))
        
        # Check for proper ARIA usage
        for attr_name, attr_value in attributes.items():
            if attr_name.startswith('aria-'):
                if not attr_value.strip():
                    issues.append(ValidationIssue(
                        element_selector=selector,
                        issue_type='empty_aria_attribute',
                        severity=ValidationSeverity.MEDIUM,
                        category=ValidationCategory.ACCESSIBILITY,
                        message=f'Empty ARIA attribute: {attr_name}',
                        description='ARIA attributes should have meaningful values',
                        recommendation=f'Provide a value for {attr_name} or remove the attribute',
                        wcag_guideline='WCAG 2.1 - 4.1.2 Name, Role, Value'
                    ))
        
        return issues

    def _check_form_elements(self, element_info: Dict[str, Any]) -> List[ValidationIssue]:
        """Form element specific checks"""
        issues = []
        tag_name = element_info.get('tag_name', '').lower()
        attributes = element_info.get('attributes', {})
        selector = element_info.get('css_selector', 'unknown')
        
        if tag_name in ['input', 'textarea', 'select']:
            # Check for required attribute handling
            if 'required' in attributes:
                if 'aria-required' not in attributes:
                    issues.append(ValidationIssue(
                        element_selector=selector,
                        issue_type='missing_aria_required',
                        severity=ValidationSeverity.LOW,
                        category=ValidationCategory.ACCESSIBILITY,
                        message='Required field missing aria-required attribute',
                        description='Required form fields should have aria-required="true"',
                        recommendation='Add aria-required="true" to the element',
                        wcag_guideline='WCAG 2.1 - 3.3.2 Labels or Instructions'
                    ))
            
            # Check for input type validation
            if tag_name == 'input':
                input_type = attributes.get('type', 'text')
                if input_type == 'email' and 'pattern' not in attributes:
                    issues.append(ValidationIssue(
                        element_selector=selector,
                        issue_type='email_input_no_validation',
                        severity=ValidationSeverity.LOW,
                        category=ValidationCategory.FUNCTIONALITY,
                        message='Email input without pattern validation',
                        description='Email inputs should have pattern validation for better UX',
                        recommendation='Consider adding a pattern attribute for email validation'
                    ))
        
        return issues

    def _check_links(self, element_info: Dict[str, Any]) -> List[ValidationIssue]:
        """Link element checks"""
        issues = []
        tag_name = element_info.get('tag_name', '').lower()
        attributes = element_info.get('attributes', {})
        selector = element_info.get('css_selector', 'unknown')
        
        if tag_name == 'a':
            href = attributes.get('href', '')
            text_content = element_info.get('text_content', '').strip()
            
            # Check for empty links
            if not text_content and 'aria-label' not in attributes:
                issues.append(ValidationIssue(
                    element_selector=selector,
                    issue_type='empty_link',
                    severity=ValidationSeverity.HIGH,
                    category=ValidationCategory.ACCESSIBILITY,
                    message='Link has no accessible text',
                    description='Links must have accessible text for screen readers',
                    recommendation='Add text content or aria-label to the link',
                    wcag_guideline='WCAG 2.1 - 2.4.4 Link Purpose'
                ))
            
            # Check for generic link text
            generic_texts = ['click here', 'read more', 'more', 'link', 'here']
            if text_content.lower() in generic_texts:
                issues.append(ValidationIssue(
                    element_selector=selector,
                    issue_type='generic_link_text',
                    severity=ValidationSeverity.MEDIUM,
                    category=ValidationCategory.USABILITY,
                    message='Link uses generic text',
                    description='Link text should be descriptive of the destination',
                    recommendation='Use more descriptive link text',
                    wcag_guideline='WCAG 2.1 - 2.4.4 Link Purpose'
                ))
            
            # Check for external links
            if href.startswith('http') and 'target' in attributes and attributes['target'] == '_blank':
                if 'rel' not in attributes or 'noopener' not in attributes['rel']:
                    issues.append(ValidationIssue(
                        element_selector=selector,
                        issue_type='external_link_security',
                        severity=ValidationSeverity.MEDIUM,
                        category=ValidationCategory.COMPLIANCE,
                        message='External link missing security attributes',
                        description='External links should include rel="noopener" for security',
                        recommendation='Add rel="noopener noreferrer" to external links'
                    ))
        
        return issues

    def _check_images(self, element_info: Dict[str, Any]) -> List[ValidationIssue]:
        """Image element checks"""
        issues = []
        tag_name = element_info.get('tag_name', '').lower()
        attributes = element_info.get('attributes', {})
        selector = element_info.get('css_selector', 'unknown')
        
        if tag_name == 'img':
            # Check for loading attribute
            if 'loading' not in attributes:
                issues.append(ValidationIssue(
                    element_selector=selector,
                    issue_type='missing_loading_attribute',
                    severity=ValidationSeverity.LOW,
                    category=ValidationCategory.PERFORMANCE,
                    message='Image missing loading attribute',
                    description='Images should use loading="lazy" for better performance',
                    recommendation='Add loading="lazy" for non-critical images'
                ))
            
            # Check for width/height attributes
            if 'width' not in attributes or 'height' not in attributes:
                issues.append(ValidationIssue(
                    element_selector=selector,
                    issue_type='missing_image_dimensions',
                    severity=ValidationSeverity.LOW,
                    category=ValidationCategory.PERFORMANCE,
                    message='Image missing width/height attributes',
                    description='Images should have width and height to prevent layout shift',
                    recommendation='Add width and height attributes to prevent CLS'
                ))
        
        return issues

    def _check_interactive_elements(self, element_info: Dict[str, Any]) -> List[ValidationIssue]:
        """Interactive element checks"""
        issues = []
        tag_name = element_info.get('tag_name', '').lower()
        bounding_rect = element_info.get('bounding_rect', {})
        selector = element_info.get('css_selector', 'unknown')
        
        # Check minimum touch target size
        interactive_tags = ['button', 'a', 'input', 'select', 'textarea']
        if tag_name in interactive_tags:
            width = bounding_rect.get('width', 0)
            height = bounding_rect.get('height', 0)
            
            min_size = 44  # WCAG recommendation for touch targets
            
            if width < min_size or height < min_size:
                issues.append(ValidationIssue(
                    element_selector=selector,
                    issue_type='small_touch_target',
                    severity=ValidationSeverity.MEDIUM,
                    category=ValidationCategory.USABILITY,
                    message=f'Touch target too small ({width}x{height}px)',
                    description='Interactive elements should be at least 44x44px for accessibility',
                    recommendation='Increase the size of the interactive element',
                    wcag_guideline='WCAG 2.1 - 2.5.5 Target Size'
                ))
        
        return issues

    def _check_text_content(self, element_info: Dict[str, Any]) -> List[ValidationIssue]:
        """Text content checks"""
        issues = []
        text_content = element_info.get('text_content', '')
        selector = element_info.get('css_selector', 'unknown')
        
        # Check for very long text without breaks
        if len(text_content) > 500 and '\n' not in text_content:
            issues.append(ValidationIssue(
                element_selector=selector,
                issue_type='long_text_no_breaks',
                severity=ValidationSeverity.LOW,
                category=ValidationCategory.USABILITY,
                message='Very long text without line breaks',
                description='Long text should be broken into paragraphs for readability',
                recommendation='Consider breaking long text into smaller sections'
            ))
        
        return issues

    def _check_visual_layout(self, element_info: Dict[str, Any]) -> List[ValidationIssue]:
        """Visual layout checks"""
        issues = []
        bounding_rect = element_info.get('bounding_rect', {})
        selector = element_info.get('css_selector', 'unknown')
        is_visible = element_info.get('is_visible', True)
        
        # Check for elements outside viewport
        x = bounding_rect.get('x', 0)
        y = bounding_rect.get('y', 0)
        
        if is_visible and (x < -100 or y < -100):
            issues.append(ValidationIssue(
                element_selector=selector,
                issue_type='element_outside_viewport',
                severity=ValidationSeverity.LOW,
                category=ValidationCategory.VISUAL,
                message='Element positioned outside typical viewport',
                description='Element may not be visible to users',
                recommendation='Check element positioning and layout'
            ))
        
        return issues

    def _check_performance_indicators(self, element_info: Dict[str, Any]) -> List[ValidationIssue]:
        """Performance-related checks"""
        issues = []
        tag_name = element_info.get('tag_name', '').lower()
        attributes = element_info.get('attributes', {})
        selector = element_info.get('css_selector', 'unknown')
        
        # Check for inline styles
        if 'style' in attributes and attributes['style'].strip():
            issues.append(ValidationIssue(
                element_selector=selector,
                issue_type='inline_styles',
                severity=ValidationSeverity.LOW,
                category=ValidationCategory.PERFORMANCE,
                message='Element uses inline styles',
                description='Inline styles can impact performance and maintainability',
                recommendation='Consider moving styles to CSS files'
            ))
        
        return issues

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default validation configuration"""
        return {
            'accessibility_level': 'AA',  # WCAG compliance level
            'check_performance': True,
            'check_usability': True,
            'check_visual': True,
            'minimum_touch_target': 44,
            'check_security': True
        }