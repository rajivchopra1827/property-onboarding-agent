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

# Registry of all available tools
_TOOLS_REGISTRY = {
    "crawl_property_website": {
        "definition": get_crawl_property_website_definition,
        "execute": execute_crawl_property_website
    },
    "extract_property_information": {
        "definition": get_extract_property_information_definition,
        "execute": execute_extract_property_information
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

