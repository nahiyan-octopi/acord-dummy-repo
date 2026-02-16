"""
OpenAI API Service for GPT-4o
"""
import json
from typing import Optional, Dict, Any
from openai import OpenAI
from app.config.config import Config


class OpenAIService:
    """Service for interacting with OpenAI API (GPT-4o)"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI service
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
        """
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.model = Config.OPENAI_MODEL
        self.temperature = Config.OPENAI_TEMPERATURE
        self.max_tokens = Config.OPENAI_MAX_TOKENS
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def chat_completion(
        self,
        messages: list,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using GPT-4o
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens
            response_format: Optional response format (e.g., {"type": "json_object"})
            
        Returns:
            Response content and metadata
        """
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
            }
            
            if response_format:
                kwargs["response_format"] = response_format
            
            response = self.client.chat.completions.create(**kwargs)
            
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to OpenAI API
        
        Returns:
            Dictionary with success status and details
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Say 'Connection successful'"}
                ],
                max_tokens=50,
                temperature=0
            )
            
            return {
                "success": True,
                "message": "Connected to OpenAI API",
                "model": self.model
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to connect: {str(e)}"
            }
    
    def extract_universal_data(self, document_text: str) -> Dict[str, Any]:
        """
        Extract structured data from any document using GPT-4o.
        
        Args:
            document_text: Text extracted from PDF
        
        Returns:
            Dictionary with extracted data
        """
        prompt = f"""You are an expert data extraction specialist. Your task is to extract ALL meaningful data from ANY type of document and organize it into logical sections.

DOCUMENT TEXT:
{document_text}

STEP 1: First, identify the document type (Certificate, Resume, Invoice, Contract, Form, Report, Letter, etc.)

STEP 2: Extract ALL data and organize into SECTIONS appropriate for that document type.

STEP 3: If the document is a certificate, identify the certificate type.
Examples of certificate type: Kosher, Halal, Non-GMO, Organic, etc.

STEP 4: If the document is a certificate, identify the certificate name and relevant details.


DOCUMENT-TYPE SPECIFIC SECTIONS:
- For RESUME/CV: Contact Information, Summary, Skills, Experience, Education, Projects, Certifications
- For INVOICE: Vendor Details, Customer Details, Invoice Details, Line Items, Payment Information, Totals
- For FORM: Form Information, Applicant Details, and form-specific sections based on content
- For CONTRACT: Parties, Terms, Dates, Obligations, Signatures
- For REPORT: Title, Author, Date, Executive Summary, Findings, Recommendations
- For Certificate: Certificate Name, Issuer, Recipient, Issue Date, Expiry Date, Details

Return JSON with this EXACT structure:
{{
    "document_type": "The identified document type",
    "certificate_type": "Certificate subtype if document_type is Certificate, otherwise null",
    "certificate_name": "If applicable, the name of the certificate",
    "sections": {{
        "Section Name 1": {{
            "field_name": "value",
            "another_field": "value"
        }},
        "Section Name 2": {{
            "field_name": "value",
            "nested_list": [
                {{"item_field": "value1"}},
                {{"item_field": "value2"}}
            ]
        }}
    }}
}}

CRITICAL RULES:
1. Extract ALL data completely - do not skip any information
2. Each piece of information must appear ONLY ONCE - NO DUPLICATES
3. Group related information together in logical sections
4. Use clean, human-readable field names
5. For lists (skills, experience), use arrays within the appropriate section
6. If document_type is not Certificate, set certificate_type to null
7. Return ONLY valid JSON"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            extracted_data = self._parse_json_response(response_text)
            
            return {
                "success": True,
                "data": extracted_data,
                "raw_response": response_text,
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Extraction failed: {str(e)}"
            }
    
    @staticmethod
    def _parse_json_response(response_text: str) -> Dict[str, Any]:
        """Parse JSON from response text, handling markdown code blocks"""
        # Try direct JSON parsing first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            if json_end > json_start:
                json_str = response_text[json_start:json_end].strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
        
        # Try to extract any JSON object
        if "{" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_end > json_start:
                json_str = response_text[json_start:json_end]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
        
        # If all else fails, return the text as is
        return {"extracted_text": response_text}


# Singleton instance
_openai_service = None


def get_openai_service() -> OpenAIService:
    """Get or create OpenAI service singleton"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service

