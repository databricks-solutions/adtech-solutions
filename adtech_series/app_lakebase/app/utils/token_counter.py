"""
Token counting utilities for context window management.

Uses simple heuristics to estimate token usage without external API calls:
- 1 word ≈ 1.33 tokens (based on empirical observations)
- Handles text preprocessing and message aggregation
"""

import re
from typing import List, Dict, Any
from databricks.sdk.service.serving import ChatMessage


def estimate_tokens_from_text(text: str) -> int:
    """
    Estimate the number of tokens in a text using simple heuristics.
    
    Uses the rule: 1 word ≈ 1.33 tokens
    
    Args:
        text: Input text to analyze
        
    Returns:
        Estimated number of tokens
    """
    if not text or not isinstance(text, str):
        return 0
    
    # Simple word count using whitespace and basic punctuation as delimiters
    # This approximates tokenization patterns used by modern LLMs
    words = re.findall(r'\b\w+\b', text.lower())
    word_count = len(words)
    
    # Apply the 1 word ≈ 1.33 tokens heuristic
    estimated_tokens = int(word_count * 1.33)
    
    return estimated_tokens


def count_total_tokens(system_prompt: str, messages: List[ChatMessage]) -> int:
    """
    Count total tokens in system prompt and message list.
    
    Args:
        system_prompt: System prompt text
        messages: List of chat messages
        
    Returns:
        Total estimated token count
    """
    total_tokens = 0
    
    # Count system prompt tokens
    if system_prompt:
        total_tokens += estimate_tokens_from_text(system_prompt)
    
    # Count message tokens
    for message in messages:
        if message.content:
            total_tokens += estimate_tokens_from_text(str(message.content))
            # Add small overhead for message structure (role, formatting, etc.)
            total_tokens += 10
    
    return total_tokens


def count_total_tokens_from_dicts(message_dicts: List[Dict[str, Any]], system_prompt: str = "") -> int:
    """
    Count total tokens in message dictionaries, optionally including a system prompt.
    
    This variant works with message dictionaries (as used in the agent service)
    instead of ChatMessage objects.
    
    Args:
        message_dicts: List of message dictionaries with 'content' key
        system_prompt: Optional system prompt text to include in the count
        
    Returns:
        Total estimated token count
    """
    total_tokens = 0
    
    # Count system prompt tokens
    if system_prompt:
        total_tokens += estimate_tokens_from_text(system_prompt)
    
    # Count message tokens
    for message_dict in message_dicts:
        content = message_dict.get('content', '')
        if content:
            total_tokens += estimate_tokens_from_text(str(content))
            # Add small overhead for message structure (role, formatting, etc.)
            total_tokens += 10
    
    return total_tokens


def trim_messages_to_fit(messages: List[ChatMessage], system_prompt: str, max_tokens: int) -> List[ChatMessage]:
    """
    Trim messages list to fit within token limit while preserving recent messages.
    
    Removes messages from the beginning of the list until the total token count
    (including system prompt) fits within the specified limit.
    
    Args:
        messages: List of chat messages to trim
        system_prompt: System prompt text (counted in token limit)
        max_tokens: Maximum allowed tokens
        
    Returns:
        Trimmed list of messages that fits within token limit
    """
    if not messages:
        return messages
    
    # Start with all messages and progressively remove from the beginning
    for i in range(len(messages)):
        candidate_messages = messages[i:]
        total_tokens = count_total_tokens(system_prompt, candidate_messages)
        
        if total_tokens <= max_tokens:
            return candidate_messages
    
    # If even a single message exceeds the limit, return empty list
    return []


def trim_message_dicts_to_fit(message_dicts: List[Dict[str, Any]], max_tokens: int) -> List[Dict[str, Any]]:
    """
    Trim message dictionaries list to fit within token limit while preserving recent messages.
    
    This variant works with message dictionaries (as used in the agent service)
    instead of ChatMessage objects.
    
    Args:
        message_dicts: List of message dictionaries to trim
        max_tokens: Maximum allowed tokens
        
    Returns:
        Trimmed list of message dictionaries that fits within token limit
    """
    if not message_dicts:
        return message_dicts
    
    # Start with all messages and progressively remove from the beginning
    for i in range(len(message_dicts)):
        candidate_messages = message_dicts[i:]
        total_tokens = count_total_tokens_from_dicts(candidate_messages)
        
        if total_tokens <= max_tokens:
            return candidate_messages
    
    # If even a single message exceeds the limit, return empty list
    return []


def should_show_warning(current_tokens: int, max_tokens: int, warning_threshold: float = 0.9) -> bool:
    """
    Determine if a context warning should be shown based on current usage.
    
    Args:
        current_tokens: Current token count
        max_tokens: Maximum allowed tokens
        warning_threshold: Threshold (as fraction) for showing warning
        
    Returns:
        True if warning should be shown, False otherwise
    """
    if max_tokens <= 0:
        return False
    
    usage_ratio = current_tokens / max_tokens
    return usage_ratio >= warning_threshold


def get_context_usage_info(current_tokens: int, max_tokens: int) -> Dict[str, Any]:
    """
    Get comprehensive context usage information for UI display.
    
    Args:
        current_tokens: Current token count
        max_tokens: Maximum allowed tokens
        
    Returns:
        Dictionary with usage statistics and display information
    """
    if max_tokens <= 0:
        return {
            'current_tokens': current_tokens,
            'max_tokens': max_tokens,
            'usage_ratio': 0.0,
            'usage_percentage': 0,
            'show_warning': False,
            'status': 'unknown'
        }
    
    usage_ratio = current_tokens / max_tokens
    usage_percentage = int(usage_ratio * 100)
    
    # Determine status based on usage
    if usage_ratio < 0.5:
        status = 'low'
    elif usage_ratio < 0.8:
        status = 'medium'
    elif usage_ratio < 0.9:
        status = 'high'
    else:
        status = 'critical'
    
    return {
        'current_tokens': current_tokens,
        'max_tokens': max_tokens,
        'usage_ratio': usage_ratio,
        'usage_percentage': usage_percentage,
        'show_warning': usage_ratio >= 0.9,
        'status': status
    }