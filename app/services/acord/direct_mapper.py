"""
ACORD Direct Field Mapper

Applies field mappings from acord_field_mappings.json directly in Python
without AI. Returns structured coverage data and tracks unmapped fields.
"""

import json
from pathlib import Path
from typing import Dict, Any, Set, Tuple


class DirectMapper:
    """
    Maps raw PDF form fields to structured schema using explicit mappings.
    No AI involved - pure programmatic mapping.
    """
    
    def __init__(self, mappings_path: str = None):
        """
        Initialize with field mappings.
        
        Args:
            mappings_path: Path to acord_field_mappings.json
        """
        if mappings_path is None:
            mappings_path = Path(__file__).parent.parent.parent / "constants" / "acord_field_mappings.json"
        
        self.mappings_path = Path(mappings_path)
        self.mappings_data = self._load_mappings()
        self.field_mappings = self.mappings_data.get("fieldMappings", {})
        
        # Define which schema paths belong to "coverage" sections (direct mapped)
        # vs "unformatted" sections (AI processed)
        self.coverage_prefixes = [
            "issue_date",
            "certificate_number",
            "certificate_holder",
            "general_liability.",
            "auto_liability.",
            "umbrella.",
            "workers_comp.",
            "other.",
            "remarks",
            "authorized_representative"
        ]
        
        # These will be processed by AI
        self.unformatted_prefixes = [
            "insured.",
            "producer.",
            "certificate_holder.",
            "insurers"
        ]
    
    def _load_mappings(self) -> Dict[str, Any]:
        """Load field mappings from JSON file."""
        try:
            if self.mappings_path.exists():
                with open(self.mappings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"Warning: Mappings file not found at {self.mappings_path}")
                return {}
        except Exception as e:
            print(f"Error loading mappings: {e}")
            return {}
    
    def direct_map(self, raw_fields: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Apply direct mappings to raw fields.
        
        Args:
            raw_fields: Dictionary of raw PDF field names and values
            
        Returns:
            Tuple of (coverage_data, unmapped_fields)
            - coverage_data: Structured data for coverage sections
            - unmapped_fields: Fields to be processed by AI
        """
        if not raw_fields:
            return {}, {}
        
        # Initialize result structure
        coverage_data = self._init_coverage_structure()
        unmapped_fields = {}
        mapped_keys = set()
        
        # Normalize raw field names by stripping [0] suffix
        # e.g., "Form_CompletionDate_A[0]" -> "Form_CompletionDate_A"
        normalized_fields = {}
        for raw_key, value in raw_fields.items():
            # Strip trailing [0], [1], etc.
            normalized_key = raw_key
            if raw_key.endswith('[0]'):
                normalized_key = raw_key[:-3]
            elif raw_key.endswith(']') and '[' in raw_key:
                # Handle other array indices like [1], [2]
                bracket_pos = raw_key.rfind('[')
                normalized_key = raw_key[:bracket_pos]
            normalized_fields[normalized_key] = value
        
        # Apply mappings using normalized field names
        for pdf_field, schema_path in self.field_mappings.items():
            if pdf_field in normalized_fields:
                value = normalized_fields[pdf_field]
                
                # Check if this is a coverage field or unformatted field
                if self._is_coverage_path(schema_path):
                    # Direct map to coverage structure
                    self._set_nested_value(coverage_data, schema_path, value)
                    mapped_keys.add(pdf_field)
                else:
                    # Will be processed by AI - add to unmapped
                    unmapped_fields[pdf_field] = value
                    mapped_keys.add(pdf_field)
        
        # Add truly unmapped fields (not in mappings at all)
        for pdf_field, value in normalized_fields.items():
            if pdf_field not in mapped_keys and value is not None:
                unmapped_fields[pdf_field] = value
        
        # Normalize checkbox values in coverage data
        coverage_data = self._normalize_checkboxes(coverage_data)
        
        return coverage_data, unmapped_fields
    
    def _is_coverage_path(self, schema_path: str) -> bool:
        """Check if schema path belongs to coverage sections."""
        for prefix in self.coverage_prefixes:
            if schema_path.startswith(prefix) or schema_path == prefix.rstrip('.'):
                return True
        return False
    
    def _init_coverage_structure(self) -> Dict[str, Any]:
        """Initialize empty coverage data structure."""
        return {
            "issue_date": None,
            "certificate_number": None,
            "certificate_holder": {
                "name": None,
                "address": None
            },
            "general_liability": {
                "insurer_letter": None,
                "policy_number": None,
                "effective_date": None,
                "expiration_date": None,
                "general_liability_coverage_indicator": None,
                "claims_made": None,
                "occurrence": None,
                "custom_option_1": None,
                "custom_option_1_value": None,
                "custom_option_2": None,
                "custom_option_2_value": None,
                "general_aggregate_limit_applies_per_policy": None,
                "general_aggregate_limit_applies_per_project": None,
                "general_aggregate_limit_applies_per_location": None,
                "general_aggregate_limit_applies_per_other": None,
                "general_aggregate_limit_applies_per_other_value": None,
                "each_occurrence": None,
                "damage_to_rented_premises": None,
                "medical_expense": None,
                "personal_adv_injury": None,
                "general_aggregate": None,
                "products_comp_op_agg": None,
                "additional_insured": None,
                "subrogation_waived": None
            },
            "auto_liability": {
                "insurer_letter": None,
                "policy_number": None,
                "effective_date": None,
                "expiration_date": None,
                "any_auto": None,
                "owned_autos_only": None,
                "hired_autos_only": None,
                "scheduled_autos_only": None,
                "non_owned_autos_only": None,
                "custom_option_1": None,
                "custom_option_1_value": None,
                "custom_option_2": None,
                "custom_option_2_value": None,
                "combined_single_limit": None,
                "bodily_injury_per_person": None,
                "bodily_injury_per_accident": None,
                "property_damage": None,
                "additional_insured": None,
                "subrogation_waived": None
            },
            "umbrella": {
                "insurer_letter": None,
                "policy_number": None,
                "effective_date": None,
                "expiration_date": None,
                "umbrella_liab": None,
                "excess_liab": None,
                "occurrence": None,
                "claims_made": None,
                "deductible": None,
                "retention": None,
                "retention_amount": None,
                "each_occurrence": None,
                "aggregate": None,
                "additional_insured": None,
                "subrogation_waived": None
            },
            "workers_comp": {
                "insurer_letter": None,
                "policy_number": None,
                "effective_date": None,
                "expiration_date": None,
                "per_statute": None,
                "other": None,
                "per_statute_other_limit": None,
                "each_accident": None,
                "disease_each_employee": None,
                "disease_policy_limit": None,
                "any_excluded": None,
                "additional_insured": None,
                "subrogation_waived": None
            },
            "other": {
                "insurer_letter": None,
                "type_of_insurance": None,
                "addl": None,
                "subr": None,
                "policy_number": None,
                "effective_date": None,
                "expiration_date": None,
                "description": None,
                "first_policy_option": None,
                "first_policy_limit": None,
                "second_policy_option": None,
                "second_policy_limit": None,
                "third_policy_option": None,
                "third_policy_limit": None
            },
            "remarks": None,
            "authorized_representative": None
        }
    
    def _set_nested_value(self, data: Dict, path: str, value: Any) -> None:
        """
        Set a value in nested dictionary using dot notation path.
        
        Args:
            data: Dictionary to update
            path: Dot-notation path (e.g., "general_liability.policy_number")
            value: Value to set
        """
        keys = path.split('.')
        current = data

        if isinstance(value, str):
            value = value.strip()
        
        for key in keys[:-1]:
            if key not in current or current[key] is None or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        
        # Set the final value
        final_key = keys[-1]
        
        # If the field already has a value and we're setting it again,
        # concatenate for address fields (multi-line addresses)
        if final_key == 'address' and current.get(final_key):
            existing = current[final_key]
            if value and str(value).strip():
                # Combine with existing value, separated by space or newline
                current[final_key] = f"{existing}, {value}"
        else:
            current[final_key] = value
    
    def _normalize_checkboxes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize checkbox values to 'Yes'/'No' strings.
        
        Args:
            data: Coverage data structure
            
        Returns:
            Data with normalized checkbox values
        """
        checkbox_fields = [
            # General Liability
            "claims_made", "occurrence", "custom_option_1", "custom_option_2",
            "general_aggregate_limit_applies_per_policy",
            "general_aggregate_limit_applies_per_project",
            "general_aggregate_limit_applies_per_location",
            "general_aggregate_limit_applies_per_other",
            "additional_insured", "subrogation_waived",
            # Auto Liability
            "any_auto", "owned_autos_only", "hired_autos_only",
            "scheduled_autos_only", "non_owned_autos_only",
            # Umbrella
            "umbrella_liab", "excess_liab", "deductible", "retention",
            # Workers Comp
            "per_statute", "other", "any_excluded",
            # Other
            "addl", "subr"
        ]
        
        def normalize_value(val):
            """Convert checkbox value to Yes/No."""
            if val is None:
                return None
            if isinstance(val, bool):
                return "Yes" if val else "No"
            if isinstance(val, str):
                val_lower = val.lower().strip()
                if val_lower in ['yes', 'y', 'true', '1', '/1', '/yes', 'x', 'checked', 'on']:
                    return "Yes"
                elif val_lower in ['no', 'n', 'false', '0', '/0', '/no', 'off', 'unchecked']:
                    return "No"
            return val
        
        def process_dict(d):
            """Recursively process dictionary."""
            for key, value in d.items():
                if isinstance(value, dict):
                    process_dict(value)
                elif key in checkbox_fields:
                    d[key] = normalize_value(value)
            return d
        
        return process_dict(data)


# Singleton instance
_direct_mapper = None


def get_direct_mapper() -> DirectMapper:
    """Get or create direct mapper singleton."""
    global _direct_mapper
    if _direct_mapper is None:
        _direct_mapper = DirectMapper()
    return _direct_mapper
