"""RAGAS-specific prompt enhancement and formatting"""

import logging
import re

logger = logging.getLogger(__name__)


class PromptEnhancer:
    """Enhance prompts for RAGAS evaluation metrics"""
    
    def enhance_prompt(self, prompt: str) -> str:
        """
        Enhance prompt with structured output instructions for RAGAS
        
        Args:
            prompt: Original prompt
            
        Returns:
            Enhanced prompt with JSON structure guidance
        """
        # Detect RAGAS metric type from prompt
        prompt_lower = prompt.lower()
        
        if "verdict" in prompt_lower and "statement" in prompt_lower:
            # Faithfulness evaluation
            return self._enhance_faithfulness_prompt(prompt)
        elif "question" in prompt_lower and "answer" in prompt_lower:
            if "relevan" in prompt_lower:  # Match both relevant and relevancy
                # Answer relevancy
                return self._enhance_answer_relevancy_prompt(prompt)
            elif "correct" in prompt_lower:
                # Answer correctness
                return self._enhance_answer_correctness_prompt(prompt)
        elif "context" in prompt_lower:
            if "precision" in prompt_lower:
                # Context precision
                return self._enhance_context_precision_prompt(prompt)
            elif "recall" in prompt_lower:
                # Context recall
                return self._enhance_context_recall_prompt(prompt)
        
        # Default: return original prompt
        return prompt
    
    def _enhance_faithfulness_prompt(self, prompt: str) -> str:
        """Enhance faithfulness evaluation prompt"""
        enhanced = prompt + """

IMPORTANT: Return your response as a valid JSON object with this exact structure:
{
    "statements": [
        {
            "statement": "The statement text here",
            "verdict": 1
        }
    ]
}

Where verdict is:
- 1 if the statement is clearly supported by the context
- 0 if the statement is not supported or contradicts the context

Example response:
{
    "statements": [
        {"statement": "RAG uses retrieval and generation", "verdict": 1},
        {"statement": "RAG was invented in 2025", "verdict": 0}
    ]
}"""
        return enhanced
    
    def _enhance_answer_relevancy_prompt(self, prompt: str) -> str:
        """Enhance answer relevancy evaluation prompt"""
        enhanced = prompt + """

IMPORTANT: Return a valid JSON response:
{
    "question": "Generated question based on the answer",
    "noncommittal": 0
}

Where noncommittal is 1 if the answer avoids the question, 0 otherwise.

Example: {"question": "What is RAG?", "noncommittal": 0}"""
        return enhanced
    
    def _enhance_context_precision_prompt(self, prompt: str) -> str:
        """Enhance context precision evaluation prompt"""
        enhanced = prompt + """

Return JSON: {"useful": [1, 0, 1, 0, 1]}
Where 1 means the context is useful, 0 means not useful.
The array length should match the number of contexts."""
        return enhanced
    
    def _enhance_context_recall_prompt(self, prompt: str) -> str:
        """Enhance context recall evaluation prompt"""
        enhanced = prompt + """

Return JSON with attributed statements:
{
    "statements": [
        {
            "statement": "Statement from ground truth",
            "attributed": 1,
            "reason": "Found in context"
        }
    ]
}

Where attributed is 1 if found in context, 0 otherwise."""
        return enhanced
    
    def _enhance_answer_correctness_prompt(self, prompt: str) -> str:
        """Enhance answer correctness evaluation prompt"""
        enhanced = prompt + """

Return JSON with correctness assessment:
{
    "TP": ["Correct statement 1", "Correct statement 2"],
    "FP": ["Incorrect statement"],
    "FN": ["Missing statement"]
}

Where:
- TP: True Positive statements (correct and present)
- FP: False Positive statements (incorrect but present)
- FN: False Negative statements (correct but missing)"""
        return enhanced