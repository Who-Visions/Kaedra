# kaedra/story/tools - StoryEngine Tool Functions
from .notion import read_page_content, list_universe_pages, update_page_content, run_lore_automations
from .lore import read_local_lore, propose_canon_update
from .youtube import ingest_youtube_content
from .director import consult_director
from .engine_mode import set_engine_mode, adjust_emotion
from .timeline import clean_timeline_data
from .world import worldforge_from_youtube
from .loredb import (
    query_lore,
    search_lore,
    create_lore_block,
    update_lore_block,
    get_backlinks,
    lore_stats,
    sync_lore_to_cloud,
    query_bigquery_lore
)

ENGINE_TOOLS = [
    read_page_content, 
    list_universe_pages, 
    update_page_content,
    run_lore_automations,
    read_local_lore, 
    set_engine_mode, 
    consult_director,
    adjust_emotion, 
    clean_timeline_data, 
    propose_canon_update,
    ingest_youtube_content,
    worldforge_from_youtube,
    query_lore,
    search_lore,
    create_lore_block,
    update_lore_block,
    get_backlinks,
    lore_stats,
    sync_lore_to_cloud,
    query_bigquery_lore
]

__all__ = [
    "ENGINE_TOOLS",
    "read_page_content",
    "list_universe_pages",
    "update_page_content",
    "run_lore_automations",
    "read_local_lore",
    "propose_canon_update",
    "ingest_youtube_content",
    "consult_director",
    "set_engine_mode",
    "adjust_emotion",
    "clean_timeline_data",
    "worldforge_from_youtube",
    "query_lore",
    "search_lore",
    "create_lore_block",
    "update_lore_block",
    "get_backlinks",
    "lore_stats",
    "sync_lore_to_cloud",
    "query_bigquery_lore",
]
