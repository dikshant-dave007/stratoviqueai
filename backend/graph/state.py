from typing import TypedDict, Optional, List, Annotated
from operator import add


class MarketingState(TypedDict):
    # --- Inputs ---
    company_name: str
    product_description: str
    target_audience: str
    budget: str
    goals: str
    industry: str

    # --- Agent Outputs ---
    market_research: Optional[str]
    audience_profile: Optional[str]
    channel_strategy: Optional[str]
    content_strategy: Optional[str]
    final_report: Optional[str]

    # --- Control Flow ---
    human_approved: Optional[bool]
    human_feedback: Optional[str]
    current_step: Optional[str]
    errors: Annotated[List[str], add]

    # --- Metadata ---
    session_id: Optional[str]
    created_at: Optional[str]
