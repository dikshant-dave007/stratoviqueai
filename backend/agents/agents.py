from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.messages import HumanMessage, SystemMessage
from backend.graph.state import MarketingState
from backend.prompts.prompts import (
    RESEARCH_AGENT_PROMPT,
    AUDIENCE_AGENT_PROMPT,
    CHANNEL_AGENT_PROMPT,
    CONTENT_AGENT_PROMPT,
    REPORT_AGENT_PROMPT,
)
from backend.config import agents_logger, search_logger, track_llm_call
import os

def get_llm():
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    agents_logger.debug(f"Initializing LLM with model: {model}")
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=0.4,
        google_api_key=os.getenv("GEMINI_API_KEY"),
        convert_system_message_to_human=True,
    )

def run_search(query: str) -> str:
    """Run a single search query using Serper and return results as string."""
    try:
        search_logger.debug(f"Executing search query: {query}")
        search = GoogleSerperAPIWrapper(
            serper_api_key=os.getenv("SERPER_API_KEY"),
            k=5,
        )
        result = search.run(query)
        search_logger.info(f"Search completed successfully. Query: {query}, Result length: {len(result)} chars")
        return result
    except Exception as e:
        search_logger.error(f"Search failed for query '{query}': {str(e)}")
        return f"Search unavailable: {str(e)}"


# ─── Agent 1: Market Research ────────────────────────────────────────────────

def research_agent(state: MarketingState) -> MarketingState:
    """Conducts competitor analysis and market research."""
    agent_name = "research"
    session_id = state.get("session_id", "unknown")
    agents_logger.info(f"[Session {session_id}] Starting {agent_name} agent")
    
    try:
        llm = get_llm()
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        # Run targeted searches via Serper
        search_queries = [
            f"{state['company_name']} {state['industry']} competitors 2025",
            f"{state['industry']} marketing trends 2025",
            f"{state['product_description']} target market size",
        ]

        agents_logger.debug(f"[Session {session_id}] Executing {len(search_queries)} search queries")
        search_results = []
        for i, query in enumerate(search_queries, 1):
            agents_logger.debug(f"[Session {session_id}] Search query {i}/{len(search_queries)}: {query}")
            result = run_search(query)
            search_results.append(f"Query: {query}\n{result}")

        combined_search = "\n\n---\n\n".join(search_results)
        agents_logger.debug(f"[Session {session_id}] Searches complete, combined result length: {len(combined_search)} chars")

        prompt = RESEARCH_AGENT_PROMPT.format(
            company_name=state["company_name"],
            product_description=state["product_description"],
            industry=state["industry"],
            target_audience=state["target_audience"],
        )

        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=f"Here is current market data from web research:\n\n{combined_search}\n\nNow write the full market research report."),
        ]

        # Calculate approximate token counts
        prompt_chars = len(prompt) + len(combined_search)
        estimated_input_tokens = int(prompt_chars / 4)  # Rough estimate: 4 chars = 1 token

        agents_logger.debug(f"[Session {session_id}] Invoking LLM for {agent_name} agent")
        response = llm.invoke(messages)
        
        # Extract token usage from response if available
        output_tokens = len(response.content) // 4
        if hasattr(response, 'response_metadata') and 'usage_metadata' in response.response_metadata:
            usage = response.response_metadata['usage_metadata']
            estimated_input_tokens = usage.get('input_tokens', estimated_input_tokens)
            output_tokens = usage.get('output_tokens', output_tokens)
        
        # Track tokens
        track_llm_call(
            agent_name=agent_name,
            input_tokens=estimated_input_tokens,
            output_tokens=output_tokens,
            model=model,
            prompt_type="system+human"
        )
        
        agents_logger.info(
            f"[Session {session_id}] {agent_name} agent completed | "
            f"Input tokens: {estimated_input_tokens:,} | "
            f"Output tokens: {output_tokens:,} | "
            f"Output length: {len(response.content)} chars"
        )
        
        return {**state, "market_research": response.content, "current_step": "audience"}
    
    except Exception as e:
        agents_logger.error(f"[Session {session_id}] {agent_name} agent failed: {str(e)}", exc_info=True)
        raise


# ─── Agent 2: Audience Intelligence ──────────────────────────────────────────

