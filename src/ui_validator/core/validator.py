import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

dataclass
class ValidationRule:
    """Represents a single validation rule"""
    id: str
    description: str
    category: str
    priority: str  # high, medium, low
    automated_check: Optional[str] = None
    manual_steps: List[str] = None
    expected_result: str = ""
    
    def __post_init__(self):
        if self.manual_steps is None:
            self.manual_steps = []

dataclass
class ValidationResult:
    """Represents the result of a validation"""
    rule_id: str
    status: str  # pass, fail, skip, pending
    timestamp: datetime
    notes: str = ""
    evidence: List[str] = None  # screenshots, logs, etc.
    validator: str = ""
    
    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []

class UIValidator:
    """Core validator class for managing UI validation workflows"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "validation_config.json"
        self.rules: Dict[str, ValidationRule] = {}
        self.results: List[ValidationResult] = []
        self.load_config()
    
    def load_config(self):
        """Load validation rules from configuration"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                for rule_data in config.get('rules', []):
                    rule = ValidationRule(**rule_data)
                    self.rules[rule.id] = rule
    
    def add_rule(self, rule: ValidationRule):
        """Add a new validation rule"""
        self.rules[rule.id] = rule
    
    def validate_rule(self, rule_id: str, status: str, notes: str = "", 
                     evidence: List[str] = None, validator: str = "") -> ValidationResult:
        """Record validation result for a specific rule"""
        if rule_id not in self.rules:
            raise ValueError(f"Rule {rule_id} not found")
        
        result = ValidationResult(
            rule_id=rule_id,
            status=status,
            timestamp=datetime.now(),
            notes=notes,
            evidence=evidence or [],
            validator=validator
        )
        
        self.results.append(result)
        return result
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results"""
        total = len(self.results)
        if total == 0:
            return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "pending": 0}
        
        status_counts = {}
        for result in self.results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
        
        return {
            "total": total,
            "passed": status_counts.get("pass", 0),
            "failed": status_counts.get("fail", 0),
            "skipped": status_counts.get("skip", 0),
            "pending": status_counts.get("pending", 0),
            "pass_rate": (status_counts.get("pass", 0) / total) * 100
        }
    
    def export_results(self, output_path: str):
        """Export validation results to JSON file"""
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_validation_summary(),
            "results": [asdict(result) for result in self.results]
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
    
    def get_failed_validations(self) -> List[ValidationResult]:
        """Get all failed validation results"""
        return [result for result in self.results if result.status == "fail"]
    
    def get_pending_validations(self) -> List[str]:
        """Get list of rules that haven't been validated yet"""
        validated_rules = {result.rule_id for result in self.results}
        return [rule_id for rule_id in self.rules.keys() if rule_id not in validated_rules]
