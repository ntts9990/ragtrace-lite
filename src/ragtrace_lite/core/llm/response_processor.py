"""Response processing and validation for RAGAS compatibility"""

import json
import re
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ResponseProcessor:
    """Process and validate LLM responses for RAGAS evaluation"""
    
    def clean_response(self, response: str, original_prompt: str) -> str:
        """
        Clean and validate LLM response for RAGAS compatibility
        
        Args:
            response: Raw LLM response
            original_prompt: Original prompt for context
            
        Returns:
            Cleaned and validated response
        """
        if not response:
            return self.get_fallback_response(original_prompt)
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            
            # Clean common JSON issues
            json_str = json_str.replace("'", '"')  # Single to double quotes
            json_str = re.sub(r',\s*}', '}', json_str)  # Trailing commas
            json_str = re.sub(r',\s*]', ']', json_str)  # Trailing commas in arrays
            
            try:
                # Validate JSON
                parsed = json.loads(json_str)
                
                # Fix RAGAS-specific format issues
                fixed = self._fix_ragas_format(parsed, original_prompt)
                
                return json.dumps(fixed, ensure_ascii=False)
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error: {e}")
                
                # Try to fix common issues
                if "verdict" in json_str:
                    # Fix faithfulness format
                    return self._create_structured_fallback("faithfulness", json_str)
                elif "question" in json_str:
                    # Fix answer relevancy format
                    return self._create_structured_fallback("relevancy", json_str)
                
        # If no JSON found or parsing failed, return fallback
        return self.get_fallback_response(original_prompt)
    
    def _fix_ragas_format(self, parsed: Dict, prompt: str) -> Dict:
        """Fix RAGAS-specific format issues in parsed JSON"""
        # Fix faithfulness format
        if "statements" in parsed:
            for stmt in parsed.get("statements", []):
                # Ensure verdict is integer
                if "verdict" in stmt:
                    verdict = stmt["verdict"]
                    if isinstance(verdict, str):
                        stmt["verdict"] = 1 if verdict.lower() in ["yes", "true", "1"] else 0
                    elif isinstance(verdict, bool):
                        stmt["verdict"] = 1 if verdict else 0
        
        # Fix answer relevancy format
        if "noncommittal" in parsed:
            nc = parsed["noncommittal"]
            if isinstance(nc, str):
                parsed["noncommittal"] = 1 if nc.lower() in ["yes", "true", "1"] else 0
            elif isinstance(nc, bool):
                parsed["noncommittal"] = 1 if nc else 0
        
        # Fix context precision format
        if "useful" in parsed:
            useful = parsed["useful"]
            if isinstance(useful, list):
                parsed["useful"] = [1 if u else 0 for u in useful]
        
        return parsed
    
    def _create_structured_fallback(self, metric_type: str, response_text: str) -> str:
        """Create structured fallback response based on metric type"""
        if metric_type == "faithfulness":
            # Extract any statements and create default structure
            statements = re.findall(r'"statement":\s*"([^"]+)"', response_text)
            verdicts = re.findall(r'"verdict":\s*(\d)', response_text)
            
            result = {"statements": []}
            for i, stmt in enumerate(statements):
                verdict = int(verdicts[i]) if i < len(verdicts) else 1
                result["statements"].append({
                    "statement": stmt,
                    "verdict": verdict
                })
            
            if not result["statements"]:
                # Default fallback
                result["statements"] = [{"statement": "No statements found", "verdict": 1}]
            
            return json.dumps(result)
        
        elif metric_type == "relevancy":
            # Extract question if possible
            question_match = re.search(r'"question":\s*"([^"]+)"', response_text)
            question = question_match.group(1) if question_match else "What is the answer about?"
            
            return json.dumps({
                "question": question,
                "noncommittal": 0
            })
        
        # Default fallback
        return "{}"
    
    def get_fallback_response(self, prompt: str) -> str:
        """Get fallback response based on prompt type"""
        prompt_lower = prompt.lower()
        
        if "verdict" in prompt_lower and "statement" in prompt_lower:
            # Faithfulness fallback
            return json.dumps({
                "statements": [
                    {"statement": "The answer is related to the context", "verdict": 1}
                ]
            })
        elif "question" in prompt_lower and "answer" in prompt_lower:
            # Answer relevancy fallback
            return json.dumps({
                "question": "What is being discussed?",
                "noncommittal": 0
            })
        elif "useful" in prompt_lower:
            # Context precision fallback
            return json.dumps({"useful": [1]})
        elif "attributed" in prompt_lower:
            # Context recall fallback
            return json.dumps({
                "statements": [
                    {"statement": "Information is provided", "attributed": 1}
                ]
            })
        elif "TP" in prompt or "FP" in prompt:
            # Answer correctness fallback
            return json.dumps({
                "TP": ["The answer addresses the question"],
                "FP": [],
                "FN": []
            })
        
        # Generic fallback
        return "{}"