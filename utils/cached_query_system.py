"""
Context caching system for repeated query patterns.
Leverages Gemini 2.5 Pro's context caching feature.
"""

import time
import hashlib
import json
import logging
from typing import Dict, Optional, Any
import google.generativeai as genai

logger = logging.getLogger(__name__)

class CachedQuerySystem:
    """Cached query system for repeated patterns."""
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize the caching system.
        
        Args:
            ttl (int): Cache time-to-live in seconds (default: 1 hour)
        """
        self.context_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = ttl
        self.model_name = "gemini-2.5-pro-preview-03-25"
        
    def get_schema_hash(self, schema: list) -> str:
        """Generate a hash for the database schema."""
        schema_str = json.dumps(schema, sort_keys=True)
        return hashlib.md5(schema_str.encode()).hexdigest()
    
    def get_cached_context(self, schema_hash: str) -> Optional[str]:
        """
        Retrieve cached context for schema.
        
        Args:
            schema_hash (str): Hash of the schema
            
        Returns:
            Optional[str]: Cached context if available and valid
        """
        cached = self.context_cache.get(schema_hash)
        if cached and cached["timestamp"] > time.time() - self.cache_ttl:
            logger.info(f"Cache hit for schema hash: {schema_hash}")
            return cached["context"]
        
        logger.info(f"Cache miss for schema hash: {schema_hash}")
        return None
    
    def cache_context(self, schema_hash: str, context: str) -> None:
        """
        Cache context for future use.
        
        Args:
            schema_hash (str): Hash of the schema
            context (str): Context to cache
        """
        self.context_cache[schema_hash] = {
            "context": context,
            "timestamp": time.time()
        }
        logger.info(f"Cached context for schema hash: {schema_hash}")
    
    def cleanup_stale_cache(self) -> None:
        """
        Remove stale cache entries.
        """
        current_time = time.time()
        stale_keys = [key for key, value in self.context_cache.items() if value["timestamp"] <= current_time - self.cache_ttl]
        for key in stale_keys:
            del self.context_cache[key]
            logger.info(f"Removed stale cache entry for schema hash: {key}")