def audience_agent(state: MarketingState) -> MarketingState:
    """Builds deep ICP and psychographic profiles."""
    agent_name = "audience"
    session_id = state.get("session_id", "unknown")
    agents_logger.info(f"[Session {session_id}] Starting {agent_name} agent")
    
    try:
        llm = get_llm()
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        prompt = AUDIENCE_AGENT_PROMPT.format(
            market_research=state.get("market_research", ""),
            company_name=state["company_name"],
            product_description=state["product_description"],
            target_audience=state["target_audience"],
            goals=state["goals"],
        )

        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content="Build the complete audience intelligence profile now."),
        ]

        # Calculate approximate token counts
        prompt_chars = len(prompt) + len(state.get("market_research", ""))
        estimated_input_tokens = int(prompt_chars / 4)

        agents_logger.debug(f"[Session {session_id}] Invoking LLM for {agent_name} agent")
        response = llm.invoke(messages)
        
        # Extract token usage from response if available
        output_tokens = len(response.content) // 4
        if hasattr(response, 'response_metadata') and 'usage_metadata' in response.response_metadata:
            usage = response.response_metadata['usage_metadata']
            estimated_input_tokens = usage.get('input_tokens', estimated_input_tokens)
            output_tokens = usage.get('output_tokens', output_tokens)
        
        # Track tokens
        track_llm_call(
            agent_name=agent_name,
            input_tokens=estimated_input_tokens,
            output_tokens=output_tokens,
            model=model,
            prompt_type="system+human"
        )
        
        agents_logger.info(
            f"[Session {session_id}] {agent_name} agent completed | "
            f"Input tokens: {estimated_input_tokens:,} | "
            f"Output tokens: {output_tokens:,} | "
            f"Output length: {len(response.content)} chars"
        )
        
        return {**state, "audience_profile": response.content, "current_step": "channel"}
    
    except Exception as e:
        agents_logger.error(f"[Session {session_id}] {agent_name} agent failed: {str(e)}", exc_info=True)
        raise


# ─── Agent 3: Channel Strategy ────────────────────────────────────────────────

def channel_agent(state: MarketingState) -> MarketingState:
    """Recommends channels, budget allocation, and KPIs."""
    agent_name = "channel"
    session_id = state.get("session_id", "unknown")
    agents_logger.info(f"[Session {session_id}] Starting {agent_name} agent")
    
    try:
        llm = get_llm()
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        prompt = CHANNEL_AGENT_PROMPT.format(
            market_research=state.get("market_research", ""),
            audience_profile=state.get("audience_profile", ""),
            budget=state["budget"],
            goals=state["goals"],
        )

        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content="Provide the full channel strategy and budget breakdown now."),
        ]

        # Calculate approximate token counts
        prompt_chars = len(prompt) + len(state.get("market_research", "")) + len(state.get("audience_profile", ""))
        estimated_input_tokens = int(prompt_chars / 4)

        agents_logger.debug(f"[Session {session_id}] Invoking LLM for {agent_name} agent")
        response = llm.invoke(messages)
        
        # Extract token usage from response if available
        output_tokens = len(response.content) // 4
        if hasattr(response, 'response_metadata') and 'usage_metadata' in response.response_metadata:
            usage = response.response_metadata['usage_metadata']
            estimated_input_tokens = usage.get('input_tokens', estimated_input_tokens)
            output_tokens = usage.get('output_tokens', output_tokens)
        
        # Track tokens
        track_llm_call(
            agent_name=agent_name,
            input_tokens=estimated_input_tokens,
            output_tokens=output_tokens,
            model=model,
            prompt_type="system+human"
        )
        
        agents_logger.info(
            f"[Session {session_id}] {agent_name} agent completed | "
            f"Input tokens: {estimated_input_tokens:,} | "
            f"Output tokens: {output_tokens:,} | "
            f"Output length: {len(response.content)} chars"
        )
        
        return {**state, "channel_strategy": response.content, "current_step": "content"}
    
    except Exception as e:
        agents_logger.error(f"[Session {session_id}] {agent_name} agent failed: {str(e)}", exc_info=True)
        raise


# ─── Agent 4: Content Strategy ───────────────────────────────────────────────

