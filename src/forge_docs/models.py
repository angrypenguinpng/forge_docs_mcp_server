"""Data models for FORGE documentation"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class SectionLevel(Enum):
    MAIN = 1      # #
    SUB = 2       # ##
    DETAIL = 3    # ###


@dataclass
class CodeBlock:
    """Represents a code block in the documentation"""
    language: str
    code: str
    context_section: str  # The section this code block is from
    line_number: int
    
    def __str__(self):
        return f"```{self.language}\n{self.code}\n```"


@dataclass
class Section:
    """Represents a documentation section"""
    title: str
    level: SectionLevel
    content: str
    path: str  # e.g., "Getting Started/Quick Start"
    line_number: int
    code_blocks: List[CodeBlock] = field(default_factory=list)
    subsections: List['Section'] = field(default_factory=list)
    
    def get_full_content(self, include_subsections: bool = True) -> str:
        """Get full content including subsections if requested"""
        content = f"{'#' * self.level.value} {self.title}\n\n{self.content}"
        
        if include_subsections:
            for subsection in self.subsections:
                content += "\n\n" + subsection.get_full_content()
        
        return content


@dataclass
class APIEntry:
    """Represents an API entry (class, method, property)"""
    name: str
    type: str  # "class", "method", "property"
    description: str
    parameters: List[Dict[str, str]] = field(default_factory=list)
    returns: Optional[str] = None
    examples: List[CodeBlock] = field(default_factory=list)
    section_path: str = ""


@dataclass
class ParsedDoc:
    """Represents the fully parsed documentation"""
    sections: List[Section]
    sections_by_path: Dict[str, Section]
    all_code_blocks: List[CodeBlock]
    api_entries: Dict[str, APIEntry]
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Simple search implementation"""
        results = []
        query_lower = query.lower()
        
        for section in self.sections:
            if query_lower in section.title.lower() or query_lower in section.content.lower():
                results.append({
                    "title": section.title,
                    "path": section.path,
                    "preview": section.content[:200] + "..." if len(section.content) > 200 else section.content,
                    "type": "section"
                })
                
                if len(results) >= max_results:
                    break
        
        return results
