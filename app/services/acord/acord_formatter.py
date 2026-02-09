"""
ACORD Data Formatter

Transforms organized ACORD data into tabbed UI format.
Coverage sections use predefined structure.
Unformatted data uses AI-structured data directly.
"""

from typing import Dict, Any


def format_checkbox(value: Any) -> str:
    """Convert checkbox/indicator value to 'Yes' or 'No' string."""
    if value is None:
        return "No"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, str):
        val_lower = value.lower().strip()
        if val_lower in ['yes', 'y', 'true', '1', '/1', '/yes', 'x', 'checked']:
            return "Yes"
    return "No"


def format_limit(value: Any) -> str:
    """Format currency/limit value."""
    if value is None:
        return ""
    
    # Handle boolean-like strings that shouldn't be in limit fields
    if isinstance(value, str):
        val_lower = value.lower().strip()
        if val_lower in ['yes', 'no', 'true', 'false', 'y', 'n']:
            return ""
            
    return str(value)


def format_for_tabs(organized_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform organized ACORD data into tabbed UI format.
    
    Args:
        organized_data: Data from hybrid extraction (direct map + AI)
        
    Returns:
        Data formatted for tabbed UI display
    """
    # Extract source data with defaults
    gl = organized_data.get("general_liability", {}) or {}
    auto = organized_data.get("auto_liability", {}) or {}
    umbrella = organized_data.get("umbrella", {}) or {}
    wc = organized_data.get("workers_comp", {}) or {}
    other = organized_data.get("other", {}) or {}
    
    # AI-structured unformatted data (flexible structure)
    unformatted = organized_data.get("unformatted_data", {}) or {}
    
    # Build tabbed output structure
    tabbed_output = {
        "information": {
            "certificate_date": organized_data.get("issue_date"),
            "certificate_number": organized_data.get("certificate_number"),
            "description_of_operations": organized_data.get("remarks"),
            "certificate_holder": organized_data.get("certificate_holder"),
            "authorized_representative": organized_data.get("authorized_representative")
        },
        "general_liability": {
            "policy_information": {
                "insurer_letter": gl.get("insurer_letter"),
                "policy_number": gl.get("policy_number"),
                "effective_date": gl.get("effective_date"),
                "expiration_date": gl.get("expiration_date"),
                "additional_insured": format_checkbox(gl.get("additional_insured")),
                "subrogation_waived": format_checkbox(gl.get("subrogation_waived"))
            },
            "policy_options": {
                "general_liability_coverage_indicator": format_checkbox(gl.get("general_liability_coverage_indicator")),
                "claims_made": format_checkbox(gl.get("claims_made")),
                "occurrence": format_checkbox(gl.get("occurrence")),
                "custom_option_1": format_checkbox(gl.get("custom_option_1")),
                "custom_option_1_value": gl.get("custom_option_1_value"),
                "custom_option_2": format_checkbox(gl.get("custom_option_2")),
                "custom_option_2_value": gl.get("custom_option_2_value"),
                "aggregate_applies_policy": format_checkbox(gl.get("general_aggregate_limit_applies_per_policy")),
                "aggregate_applies_project": format_checkbox(gl.get("general_aggregate_limit_applies_per_project")),
                "aggregate_applies_location": format_checkbox(gl.get("general_aggregate_limit_applies_per_location")),
                "aggregate_applies_other": format_checkbox(gl.get("general_aggregate_limit_applies_per_other")),
                "aggregate_applies_other_value": gl.get("general_aggregate_limit_applies_per_other_value")
            },
            "policy_limits": {
                "each_occurrence": format_limit(gl.get("each_occurrence")),
                "damage_to_rented_premises": format_limit(gl.get("damage_to_rented_premises")),
                "med_exp": format_limit(gl.get("medical_expense")),
                "personal_adv_injury": format_limit(gl.get("personal_adv_injury")),
                "general_aggregate": format_limit(gl.get("general_aggregate")),
                "products_comp_op_agg": format_limit(gl.get("products_comp_op_agg"))
            }
        },
        "automobile_liability": {
            "policy_information": {
                "insurer_letter": auto.get("insurer_letter"),
                "policy_number": auto.get("policy_number"),
                "effective_date": auto.get("effective_date"),
                "expiration_date": auto.get("expiration_date"),
                "additional_insured": format_checkbox(auto.get("additional_insured")),
                "subrogation_waived": format_checkbox(auto.get("subrogation_waived"))
            },
            "policy_options": {
                "any_auto": format_checkbox(auto.get("any_auto")),
                "owned_autos_only": format_checkbox(auto.get("owned_autos_only")),
                "hired_autos_only": format_checkbox(auto.get("hired_autos_only")),
                "scheduled_autos_only": format_checkbox(auto.get("scheduled_autos_only")),
                "non_owned_autos_only": format_checkbox(auto.get("non_owned_autos_only")),
                "custom_option_1": format_checkbox(auto.get("custom_option_1")),
                "custom_option_1_value": auto.get("custom_option_1_value"),
                "custom_option_2": format_checkbox(auto.get("custom_option_2")),
                "custom_option_2_value": auto.get("custom_option_2_value")
            },
            "policy_limits": {
                "combined_single_limit": format_limit(auto.get("combined_single_limit")),
                "bodily_injury_person": format_limit(auto.get("bodily_injury_per_person")),
                "bodily_injury_accident": format_limit(auto.get("bodily_injury_per_accident")),
                "property_damage": format_limit(auto.get("property_damage"))
            }
        },
        "umbrella_liability": {
            "policy_information": {
                "insurer_letter": umbrella.get("insurer_letter"),
                "policy_number": umbrella.get("policy_number"),
                "effective_date": umbrella.get("effective_date"),
                "expiration_date": umbrella.get("expiration_date"),
                "additional_insured": format_checkbox(umbrella.get("additional_insured")),
                "subrogation_waived": format_checkbox(umbrella.get("subrogation_waived"))
            },
            "policy_options": {
                "umbrella_liability": format_checkbox(umbrella.get("umbrella_liab")),
                "excess_liability": format_checkbox(umbrella.get("excess_liab")),
                "occurrence": format_checkbox(umbrella.get("occurrence")),
                "claims_made": format_checkbox(umbrella.get("claims_made")),
                "deductible": format_checkbox(umbrella.get("deductible")),
                "retention_checkbox": format_checkbox(umbrella.get("retention")),
                "retention": format_limit(umbrella.get("retention_amount"))
            },
            "policy_limits": {
                "each_occurrence": format_limit(umbrella.get("each_occurrence")),
                "aggregate": format_limit(umbrella.get("aggregate"))
            }
        },
        "workers_comp": {
            "policy_information": {
                "insurer_letter": wc.get("insurer_letter"),
                "policy_number": wc.get("policy_number"),
                "effective_date": wc.get("effective_date"),
                "expiration_date": wc.get("expiration_date"),
                "any_officers_excluded": format_checkbox(wc.get("any_excluded")),
                "additional_insured": format_checkbox(wc.get("additional_insured")),
                "subrogation_waived": format_checkbox(wc.get("subrogation_waived"))
            },
            "policy_options": {
                "per_statute": format_checkbox(wc.get("per_statute")),
                "other": format_checkbox(wc.get("other"))
            },
            "policy_limits": {
                "per_statute_other_limit": format_limit(wc.get("per_statute_other_limit")),
                "each_accident": format_limit(wc.get("each_accident")),
                "each_employee": format_limit(wc.get("disease_each_employee")),
                "disease_policy_limit": format_limit(wc.get("disease_policy_limit"))
            }
        },
        "other_coverage": {
            "policy_information": {
                "insurer_letter": other.get("insurer_letter"),
                "type_of_insurance": other.get("type_of_insurance") if other.get("type_of_insurance") else "Other",
                "policy_number": other.get("policy_number"),
                "effective_date": other.get("effective_date"),
                "expiration_date": other.get("expiration_date"),
                "additional_insured": format_checkbox(other.get("addl")),
                "subrogation_waived": format_checkbox(other.get("subr"))
            },
            "policy_limits": [
                {"policy_option": other.get("first_policy_option"), "policy_limit": format_limit(other.get("first_policy_limit"))},
                {"policy_option": other.get("second_policy_option"), "policy_limit": format_limit(other.get("second_policy_limit"))},
                {"policy_option": other.get("third_policy_option"), "policy_limit": format_limit(other.get("third_policy_limit"))}
            ]
        },
        
        # AI-structured unformatted data - include directly as returned by AI
        # This section adapts to available data (no predefined null fields)
        "unformatted_data": unformatted
    }
    
    return tabbed_output


class AcordFormatter:
    """Service class for formatting ACORD data for UI display."""
    
    def __init__(self):
        pass
    
    def format(self, organized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format organized data for tabbed UI display.
        
        Args:
            organized_data: Data from hybrid extraction (direct map + AI)
            
        Returns:
            Tabbed format for UI display
        """
        return format_for_tabs(organized_data)
