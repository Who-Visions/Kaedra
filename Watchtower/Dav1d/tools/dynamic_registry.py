"""
Dynamic Tool Registry for Dav1d
Implements lazy-loading and search-based tool discovery
Similar to Claude's Tool Search Tool pattern
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import re
from collections import Counter
import math


@dataclass
class ToolDefinition:
    """Represents a tool that can be called by Gemini."""
    name: str
    description: str
    function: Callable
    parameters: dict
    examples: Optional[List[dict]] = None
    defer_loading: bool = False
    category: Optional[str] = None


class BM25Search:
    """
    BM25 (Best Matching 25) search algorithm for tool discovery.
    More sophisticated than simple regex matching.
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs = {}
        self.doc_lengths = {}
        self.avg_doc_length = 0
        self.documents = {}
        
    def index_documents(self, documents: Dict[str, str]):
        """Index tool names and descriptions for search."""
        self.documents = documents
        
        # Calculate document frequencies
        all_terms = set()
        for doc_id, text in documents.items():
            terms = self._tokenize(text)
            self.doc_lengths[doc_id] = len(terms)
            
            for term in set(terms):
                if term not in self.doc_freqs:
                    self.doc_freqs[term] = 0
                self.doc_freqs[term] += 1
                all_terms.add(term)
        
        # Calculate average document length
        if documents:
            self.avg_doc_length = sum(self.doc_lengths.values()) / len(documents)
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for search."""
        # Simple word tokenization with lowercasing
        text = text.lower()
        # Split on non-alphanumeric, keep underscores for function names
        tokens = re.findall(r'[a-z0-9_]+', text)
        return tokens
    
    def _idf(self, term: str) -> float:
        """Calculate Inverse Document Frequency."""
        n_docs = len(self.documents)
        df = self.doc_freqs.get(term, 0)
        if df == 0:
            return 0
        return math.log((n_docs - df + 0.5) / (df + 0.5) + 1)
    
    def search(self, query: str, limit: int = 5) -> List[tuple]:
        """
        Search for documents matching the query.
        Returns list of (doc_id, score) tuples.
        """
        query_terms = self._tokenize(query)
        scores = {}
        
        for doc_id, doc_text in self.documents.items():
            doc_terms = self._tokenize(doc_text)
            term_freqs = Counter(doc_terms)
            doc_length = self.doc_lengths[doc_id]
            
            score = 0
            for term in query_terms:
                if term in term_freqs:
                    tf = term_freqs[term]
                    idf = self._idf(term)
                    
                    # BM25 formula
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (
                        1 - self.b + self.b * (doc_length / self.avg_doc_length)
                    )
                    score += idf * (numerator / denominator)
            
            if score > 0:
                scores[doc_id] = score
        
        # Sort by score and return top results
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:limit]


class DynamicToolRegistry:
    """
    Manages tool discovery and lazy loading.
    
    Key features:
    - On-demand tool loading (save tokens)
    - BM25 semantic search for tool discovery
    - Category-based organization
    - Always-loaded core tools
    """
    
    def __init__(self):
        self.all_tools: Dict[str, ToolDefinition] = {}
        self.search_index = BM25Search()
        self.core_tools: set = set()  # Always loaded
        self.loaded_tools: set = set()  # Currently in context
        
    def register_tool(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: dict,
        examples: Optional[List[dict]] = None,
        defer_loading: bool = True,
        is_core: bool = False,
        category: Optional[str] = None
    ):
        """Register a tool in the registry."""
        tool = ToolDefinition(
            name=name,
            description=description,
            function=function,
            parameters=parameters,
            examples=examples,
            defer_loading=defer_loading,
            category=category
        )
        
        self.all_tools[name] = tool
        
        if is_core:
            self.core_tools.add(name)
            self.loaded_tools.add(name)
    
    def build_index(self):
        """Build search index from all registered tools."""
        documents = {}
        for name, tool in self.all_tools.items():
            # Combine name, description, and category for search
            search_text = f"{name} {tool.description}"
            if tool.category:
                search_text += f" {tool.category}"
            documents[name] = search_text
        
        self.search_index.index_documents(documents)
    
    def search_tools(self, query: str, limit: int = 5) -> List[str]:
        """
        Search for tools matching the query.
        Returns list of tool names.
        """
        results = self.search_index.search(query, limit)
        return [tool_name for tool_name, score in results]
    
    def get_tools_for_request(
        self,
        user_message: str,
        max_tools: int = 10
    ) -> List[ToolDefinition]:
        """
        Analyze user message and return relevant tools.
        
        Strategy:
        1. Always include core tools
        2. Search for relevant tools based on message
        3. Return combined set up to max_tools
        """
        # Start with core tools (always loaded)
        relevant_tools = [
            self.all_tools[name] for name in self.core_tools
        ]
        
        # Search for additional relevant tools
        search_results = self.search_tools(user_message, limit=max_tools)
        
        for tool_name in search_results:
            if tool_name not in self.core_tools:
                tool = self.all_tools[tool_name]
                if not tool.defer_loading or len(relevant_tools) < max_tools:
                    relevant_tools.append(tool)
                    self.loaded_tools.add(tool_name)
        
        return relevant_tools[:max_tools]
    
    def get_tool_by_name(self, name: str) -> Optional[ToolDefinition]:
        """Get a specific tool by name."""
        return self.all_tools.get(name)
    
    def get_all_categories(self) -> List[str]:
        """Get all unique tool categories."""
        categories = set()
        for tool in self.all_tools.values():
            if tool.category:
                categories.add(tool.category)
        return sorted(list(categories))
    
    def get_tools_by_category(self, category: str) -> List[ToolDefinition]:
        """Get all tools in a specific category."""
        return [
            tool for tool in self.all_tools.values()
            if tool.category == category
        ]
    
    def get_statistics(self) -> dict:
        """Get registry statistics for monitoring."""
        return {
            "total_tools": len(self.all_tools),
            "core_tools": len(self.core_tools),
            "loaded_tools": len(self.loaded_tools),
            "deferred_tools": sum(
                1 for t in self.all_tools.values() if t.defer_loading
            ),
            "categories": len(self.get_all_categories()),
        }
    
    def reset_loaded_tools(self):
        """Reset loaded tools to core only (cleanup between requests)."""
        self.loaded_tools = set(self.core_tools)


# Global registry instance
tool_registry = DynamicToolRegistry()


def register_core_tool(name: str, description: str, function: Callable, parameters: dict, **kwargs):
    """Convenience function to register a core tool (always loaded)."""
    tool_registry.register_tool(
        name=name,
        description=description,
        function=function,
        parameters=parameters,
        defer_loading=False,
        is_core=True,
        **kwargs
    )


def register_deferred_tool(name: str, description: str, function: Callable, parameters: dict, **kwargs):
    """Convenience function to register a deferred tool (loaded on-demand)."""
    tool_registry.register_tool(
        name=name,
        description=description,
        function=function,
        parameters=parameters,
        defer_loading=True,
        is_core=False,
        **kwargs
    )
