"""
Example of an NLP-aware detector that uses enriched context.
This detector can work with both simple text and NLP-enriched context.
"""
from typing import Dict, Any, Optional


def detect(text: str) -> bool:
    """
    Basic text-based detection (backward compatible).
    
    Args:
        text: The text to analyze
        
    Returns:
        bool: True if pattern detected, False otherwise
    """
    # Simple keyword-based detection
    keywords = ["aber", "jedoch", "trotzdem"]
    return any(keyword in text.lower() for keyword in keywords)


def detect_with_context(context) -> Optional[Dict[str, Any]]:
    """
    Enhanced detection using NLP-enriched context.
    
    Args:
        context: AnalysisContext object with NLP annotations
        
    Returns:
        Optional[Dict]: Detection result with confidence and details
    """
    if not context.tokens:
        # Fallback to simple detection if no tokens
        if detect(context.text):
            return {"confidence": 0.5, "details": {"method": "fallback"}}
        return None
    
    # Look for adversative conjunctions with context
    adversative_conjunctions = {"aber", "jedoch", "trotzdem", "dennoch", "allerdings"}
    
    for i, token in enumerate(context.tokens):
        if token.lower() in adversative_conjunctions:
            # Found adversative conjunction, analyze context
            
            # Check if it's between two contrasting statements
            before_tokens = context.tokens[:i] if i > 0 else []
            after_tokens = context.tokens[i+1:] if i < len(context.tokens) - 1 else []
            
            # Simple heuristic: if we have tokens before and after, it's likely contrasting
            if before_tokens and after_tokens:
                confidence = 0.9
                
                # Adjust confidence based on position
                # Conjunctions in the middle of sentence are stronger indicators
                position_ratio = i / len(context.tokens)
                if 0.3 < position_ratio < 0.7:
                    confidence = 0.95
                
                return {
                    "confidence": confidence,
                    "details": {
                        "trigger_token": token,
                        "position": i,
                        "total_tokens": len(context.tokens),
                        "context_before": " ".join(before_tokens[-5:]),  # Last 5 tokens before
                        "context_after": " ".join(after_tokens[:5]),     # First 5 tokens after
                        "method": "nlp_enhanced"
                    }
                }
    
    return None


def analyze_sentiment_contrast(context) -> Optional[Dict[str, Any]]:
    """
    Advanced analysis that could use sentiment from NLP.
    This is a placeholder for future enhancement when sentiment analysis is available.
    
    Args:
        context: AnalysisContext with potential sentiment annotations
        
    Returns:
        Optional[Dict]: Analysis results
    """
    # This would use sentiment analysis when available
    # For now, just demonstrate the pattern
    
    if hasattr(context, 'sentiment_scores') and context.sentiment_scores:
        # Future: analyze sentiment shifts around conjunctions
        pass
    
    # Fallback to basic detection
    return detect_with_context(context)


# Example usage patterns:
if __name__ == "__main__":
    # Test with simple text
    text1 = "Ich liebe dich, aber ich brauche Zeit für mich."
    print(f"Simple detection: {detect(text1)}")
    
    # Test with mock context
    class MockContext:
        def __init__(self, text, tokens):
            self.text = text
            self.tokens = tokens
    
    context = MockContext(
        text="Ich liebe dich, aber ich brauche Zeit für mich.",
        tokens=["Ich", "liebe", "dich", ",", "aber", "ich", "brauche", "Zeit", "für", "mich", "."]
    )
    
    result = detect_with_context(context)
    print(f"Context-aware detection: {result}")