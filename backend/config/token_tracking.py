"""
Token usage tracking for LLM calls
Provides wrapper to track input, output, and total token usage
"""

from typing import Dict, List, Optional
from datetime import datetime
from backend.config.logging_config import token_logger, get_logger

logger = get_logger(__name__)


class TokenUsageTracker:
    """Track token usage across LLM calls"""
    
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_tokens = 0
        self.call_count = 0
        self.calls: List[Dict] = []
    
    def record_call(
        self,
        agent_name: str,
        input_tokens: int,
        output_tokens: int,
        model: str = "gemini-1.5-flash",
        prompt_type: str = "system+human"
    ) -> Dict:
        """
        Record an LLM call and track tokens
        
        Args:
            agent_name: Name of the agent/step calling the LLM
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name being used
            prompt_type: Type of prompt (e.g., system+human, reasoning, etc.)
        
        Returns:
            Dictionary with call information
        """
        total = input_tokens + output_tokens
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_tokens += total
        self.call_count += 1
        
        call_info = {
            "call_id": self.call_count,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_name,
            "model": model,
            "prompt_type": prompt_type,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total,
            "cumulative_total": self.total_tokens,
        }
        
        self.calls.append(call_info)
        
        # Log to token logger
        token_logger.info(
            f"Agent: {agent_name} | Model: {model} | "
            f"Input: {input_tokens:,} | Output: {output_tokens:,} | "
            f"Total: {total:,} | Cumulative: {self.total_tokens:,}"
        )
        
        return call_info
    
    def get_summary(self) -> Dict:
        """Get summary of all token usage"""
        if self.call_count == 0:
            return {
                "total_calls": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "average_tokens_per_call": 0,
            }
        
        return {
            "total_calls": self.call_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "average_tokens_per_call": round(self.total_tokens / self.call_count, 2),
            "calls": self.calls,
        }
    
    def log_summary(self):
        """Log a summary of token usage to files"""
        summary = self.get_summary()
        
        summary_msg = (
            f"=== TOKEN USAGE SUMMARY ===\n"
            f"Total Calls: {summary['total_calls']}\n"
            f"Total Input Tokens: {summary['total_input_tokens']:,}\n"
            f"Total Output Tokens: {summary['total_output_tokens']:,}\n"
            f"Total Tokens: {summary['total_tokens']:,}\n"
            f"Avg Tokens/Call: {summary['average_tokens_per_call']}"
        )
        
        token_logger.info(summary_msg)
        logger.info(summary_msg)
        
        return summary
    
    def reset(self):
        """Reset tracker for new session"""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_tokens = 0
        self.call_count = 0
        self.calls = []


# Global tracker instance
_global_tracker = TokenUsageTracker()


def get_token_tracker() -> TokenUsageTracker:
    """Get the global token tracker"""
    return _global_tracker


def track_llm_call(
    agent_name: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    model: str = "gemini-1.5-flash",
    prompt_type: str = "system+human"
) -> Dict:
    """
    Convenience function to track an LLM call globally
    
    Args:
        agent_name: Name of the agent calling the LLM
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name
        prompt_type: Type of prompt
    
    Returns:
        Call information dictionary
    """
    return _global_tracker.record_call(
        agent_name=agent_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=model,
        prompt_type=prompt_type
    )


def get_token_summary() -> Dict:
    """Get current token usage summary"""
    return _global_tracker.get_summary()


def log_token_summary():
    """Log and return token summary"""
    return _global_tracker.log_summary()


def reset_token_tracker():
    """Reset the global token tracker"""
    _global_tracker.reset()
    logger.info("Token tracker reset for new session")
