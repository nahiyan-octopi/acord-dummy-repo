"""
ACORD Data Organizer

Uses OpenAI to organize extracted PDF form fields into a standardized schema.
Provides explicit field mappings to ensure accurate classification.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from app.services.ai.openai_service import get_openai_service


class AcordOrganizer:
    """Organizes extracted ACORD form data using OpenAI with explicit mappings"""
    
    def __init__(self, mappings_path: Optional[str] = None):
        """
        Initialize organizer with field mappings.
        
        Args:
            mappings_path: Path to acord_field_mappings.json
        """
        if mappings_path is None:
            # Default to acord_data_structure folder
            mappings_path = Path(__file__).parent.parent.parent.parent / "acord_data_structure" / "acord_field_mappings.json"
        
        self.mappings_path = Path(mappings_path)
        self.mappings_data = self._load_mappings()
        self.openai_service = get_openai_service()
    
    def _load_mappings(self) -> Dict[str, Any]:
        """Load field mappings from JSON file"""
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
    
    def organize(self, raw_fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Organize raw extracted fields into standardized schema using OpenAI.
        
        Args:
            raw_fields: Dictionary of raw PDF field names and values
            
        Returns:
            Organized data matching target schema
        """
        if not raw_fields:
            return {
                "success": False,
                "error": "No fields to organize",
                "organized_data": {}
            }
        
        # Build the prompt with mappings
        prompt = self._build_prompt(raw_fields)
        
        try:
            # Call OpenAI API
            response = self.openai_service.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at organizing ACORD insurance form data. Return ONLY valid JSON with no additional text or explanation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            if not response.get("success"):
                return {
                    "success": False,
                    "error": response.get("error", "API call failed"),
                    "organized_data": {}
                }
            
            # Parse the response
            organized_data = self._parse_response(response.get("content", ""))
            
            return {
                "success": True,
                "organized_data": organized_data
            }
            
        except Exception as e:
            print(f"Error organizing data: {e}")
            return {
                "success": False,
                "error": str(e),
                "organized_data": {}
            }
    
    def _build_prompt(self, raw_fields: Dict[str, Any]) -> str:
        """
        Build the prompt for OpenAI with target schema and mappings.
        
        Args:
            raw_fields: Dictionary of raw PDF field names and values
            
        Returns:
            Prompt string for OpenAI
        """
        target_schema = self.mappings_data.get("targetSchema", {})
        field_mappings = self.mappings_data.get("fieldMappings", {})
        instructions = self.mappings_data.get("promptInstructions", "")
        
        # Build mappings text
        mappings_text = "\n".join([
            f"  {pdf_field} → {schema_path}"
            for pdf_field, schema_path in field_mappings.items()
        ])
        
        # Build raw data text (only non-null values)
        raw_data_items = []
        for key, value in raw_fields.items():
            if value is not None and str(value).strip():
                raw_data_items.append(f'  "{key}": "{value}"')
        raw_data_text = "{\n" + ",\n".join(raw_data_items) + "\n}"
        
        prompt = f"""{instructions}

TARGET SCHEMA (output must match this structure exactly):
{json.dumps(target_schema, indent=2)}

KNOWN FIELD MAPPINGS (PDF field name → schema path):
{mappings_text}

RAW EXTRACTED DATA FROM PDF (ALL fields extracted):
{raw_data_text}

CRITICAL INSTRUCTIONS FOR COMPLETE EXTRACTION:
1. Map ALL raw fields to the target schema using the known mappings above
2. For fields with multiple address components, combine them into a single address string
3. For checkbox fields (including "Indicator" fields), use "Yes" or "No"
4. For missing fields, use null
5. IMPORTANT: For any field that contains "InsurerLetterCode" or "INSR" or ends with "_LTR", map it to the appropriate insurer_letter field (general_liability.insurer_letter, auto_liability.insurer_letter, umbrella.insurer_letter, workers_comp.insurer_letter, or other.insurer_letter)
6. IMPORTANT: For General Liability custom options (CustomOption1_A, CustomOption2_A), extract BOTH the checkbox state AND any associated text value
7. IMPORTANT: For Auto Liability custom options (CustomOption1_A, CustomOption2_A), extract BOTH the checkbox state AND any associated text value  
8. IMPORTANT: For General Aggregate Limit Applies Per fields, map them to:
   - general_aggregate_limit_applies_per_policy (POLICY checkbox)
   - general_aggregate_limit_applies_per_project (PROJECT checkbox)
   - general_aggregate_limit_applies_per_location (LOC checkbox)
   - general_aggregate_limit_applies_per_other (OTHER checkbox)
   - general_aggregate_limit_applies_per_other_value (text value for OTHER)
9. IMPORTANT: For Auto Liability vehicle options, use the correct field names:
   - any_auto, owned_autos_only, hired_autos_only, scheduled_autos_only, non_owned_autos_only
10. IMPORTANT: Add an "unmapped_fields" object containing ANY fields from the raw data that do NOT match any known mapping. Use the original field name as the key.
11. Return ONLY the JSON object - no explanation or text outside the JSON

The output JSON must include ALL data from the PDF. Do not discard any information.

Return the complete organized JSON now:"""

        return prompt
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse OpenAI response to extract JSON.
        
        Args:
            response: Raw response from OpenAI
            
        Returns:
            Parsed JSON dictionary
        """
        if not response:
            return {}
        
        # Try to extract JSON from the response
        response = response.strip()
        
        # If response starts with ```json, extract the JSON block
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end > start:
                response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end > start:
                response = response[start:end].strip()
        
        # Try to parse as JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(response[start:end])
                except json.JSONDecodeError:
                    pass
        
        return {}


def organize_acord_data(raw_fields: Dict[str, Any], mappings_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to organize ACORD data.
    
    Args:
        raw_fields: Dictionary of raw PDF field names and values
        mappings_path: Optional path to field mappings JSON
        
    Returns:
        Organization result with organized_data
    """
    organizer = AcordOrganizer(mappings_path)
    return organizer.organize(raw_fields)
