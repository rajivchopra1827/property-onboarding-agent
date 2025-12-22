#!/usr/bin/env python3
"""
FionaFast - Property Information Extraction Agent
A conversational agent designed to extract comprehensive information from property websites.
"""

import os
import sys
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from tools import get_all_tools, execute_tool


def get_system_prompt():
    """Returns the system prompt that defines FionaFast's capabilities."""
    return """You are FionaFast, a specialized AI agent designed to extract comprehensive information from property websites for apartment buildings and residential complexes.

Your primary capability is to extract the following information from property websites:

1. **Property Information**
   - Property name (name of the apartment complex/property)
   - Address (street, city, state, ZIP code)
   - Phone number
   - Email address
   - Office hours

2. **Images**
   - All images on the website (exterior, interior, amenities, etc.)
   - Future capability: organize them by type

3. **Amenities**
   - Building amenities (pool, gym, business center, etc.)
   - Apartment amenities (appliances, features, etc.)

4. **Floor Plans**
   - Size (square feet)
   - Bedrooms/bathrooms
   - Price ranges
   - Availability status and unit counts
   - Floorplan photos

5. **Special Offers/Concessions**
   - Promotions (e.g., "First month free")
   - Descriptions
   - Validity dates

6. **Pet Policy**
   - Whether pets are allowed
   - Deposit amounts
   - Monthly fees
   - Restrictions (size limits, breed restrictions, etc.)

7. **Brand Guidelines**
   - Brand colors
   - Tone
   - Tagline/slogan
   - Keywords they use

8. **Social Media Profiles**
   - Instagram, Facebook, Twitter, LinkedIn
   - Handles and profile URLs

9. **Testimonials/Reviews**
   - Star ratings
   - Customer quotes
   - Author names

10. **Nearby Points of Interest**
    - Schools, transit, shopping, entertainment, dining
    - Names and distances from property

You have access to the following tools:

1. **onboard_property**: Fully onboards a property by running all extraction tools in sequence. This is the recommended tool when users want to extract comprehensive information from a property website. It runs all extractions (property info, images, brand identity, amenities, floor plans, special offers) and handles errors gracefully. Use this when:
   - User wants to "onboard" a property or extract "all information" from a property website
   - User wants comprehensive property data extraction
   - This tool orchestrates all other extraction tools and provides a complete summary

2. **crawl_property_website**: Crawls/scrapes property websites and caches the content. Returns raw markdown from all crawled pages (no images). Use this when:
   - User says "crawl [url]" or "scrape [url]"
   - You need to get website content for other tools to use
   - This tool handles caching automatically and will prompt the user if cached data exists

3. **extract_property_information**: Extracts structured property information (name, address, phone, email, office hours). Can accept either:
   - A URL (will call crawl_property_website internally to get content)
   - Markdown content directly (if you already have crawled content)
   - Use this when user asks to "extract property information from [url]"

4. **extract_website_images**: Extracts images from property websites using Apify Actor. Returns a list of image URLs found across the website. Use this when:
   - User asks to extract images from a website
   - You need to get images separately from markdown content
   - This tool has its own caching system and will prompt the user if cached images exist

5. **extract_brand_identity**: Extracts comprehensive brand identity information from property websites using Firecrawl. Returns branding data including colors, fonts, typography, spacing, UI components, logo, and design system information. Use this when:
   - User asks to extract brand identity, brand colors, design system, or visual identity
   - User wants to know about the website's color scheme, fonts, or styling
   - This tool has its own caching system and will prompt the user if cached branding exists

6. **extract_amenities**: Extracts amenities information from property websites. Returns building amenities (pool, gym, etc.) and apartment amenities (appliances, features, etc.). Can accept either a URL or markdown content. Use this when:
   - User asks to extract amenities from a property website
   - User wants to know what amenities are available

7. **extract_floor_plans**: Extracts floor plan information from property websites. Returns floor plan details including name, size, bedrooms, bathrooms, prices, and availability. Can accept either a URL or markdown content. Use this when:
   - User asks to extract floor plans from a property website
   - User wants to know about available unit types and pricing

8. **extract_special_offers**: Extracts special offers and promotions from property websites. Returns offer descriptions, validity dates, and descriptive text. Can accept either a URL or markdown content. Use this when:
   - User asks to extract special offers or promotions from a property website
   - User wants to know about current deals or move-in specials

9. **bulk_classify_images**: Bulk classifies all unclassified images for a property (or all properties). Processes images in batches to assign tags, confidence scores, and quality scores. Can re-classify existing images if needed. Use this when:
   - User asks to "bulk classify images" or "classify all images" for a property
   - User wants to classify multiple images at once for a property ID
   - This tool automatically finds unclassified images and processes them in batches

**Tool Usage Flow**:
- **For comprehensive onboarding**: Use `onboard_property` tool - this is the easiest way to extract all information from a property website
- If user wants to crawl/scrape for markdown: Use `crawl_property_website` tool
- If user wants to extract specific information: Use the appropriate extraction tool (extract_property_information, extract_amenities, etc.)
- If user wants to extract images: Use `extract_website_images` tool
- If user wants to extract brand identity: Use `extract_brand_identity` tool with URL
- If you already have markdown from a previous crawl: Use extraction tools with markdown parameter

**Cache System**: Most tools use separate caching systems. If cached data exists, they will automatically prompt the user to choose between using the cache (faster) or refreshing with a new extraction (latest data). The `onboard_property` tool respects cache preferences and passes them to individual extraction tools.

When asked about your capabilities, provide a clear and helpful explanation of what you can do and how you're designed to help with property information extraction."""


