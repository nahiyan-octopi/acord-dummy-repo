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
            # Call OpenAI API with minimal overhead
            response = self.openai_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
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
        Build a compact prompt for OpenAI.
        
        Args:
            raw_fields: Dictionary of raw PDF field names and values
            
        Returns:
            Prompt string for OpenAI
        """
        field_mappings = self.mappings_data.get("fieldMappings", {})
        
        # Match extracted fields to mappings (case-insensitive)
        raw_field_names_lower = {k.lower(): k for k in raw_fields.keys()}
        
        # Build data with schema paths
        mapped_data = []
        unmapped_data = []
        
        for key, value in raw_fields.items():
            if value is None or not str(value).strip():
                continue
            
            # Find mapping for this field
            schema_path = None
            for pdf_field, path in field_mappings.items():
                if pdf_field.lower() == key.lower():
                    schema_path = path
                    break
            
            if schema_path:
                mapped_data.append(f'{schema_path}="{value}"')
            else:
                unmapped_data.append(f'{key}="{value}"')
        
        prompt = f"""Convert to nested JSON. Paths use dots for nesting (e.g. "a.b"="v" becomes {{"a":{{"b":"v"}}}}).
Checkboxes/Indicators: "Yes"/"No". Combine address lines. insurers is array with letter/name/naic.

{chr(10).join(mapped_data)}

unmapped_fields:
{chr(10).join(unmapped_data) if unmapped_data else 'none'}

JSON only:"""

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
