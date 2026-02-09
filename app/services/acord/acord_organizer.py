"""
ACORD Data Organizer

Uses OpenAI GPT to organize ONLY unformatted/supplementary data 
(insured, producer, certificate holder, insurers).

Coverage sections are handled by direct_mapper.py without AI.
"""

import json
from typing import Dict, Any

from app.services.ai.openai_service import get_openai_service


class AcordOrganizer:
    """
    Organizes unformatted ACORD form data using AI with guidance-based prompts.
    Only processes supplementary data (contacts, addresses, insurers).
    Coverage data is handled by DirectMapper.
    """
    
    def __init__(self):
        """Initialize organizer."""
        self.openai_service = get_openai_service()
    
    def organize_unformatted(self, unmapped_fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Organize unformatted/supplementary fields using AI with guidance.
        
        Args:
            unmapped_fields: Dictionary of PDF fields not consumed by direct mapper
            
        Returns:
            AI-structured data for unformatted sections
        """
        if not unmapped_fields:
            return {
                "success": True,
                "unformatted_data": {}
            }
        
        # Build guidance-based prompt
        prompt = self._build_guidance_prompt(unmapped_fields)
        
        try:
            # Call OpenAI API
            response = self.openai_service.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at organizing insurance form contact and entity data. Return ONLY valid JSON."
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
                    "unformatted_data": {}
                }
            
            # Parse the response
            unformatted_data = self._parse_response(response.get("content", ""))
            
            return {
                "success": True,
                "unformatted_data": unformatted_data,
                "tokens_used": response.get("usage", {})
            }
            
        except Exception as e:
            print(f"Error organizing unformatted data: {e}")
            return {
                "success": False,
                "error": str(e),
                "unformatted_data": {}
            }
    
    def _build_guidance_prompt(self, unmapped_fields: Dict[str, Any]) -> str:
        """Build a concise prompt for fast AI processing."""
        # Build compact raw data
        items = [f'"{k}": "{str(v).strip()}"' for k, v in unmapped_fields.items() 
                 if v is not None and str(v).strip()]
        raw_data = "{" + ", ".join(items) + "}"
        
        return f"""Organize ACORD insurance data into JSON:

INPUT: {raw_data}

OUTPUT FORMAT:
{{"insured":{{"name":"...","address":"..."}},"producer":{{"name":"...","address":"...","contact_person":"...","phone":"...","fax":"...","email":"..."}},"certificate_holder":{{"name":"...","address":"..."}},"insurers":[{{"letter":"A","name":"...","naic":"..."}}],"additional_fields":{{"Human Readable Label":"value"}}}}

RULES:
1. Combine multi-line addresses into one string
2. Only include fields with data
3. Convert field names to Title Case labels in additional_fields (e.g. "OtherPolicy_Code_A" → "Other Policy Code A")
4. Return ONLY valid JSON"""
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse AI response to extract JSON.
        
        Args:
            response: Raw response from AI
            
        Returns:
            Parsed JSON dictionary
        """
        if not response:
            return {}
        
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


# Singleton instance
_acord_organizer = None


def get_acord_organizer() -> AcordOrganizer:
    """Get or create ACORD organizer singleton."""
    global _acord_organizer
    if _acord_organizer is None:
        _acord_organizer = AcordOrganizer()
    return _acord_organizer
