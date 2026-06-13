SEARCH_ROUTER_PROMPT = """\
Does this message require current, real-time, or recent information to answer well?
Answer with JSON only: {{"needs_search": true/false, "search_query": "query if needed"}}

Messages that need search: news, current prices, recent events, "who won", "latest", "today"
Messages that don't: general knowledge, coding help, math, creative writing, memory-based questions

Message: {message}
Respond with JSON only.
"""
