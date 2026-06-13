import os
import httpx
from pydantic import BaseModel
from backend.config import settings


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class WebSearchTool:
    def __init__(self) -> None:
        self.api_key = settings.TAVILY_API_KEY
        self.base_url = "https://api.tavily.com/search"

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self.api_key or self.api_key == "your_key":
            return []

        try:
            response = httpx.post(
                self.base_url,
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "basic",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            raw_results = data.get("results", [])
            return [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    snippet=r.get("content", r.get("snippet", "")),
                )
                for r in raw_results
            ]
        except Exception:
            return []

    def format_for_prompt(self, results: list[SearchResult]) -> str:
        if not results:
            return ""
        lines = ["\nWeb search results:"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. [{r.title}]({r.url})\n{r.snippet}")
        return "\n".join(lines)
