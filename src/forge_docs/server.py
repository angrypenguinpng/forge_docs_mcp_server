"""MCP server for FORGE documentation"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional, Any

from mcp.server.models import InitializationOptions
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from .parser import ForgeDocParser
from .models import ParsedDoc


# Global variable to store parsed documentation
PARSED_DOC: Optional[ParsedDoc] = None


def load_documentation():
    """Load and parse the FORGE documentation"""
    global PARSED_DOC
    
    try:
        # Get the path to the documentation file
        doc_path = Path(__file__).parent / "docs" / "forge.txt"
        
        print(f"Looking for documentation at: {doc_path}", file=sys.stderr)
        
        if not doc_path.exists():
            print(f"Documentation file not found: {doc_path}", file=sys.stderr)
            raise FileNotFoundError(f"Documentation file not found: {doc_path}")
        
        print(f"Documentation file found, size: {doc_path.stat().st_size} bytes", file=sys.stderr)
        
        # Read and parse the documentation
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"Documentation content loaded, length: {len(content)} characters", file=sys.stderr)
        
        parser = ForgeDocParser()
        print("Created parser, starting to parse...", file=sys.stderr)
        
        PARSED_DOC = parser.parse_document(content)
        
        print(f"Loaded documentation with {len(PARSED_DOC.sections)} top-level sections", file=sys.stderr)
        
    except Exception as e:
        print(f"Error in load_documentation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise


# Load documentation on startup
try:
    load_documentation()
except Exception as e:
    print(f"Error loading documentation: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)


# Replace the global variable and tool definitions
mcp = FastMCP("forge-docs")

@mcp.tool()
async def search_docs(query: str, max_results: int = 5) -> str:
    """Search the FORGE documentation for relevant content."""
    try:
        print(f"search_docs called with query: {query}", file=sys.stderr)
        if not PARSED_DOC:
            return "Documentation not loaded"
        
        results = PARSED_DOC.search(query, max_results)
        
        if not results:
            return f"No results found for '{query}'"
        
        # Format results
        formatted_results = []
        for result in results:
            text = f"**{result['title']}**\n"
            text += f"Path: {result['path']}\n"
            text += f"Preview: {result['preview']}\n"
            formatted_results.append(text)
        
        return "\n\n".join(formatted_results)
    except Exception as e:
        print(f"Error in search_docs: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return f"Error searching documentation: {e}"

@mcp.tool()
async def get_section(path: str) -> str:
    """Get content of a specific documentation section by path."""
    try:
        print(f"get_section called with path: {path}", file=sys.stderr)
        if not PARSED_DOC:
            return "Documentation not loaded"
        
        section = PARSED_DOC.sections_by_path.get(path)
        
        if not section:
            # Try to find partial matches
            similar_paths = [p for p in PARSED_DOC.sections_by_path.keys() if path.lower() in p.lower()]
            if similar_paths:
                suggestions = "\n".join(f"- {p}" for p in similar_paths[:5])
                return f"Section not found. Did you mean one of these?\n{suggestions}"
            else:
                return f"Section not found: {path}"
        
        return section.get_full_content()
    except Exception as e:
        print(f"Error in get_section: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return f"Error getting section: {e}"

@mcp.tool()
async def get_code_examples(topic: str, language: str = None) -> str:
    """Get code examples related to a specific topic."""
    try:
        print(f"get_code_examples called with topic: {topic}, language: {language}", file=sys.stderr)
        if not PARSED_DOC:
            return "Documentation not loaded"
        
        topic_lower = topic.lower()
        relevant_examples = []
        
        for code_block in PARSED_DOC.all_code_blocks:
            # Check if topic appears in the code or its context
            if (topic_lower in code_block.code.lower() or 
                topic_lower in code_block.context_section.lower()):
                
                # Apply language filter if specified
                if language and code_block.language.lower() != language.lower():
                    continue
                
                relevant_examples.append(code_block)
        
        if not relevant_examples:
            return f"No code examples found for '{topic}'"
        
        # Format examples
        formatted_examples = []
        for example in relevant_examples[:10]:  # Limit to 10 examples
            text = f"**From section:** {example.context_section}\n\n"
            text += str(example)
            formatted_examples.append(text)
        
        return "\n\n".join(formatted_examples)
    except Exception as e:
        print(f"Error in get_code_examples: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return f"Error getting code examples: {e}"

@mcp.tool()
async def get_api_info(class_name: str, method_name: str = None) -> str:
    """Get API documentation for a class or method."""
    try:
        print(f"get_api_info called with class_name: {class_name}, method_name: {method_name}", file=sys.stderr)
        if not PARSED_DOC:
            return "Documentation not loaded"
        
        # First, try to find the class in API entries
        api_entry = PARSED_DOC.api_entries.get(class_name)
        
        if not api_entry:
            # Try to find it in sections
            for section in PARSED_DOC.sections_by_path.values():
                if class_name.lower() in section.title.lower():
                    text = section.get_full_content(include_subsections=True)
                    
                    # If looking for a specific method, try to find it
                    if method_name:
                        method_lower = method_name.lower()
                        lines = text.split('\n')
                        method_section = []
                        capturing = False
                        
                        for line in lines:
                            if method_lower in line.lower() and ('##' in line or '###' in line):
                                capturing = True
                            elif capturing and line.strip().startswith('#'):
                                break
                            
                            if capturing:
                                method_section.append(line)
                        
                        if method_section:
                            text = '\n'.join(method_section)
                    
                    return text
        
        # If we found an API entry
        if api_entry:
            text = f"# {api_entry.name}\n\n"
            text += f"Type: {api_entry.type}\n\n"
            text += f"{api_entry.description}\n\n"
            
            if api_entry.section_path:
                section = PARSED_DOC.sections_by_path.get(api_entry.section_path)
                if section:
                    text += section.get_full_content()
            
            return text
        
        return f"No API documentation found for '{class_name}'"
    except Exception as e:
        print(f"Error in get_api_info: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return f"Error getting API info: {e}"

@mcp.tool()
async def list_sections(parent_path: str = None) -> str:
    """List all sections or subsections under a given path."""
    try:
        print(f"list_sections called with parent_path: {parent_path}", file=sys.stderr)
        if not PARSED_DOC:
            return "Documentation not loaded"
        
        if parent_path:
            # List subsections of a specific section
            parent_section = PARSED_DOC.sections_by_path.get(parent_path)
            if not parent_section:
                return f"Parent section not found: {parent_path}"
            
            if not parent_section.subsections:
                return f"No subsections found under '{parent_path}'"
            
            sections_list = "\n".join(f"- {s.title}: {s.path}" for s in parent_section.subsections)
            return f"Subsections of '{parent_path}':\n{sections_list}"
        else:
            # List top-level sections
            sections_list = "\n".join(f"- {s.title}: {s.path}" for s in PARSED_DOC.sections)
            return f"Top-level sections:\n{sections_list}"
    except Exception as e:
        print(f"Error in list_sections: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return f"Error listing sections: {e}"

def main():
    """Main entry point for the server"""
    try:
        print("Starting FastMCP server...", file=sys.stderr)
        # Run the server using FastMCP
        mcp.run()
    except Exception as e:
        print(f"Error in main: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise


if __name__ == "__main__":
    main()