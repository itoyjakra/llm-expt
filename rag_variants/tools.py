"""A collection of tools for the rag_variants package."""

import os

from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv()
tavily_api_key = os.getenv("TAVILY_API_KEY")

web_search_tool = TavilySearchResults(k=3)
