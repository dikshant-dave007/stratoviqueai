"""
StratoviqueAI — Serper Search Tool
Replaces CrewAI's SerperDevTool with a clean LangChain wrapper.
"""

import os
from langchain_community.utilities import GoogleSerperAPIWrapper
from backend.config import search_logger


def run_search(query: str) -> str:
    """Execute a single search query via Serper and return results as string."""
    try:
        search_logger.debug(f"Executing search query: {query}")
        search = GoogleSerperAPIWrapper(
            serper_api_key=os.getenv("SERPER_API_KEY"),
            k=5,
        )
        result = search.run(query)
        search_logger.info(f"Search completed successfully | Query: {query} | Result length: {len(result)} chars")
        return result
    except Exception as e:
        search_logger.error(f"Search failed for query '{query}': {str(e)}")
        return f"[Search unavailable: {str(e)}]"


def run_multiple_searches(queries: list[str]) -> str:
    """Run multiple queries and combine results with separators."""
    search_logger.debug(f"Running {len(queries)} search queries")
    results = []
    for i, query in enumerate(queries, 1):
        search_logger.debug(f"Query {i}/{len(queries)}: {query}")
        result = run_search(query)
        results.append(f"🔍 Query: {query}\n{result}")
    
    combined = "\n\n---\n\n".join(results)
    search_logger.info(f"Multiple search batch completed | Queries: {len(queries)} | Total result length: {len(combined)} chars")
    return combined
