"""Parser for FORGE documentation"""

import re
from typing import List, Dict, Optional, Tuple
from .models import Section, CodeBlock, ParsedDoc, SectionLevel, APIEntry


class ForgeDocParser:
    """Parses FORGE documentation from markdown format"""
    
    def __init__(self):
        self.sections: List[Section] = []
        self.code_blocks: List[CodeBlock] = []
        self.api_entries: Dict[str, APIEntry] = {}
        
    def parse_document(self, content: str) -> ParsedDoc:
        """Parse the entire document"""
        lines = content.split('\n')
        self.sections = []
        self.code_blocks = []
        self.api_entries = {}
        
        current_section_stack: List[Section] = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for headers
            if header_match := re.match(r'^(#{1,3})\s+(.+)$', line):
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                # Create new section
                section = Section(
                    title=title,
                    level=SectionLevel(level),
                    content="",
                    path=self._build_path(current_section_stack, title),
                    line_number=i
                )
                
                # Add to appropriate parent
                self._add_section_to_hierarchy(section, current_section_stack)
                
                # Update stack
                while current_section_stack and current_section_stack[-1].level.value >= level:
                    current_section_stack.pop()
                current_section_stack.append(section)
                
            # Check for code blocks
            elif line.strip().startswith('```'):
                code_block, end_line = self._parse_code_block(lines, i)
                if code_block and current_section_stack:
                    code_block.context_section = current_section_stack[-1].path
                    current_section_stack[-1].code_blocks.append(code_block)
                    self.code_blocks.append(code_block)
                i = end_line
                
            # Regular content
            elif current_section_stack:
                current_section_stack[-1].content += line + "\n"
            
            i += 1
        
        # Build sections by path
        sections_by_path = {}
        for section in self._flatten_sections(self.sections):
            sections_by_path[section.path] = section
        
        # Extract API entries
        self._extract_api_entries()
        
        return ParsedDoc(
            sections=self.sections,
            sections_by_path=sections_by_path,
            all_code_blocks=self.code_blocks,
            api_entries=self.api_entries
        )
    
    def _build_path(self, stack: List[Section], title: str) -> str:
        """Build section path from stack"""
        path_parts = [s.title for s in stack] + [title]
        return "/".join(path_parts)
    
    def _add_section_to_hierarchy(self, section: Section, stack: List[Section]):
        """Add section to appropriate place in hierarchy"""
        if not stack:
            self.sections.append(section)
        else:
            # Find parent section
            for parent in reversed(stack):
                if parent.level.value < section.level.value:
                    parent.subsections.append(section)
                    return
            # If no parent found, add to root
            self.sections.append(section)
    
    def _parse_code_block(self, lines: List[str], start_line: int) -> Tuple[Optional[CodeBlock], int]:
        """Parse a code block starting at the given line"""
        if not lines[start_line].strip().startswith('```'):
            return None, start_line
        
        # Extract language
        first_line = lines[start_line].strip()
        language = first_line[3:].strip() or "plaintext"
        
        # Find end of code block
        code_lines = []
        i = start_line + 1
        while i < len(lines):
            if lines[i].strip() == '```':
                code = '\n'.join(code_lines)
                return CodeBlock(
                    language=language,
                    code=code,
                    context_section="",
                    line_number=start_line
                ), i
            code_lines.append(lines[i])
            i += 1
        
        return None, i
    
    def _flatten_sections(self, sections: List[Section]) -> List[Section]:
        """Flatten nested sections into a single list"""
        result = []
        for section in sections:
            result.append(section)
            result.extend(self._flatten_sections(section.subsections))
        return result
    
    def _extract_api_entries(self):
        """Extract API entries from sections"""
        for section in self._flatten_sections(self.sections):
            # Look for class definitions
            if "class" in section.title.lower() or "Creating a" in section.title:
                # Extract class name
                class_match = re.search(r'Creating a (\w+)|class (\w+)', section.title)
                if class_match:
                    class_name = class_match.group(1) or class_match.group(2)
                    self.api_entries[class_name] = APIEntry(
                        name=class_name,
                        type="class",
                        description=section.content.split('\n')[0],
                        section_path=section.path
                    )
