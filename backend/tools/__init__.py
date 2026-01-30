"""
Tools module for FionaFast agent.

Each tool is defined in its own file and exports:
- get_tool_definition(): Returns the tool definition for OpenAI
- execute(arguments): Executes the tool with given arguments
"""

from .crawl_property_website import (
    get_tool_definition as get_crawl_property_website_definition,
    execute as execute_crawl_property_website
)
from .extract_property_information import (
    get_tool_definition as get_extract_property_information_definition,
    execute as execute_extract_property_information
)
from .extract_website_images import (
    get_tool_definition as get_extract_website_images_definition,
    execute as execute_extract_website_images
)
from .extract_brand_identity import (
    get_tool_definition as get_extract_brand_identity_definition,
    execute as execute_extract_brand_identity
)
from .extract_amenities import (
    get_tool_definition as get_extract_amenities_definition,
    execute as execute_extract_amenities
)
from .extract_floor_plans import (
    get_tool_definition as get_extract_floor_plans_definition,
    execute as execute_extract_floor_plans
)
from .extract_special_offers import (
    get_tool_definition as get_extract_special_offers_definition,
    execute as execute_extract_special_offers
)
from .extract_reviews import (
    get_tool_definition as get_extract_reviews_definition,
    execute as execute_extract_reviews
)
from .generate_reviews_sentiment import (
    get_tool_definition as get_generate_reviews_sentiment_definition,
    execute as execute_generate_reviews_sentiment
)
# DEPRECATED: onboard_property tool removed - use workflows instead
# from .onboard_property import (
#     get_tool_definition as get_onboard_property_definition,
#     execute as execute_onboard_property
# )
from .find_competitors import (
    get_tool_definition as get_find_competitors_definition,
    execute as execute_find_competitors
)
from .generate_social_posts import (
    get_tool_definition as get_generate_social_posts_definition,
    execute as execute_generate_social_posts
)
from .classify_images import (
    get_tool_definition as get_classify_images_definition,
    execute as execute_classify_images
)
from .bulk_classify_images import (
    get_tool_definition as get_bulk_classify_images_definition,
    execute as execute_bulk_classify_images
)

# Registry of all available tools
_TOOLS_REGISTRY = {
    "crawl_property_website": {
        "definition": get_crawl_property_website_definition,
        "execute": execute_crawl_property_website
    },
    "extract_property_information": {
        "definition": get_extract_property_information_definition,
        "execute": execute_extract_property_information
    },
    "extract_website_images": {
        "definition": get_extract_website_images_definition,
        "execute": execute_extract_website_images
    },
    "extract_brand_identity": {
        "definition": get_extract_brand_identity_definition,
        "execute": execute_extract_brand_identity
    },
    "extract_amenities": {
        "definition": get_extract_amenities_definition,
        "execute": execute_extract_amenities
    },
    "extract_floor_plans": {
        "definition": get_extract_floor_plans_definition,
        "execute": execute_extract_floor_plans
    },
    "extract_special_offers": {
        "definition": get_extract_special_offers_definition,
        "execute": execute_extract_special_offers
    },
    "extract_reviews": {
        "definition": get_extract_reviews_definition,
        "execute": execute_extract_reviews
    },
    "generate_reviews_sentiment": {
        "definition": get_generate_reviews_sentiment_definition,
        "execute": execute_generate_reviews_sentiment
    },
    # DEPRECATED: onboard_property tool removed - use workflows instead
    # "onboard_property": {
    #     "definition": get_onboard_property_definition,
    #     "execute": execute_onboard_property
    # },
    "find_competitors": {
        "definition": get_find_competitors_definition,
        "execute": execute_find_competitors
    },
    "generate_social_posts": {
        "definition": get_generate_social_posts_definition,
        "execute": execute_generate_social_posts
    },
    "classify_images": {
        "definition": get_classify_images_definition,
        "execute": execute_classify_images
    },
    "bulk_classify_images": {
        "definition": get_bulk_classify_images_definition,
        "execute": execute_bulk_classify_images
    }
}


def get_all_tools():
    """
    Returns a list of all available tool definitions for OpenAI.
    
    Returns:
        List of tool definition dictionaries
    """
    return [tool["definition"]() for tool in _TOOLS_REGISTRY.values()]


def execute_tool(tool_name, arguments):
    """
    Execute a tool by name.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments for the tool
        
    Returns:
        Dictionary with the tool execution result
        
    Raises:
        ValueError: If the tool name is not found
    """
    if tool_name not in _TOOLS_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    print(f"\n[Tool Called: {tool_name}]")
    
    tool = _TOOLS_REGISTRY[tool_name]
    result = tool["execute"](arguments)
    
    return result

