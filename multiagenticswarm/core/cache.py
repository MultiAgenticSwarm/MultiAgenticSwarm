import sqlite3
import json
import hashlib
import logging

logging.basicConfig(level=logging.ERROR)

class GraphCache:
    """
    Persistent cache for compiled graphs using SQLite.
    Stores graphs as JSON strings. Tracks hits, misses, and errors.
    """

    def __init__(self, db_path="graph_cache.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Create tables for cache and stats if not exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                # Cache table
                c.execute("""
                    CREATE TABLE IF NOT EXISTS cache (
                        key TEXT PRIMARY KEY,
                        graph TEXT
                    )
                """)
                # Stats table
                c.execute("""
                    CREATE TABLE IF NOT EXISTS cache_stats (
                        key TEXT PRIMARY KEY,
                        hits INTEGER DEFAULT 0,
                        misses INTEGER DEFAULT 0,
                        errors INTEGER DEFAULT 0
                    )
                """)
                # Ensure global stats row exists
                c.execute("""
                    INSERT OR IGNORE INTO cache_stats(key, hits, misses, errors)
                    VALUES('global', 0, 0, 0)
                """)
                conn.commit()
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")

    def generate_key(self, parsed_prompt: dict) -> str:
        """Generate SHA256 hash key from parsed prompt."""
        prompt_str = json.dumps(parsed_prompt, sort_keys=True)
        return hashlib.sha256(prompt_str.encode("utf-8")).hexdigest()

    def _update_stats(self, field: str):
        """Increment a field in cache_stats."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(f"""
                    UPDATE cache_stats SET {field} = {field} + 1 WHERE key='global'
                """)
                conn.commit()
        except Exception as e:
            logging.error(f"Failed to update cache stats ({field}): {e}")

    def put(self, key: str, graph: dict):
        """Store compiled graph as JSON."""
        try:
            graph_json = json.dumps(graph)
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO cache(key, graph) VALUES (?, ?)", (key, graph_json))
                conn.commit()
            self._update_stats("hits")
        except Exception as e:
            logging.error(f"Failed to cache key {key}: {e}")
            self._update_stats("errors")

    def get(self, key: str):
        """Retrieve compiled graph as dict. Returns None if not found."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT graph FROM cache WHERE key=?", (key,))
                row = c.fetchone()
                if row:
                    self._update_stats("hits")
                    return json.loads(row[0])
                else:
                    self._update_stats("misses")
                    return None
        except Exception as e:
            logging.error(f"Failed to retrieve key {key}: {e}")
            self._update_stats("errors")
            return None

    def stats(self):
        """Return cache stats as dict."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT hits, misses, errors FROM cache_stats WHERE key='global'")
                row = c.fetchone()
                if row:
                    return {"hits": row[0], "misses": row[1], "errors": row[2]}
        except Exception as e:
            logging.error(f"Failed to read cache stats: {e}")
        return {"hits": 0, "misses": 0, "errors": 0}