def content_agent(state: MarketingState) -> MarketingState:
    """Creates messaging framework, campaigns, and content calendar."""
    agent_name = "content"
    session_id = state.get("session_id", "unknown")
    agents_logger.info(f"[Session {session_id}] Starting {agent_name} agent")
    
    try:
        llm = get_llm()
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        prompt = CONTENT_AGENT_PROMPT.format(
            channel_strategy=state.get("channel_strategy", ""),
            audience_profile=state.get("audience_profile", ""),
            company_name=state["company_name"],
            product_description=state["product_description"],
        )

        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content="Deliver the complete content strategy and messaging framework now."),
        ]

        # Calculate approximate token counts
        prompt_chars = len(prompt) + len(state.get("channel_strategy", "")) + len(state.get("audience_profile", ""))
        estimated_input_tokens = int(prompt_chars / 4)

        agents_logger.debug(f"[Session {session_id}] Invoking LLM for {agent_name} agent")
        response = llm.invoke(messages)
        
        # Extract token usage from response if available
        output_tokens = len(response.content) // 4
        if hasattr(response, 'response_metadata') and 'usage_metadata' in response.response_metadata:
            usage = response.response_metadata['usage_metadata']
            estimated_input_tokens = usage.get('input_tokens', estimated_input_tokens)
            output_tokens = usage.get('output_tokens', output_tokens)
        
        # Track tokens
        track_llm_call(
            agent_name=agent_name,
            input_tokens=estimated_input_tokens,
            output_tokens=output_tokens,
            model=model,
            prompt_type="system+human"
        )
        
        agents_logger.info(
            f"[Session {session_id}] {agent_name} agent completed | "
            f"Input tokens: {estimated_input_tokens:,} | "
            f"Output tokens: {output_tokens:,} | "
            f"Output length: {len(response.content)} chars"
        )
        
        return {**state, "content_strategy": response.content, "current_step": "human_review"}
    
    except Exception as e:
        agents_logger.error(f"[Session {session_id}] {agent_name} agent failed: {str(e)}", exc_info=True)
        raise


# ─── Agent 5: Report Generation ──────────────────────────────────────────────

def report_agent(state: MarketingState) -> MarketingState:
    """Synthesizes everything into the final executive report."""
    agent_name = "report"
    session_id = state.get("session_id", "unknown")
    agents_logger.info(f"[Session {session_id}] Starting {agent_name} agent")
    
    try:
        llm = get_llm()
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        prompt = REPORT_AGENT_PROMPT.format(
            market_research=state.get("market_research", ""),
            audience_profile=state.get("audience_profile", ""),
            channel_strategy=state.get("channel_strategy", ""),
            content_strategy=state.get("content_strategy", ""),
            human_feedback=state.get("human_feedback", "No additional feedback provided."),
            company_name=state["company_name"],
            product_description=state["product_description"],
            budget=state["budget"],
            goals=state["goals"],
        )

        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the complete final marketing strategy report now."),
        ]

        # Calculate approximate token counts
        prompt_chars = (len(prompt) + len(state.get("market_research", "")) + 
                       len(state.get("audience_profile", "")) + len(state.get("channel_strategy", "")) +
                       len(state.get("content_strategy", "")))
        estimated_input_tokens = int(prompt_chars / 4)

        agents_logger.debug(f"[Session {session_id}] Invoking LLM for {agent_name} agent")
        response = llm.invoke(messages)
        
        # Extract token usage from response if available
        output_tokens = len(response.content) // 4
        if hasattr(response, 'response_metadata') and 'usage_metadata' in response.response_metadata:
            usage = response.response_metadata['usage_metadata']
            estimated_input_tokens = usage.get('input_tokens', estimated_input_tokens)
            output_tokens = usage.get('output_tokens', output_tokens)
        
        # Track tokens
        track_llm_call(
            agent_name=agent_name,
            input_tokens=estimated_input_tokens,
            output_tokens=output_tokens,
            model=model,
            prompt_type="system+human"
        )
        
        agents_logger.info(
            f"[Session {session_id}] {agent_name} agent completed | "
            f"Input tokens: {estimated_input_tokens:,} | "
            f"Output tokens: {output_tokens:,} | "
            f"Output length: {len(response.content)} chars"
        )
        
        return {**state, "final_report": response.content, "current_step": "complete"}
    
    except Exception as e:
        agents_logger.error(f"[Session {session_id}] {agent_name} agent failed: {str(e)}", exc_info=True)
        raise