def main():
    """Main function to run the FionaFast agent."""
    # Load environment variables from .env.local or .env file
    # Check current directory first, then parent directory (project root)
    env_file = Path(".env.local")
    if not env_file.exists():
        env_file = Path(".env")
    
    # If not found in current directory, check parent directory (project root)
    if not env_file.exists():
        env_file = Path("../.env.local")
        if not env_file.exists():
            env_file = Path("../.env")
    
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment variables from {env_file}")
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found.")
        print("Please set it in .env.local or .env file, or use: export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    print("=" * 60)
    print("FionaFast - Property Information Extraction Agent")
    print("=" * 60)
    print("\nType your message (or 'quit'/'exit' to end the conversation)\n")
    
    # Get system prompt and tools
    system_prompt = get_system_prompt()
    tools = get_all_tools()
    
    # Conversation history
    messages = [{"role": "system", "content": system_prompt}]
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            if not user_input:
                continue
            
            # Add user message to history
            messages.append({"role": "user", "content": user_input})
            
            # Get response from OpenAI with tool support
            print("\nFionaFast: ", end="", flush=True)
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",  # Using a cost-effective model
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",  # Let the model decide when to use tools
                    stream=True
                )
            except Exception as api_error:
                error_str = str(api_error)
                if "429" in error_str or "rate_limit" in error_str.lower() or "Rate limit" in error_str:
                    print("\n⚠️  Rate Limit Error: OpenAI rate limit reached.")
                    print("You've made too many API requests. Try:")
                    print("  - Waiting a few minutes before trying again")
                    print("  - Using cached data when available (reduces API calls)")
                    print(f"\nError: {error_str[:300]}")
                    # Remove the last user message so they can try again
                    messages.pop()
                    continue
                else:
                    raise
            
            # Handle streaming response with tool calls
            assistant_response = ""
            tool_calls = []
            current_tool_call = None
            
            for chunk in response:
                # Handle content streaming
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    assistant_response += content
                
                # Handle tool calls
                if chunk.choices[0].delta.tool_calls:
                    for tool_call_delta in chunk.choices[0].delta.tool_calls:
                        if tool_call_delta.index is not None:
                            # Initialize tool call if needed
                            while len(tool_calls) <= tool_call_delta.index:
                                tool_calls.append({
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                })
                            
                            current_tool_call = tool_calls[tool_call_delta.index]
                            
                            # Update tool call ID
                            if tool_call_delta.id:
                                current_tool_call["id"] = tool_call_delta.id
                            
                            # Update function name
                            if tool_call_delta.function.name:
                                current_tool_call["function"]["name"] = tool_call_delta.function.name
                            
                            # Update function arguments
                            if tool_call_delta.function.arguments:
                                current_tool_call["function"]["arguments"] += tool_call_delta.function.arguments
            
            print("\n")
            
            # If there are tool calls, execute them
            if tool_calls:
                # Add assistant message with tool calls to history
                messages.append({
                    "role": "assistant",
                    "content": assistant_response if assistant_response else None,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": tc["type"],
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"]
                            }
                        }
                        for tc in tool_calls
                    ]
                })
                
                # Execute each tool call
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    try:
                        tool_arguments = json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError:
                        tool_arguments = {}
                    
                    # Execute the tool
                    tool_result = execute_tool(tool_name, tool_arguments)
                    
                    # Check if tool returned cache availability info
                    # If cache is available and use_cache wasn't specified, prompt user
                    if isinstance(tool_result, dict) and tool_result.get("cache_available"):
                        cache_age = tool_result.get("cache_age_hours", 0)
                        domain = tool_result.get("domain", "this website")
                        
                        # Prompt user about cache
                        print(f"\n[Cache Available] Found cached data for {domain} from {cache_age:.1f} hours ago.")
                        print("Options:")
                        print("  1. Use cache (faster, may be slightly outdated)")
                        print("  2. Refresh (crawl fresh data)")
                        
                        while True:
                            user_choice = input("\nUse cache or refresh? (cache/refresh): ").strip().lower()
                            if user_choice in ['cache', 'c', '1']:
                                # Re-execute tool with use_cache=True
                                tool_arguments["use_cache"] = True
                                tool_result = execute_tool(tool_name, tool_arguments)
                                break
                            elif user_choice in ['refresh', 'r', '2']:
                                # Re-execute tool with force_refresh=True
                                tool_arguments["force_refresh"] = True
                                tool_result = execute_tool(tool_name, tool_arguments)
                                break
                            else:
                                print("Please enter 'cache' or 'refresh'")
                    
                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(tool_result)
                    })
                
                # Get final response after tool execution
                print("FionaFast: ", end="", flush=True)
                try:
                    final_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        tools=tools,
                        stream=True
                    )
                except Exception as api_error:
                    error_str = str(api_error)
                    if "429" in error_str or "rate_limit" in error_str.lower() or "Rate limit" in error_str:
                        print("\n⚠️  Rate Limit Error: OpenAI rate limit reached during response generation.")
                        print("Try using cached data (use_cache=True) to reduce API calls, or wait a few minutes.")
                        print(f"\nError: {error_str[:300]}")
                        # Remove tool result and assistant message to allow retry
                        messages.pop()  # Remove tool result
                        messages.pop()  # Remove assistant message with tool calls
                        continue
                    else:
                        raise
                
                final_assistant_response = ""
                for chunk in final_response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)
                        final_assistant_response += content
                
                print("\n")
                messages.append({"role": "assistant", "content": final_assistant_response})
            else:
                # No tool calls, just add the response
                messages.append({"role": "assistant", "content": assistant_response})
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            # Check for rate limit errors
            error_str = str(e)
            if "429" in error_str or "rate_limit" in error_str.lower() or "Rate limit" in error_str:
                print(f"\n⚠️  Rate Limit Error: You've hit OpenAI's rate limit.")
                print("\nThis means you've made too many API requests in a short time.")
                print("\nOptions:")
                print("  1. Wait a bit and try again (rate limits reset over time)")
                print("  2. Use cached data when available (set use_cache=True) to reduce API calls")
                print("  3. Add a payment method to increase your rate limits")
                print(f"\nFull error: {error_str[:200]}...")
            else:
                print(f"\nError: {e}")
                print("Please check your API key and internet connection.")


if __name__ == "__main__":
    main()

