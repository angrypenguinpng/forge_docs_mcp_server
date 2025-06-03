# FORGE Docs MCP Server

A Model Context Protocol (MCP) server that provides access to FORGE 3D Gaussian Splatting documentation through Claude Desktop.

## Features

- **Search Documentation**: Find relevant sections using natural language queries
- **Browse Sections**: Navigate through documentation sections by path
- **Code Examples**: Find code examples related to specific topics
- **API Information**: Get detailed API documentation for classes and methods
- **Section Listing**: Browse available documentation sections

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/angrypenguinpng/forge_docs_mcp_server.git
   cd forge_docs_mcp
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

## Usage

### Test the server locally:
```bash
uv run forge-docs
```

### Configure with Claude Desktop:

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "forge-docs": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/your/forge_docs_mcp",
        "run",
        "forge-docs"
      ]
    }
  }
}
```

Replace `/path/to/your/forge_docs_mcp` with the actual path to this project.

## Available Tools

- `search_docs(query, max_results=5)` - Search documentation
- `get_section(path)` - Get specific section content
- `get_code_examples(topic, language=None)` - Find code examples
- `get_api_info(class_name, method_name=None)` - Get API documentation
- `list_sections(parent_path=None)` - List available sections

## Example Queries in Claude

- "Search for installation instructions"
- "Show me the Quick Start section"
- "Find Python code examples for creating a Gaussian"
- "Get API info for the GaussianModel class"
- "List all available documentation sections"

## Development

The server is built using the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk).

### Project Structure

```bash
# Install with uv (recommended)
uv pip install -e .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
