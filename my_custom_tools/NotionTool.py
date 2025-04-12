from typing import Generic, TypeVar, List, ClassVar, Dict
from portia import * 
from dotenv import load_dotenv
from portia.cli import CLIExecutionHooks
import requests
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List
from notion_client import Client
import os
import openai
import re
import google.generativeai as genai


class NotionToolSchema(BaseModel):
    """Input schema for ArXiv Tool"""
    topics: list[str] = Field(..., description="The topic to learn about")

class NotionTool(Tool[List[Dict[str, str]]]):
    """Creates and populates a Notion Board and subpages for learning"""

    id: ClassVar[str] = "notion_tool"
    name: ClassVar[str] = "Notion Tool"
    description: ClassVar[str] = "Create and populate Notion Learning Plan."
    args_schema = NotionToolSchema
    output_schema: ClassVar[tuple[str, str]] = (
        "list[dict[str, str]]",
        "A list of dictionaries that have 'topic' and 'page_id' for each Notion page created."
    )

    def run(self, context: ToolRunContext, topics: list[str]) -> List[Dict[str, str]]:
        notion_api_key = os.getenv("NOTION_API_KEY")
        notion_parent_id = os.getenv("NOTION_PARENT_ID")
        notion = Client(auth=notion_api_key)

        notion.pages.update(
            page_id=notion_parent_id,
            properties={
                "title": [
                    {
                        "type": "text",
                        "text": {"content": "Learning Boards"}
                    }
                ]
            }
        )

        created_pages = []
        checkbox_blocks = []

        for topic in topics:
            blocks, content = self.generate_lesson_blocks(topic)

            response = notion.pages.create(
                parent={"type": "page_id", "page_id": notion_parent_id},
                properties={"title": [{"type": "text", "text": {"content": topic}}]},
                children=blocks
            )

            created_pages.append({"topic": topic, "page_id": response["id"], "content": content})

            checkbox_blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": topic}}],
                    "checked": False
                }
            })

        # Now add the Paper Summary page (one page, after all topics)
        response = notion.pages.create(
            parent={"type": "page_id", "page_id": notion_parent_id},
            properties={
                "title": [
                    {"type": "text", "text": {"content": "Paper Summary"}}
                ]
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": ""}}
                        ]
                    }
                }
            ]
        )

        created_pages.append({"topic": "Paper Summary", "page_id": response["id"], "content": "summary of paper"})

        notion.blocks.children.append(
            block_id=notion_parent_id,
            children=[
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "📈 Progress Tracker"}
                            }
                        ]
                    }
                },
                *checkbox_blocks
            ]
        )

        return created_pages

    def generate_lesson_blocks(self, topic: str) -> List[dict]:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        section_map = {
            "introduction": "📘 Introduction",
            "key definitions": "📾 Key Definitions",
            "relevant formulas": "🔣 Relevant Formulas",
            "examples": "💡 Examples",
            "reflective questions": "🧠 Reflective Questions"
        }

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "You're a tutor writing lesson content formatted for Notion pages. "
                    "Use clear section delimiters. Each section MUST begin with [[Section Name]] on its own line. "
                    "Sections: Introduction, Key Definitions, Relevant Formulas, Examples, Reflective Questions. "
                    "All math must be written using inline LaTeX formatted as \\( ... \\). "
                    "Do NOT use display math like \\[...\\], $$...$$, or {{math: ...}}. "
                    "Do NOT wrap equations in square brackets [ ... ] or parentheses like (\\( ... \\)). "
                    "In the 'Relevant Formulas' section, format each entry with a short bold title on one line, followed by the math on its own line in \\( ... \\). "
                    "Keep formulas concise and readable with no extra explanation unless absolutely necessary. "
                    "Only use valid LaTeX commands (e.g., \\frac, \\int, \\sum, \\left(, \\right)). "
                    "Each lesson must be self-contained: include 3-4 definitions, 2-3 formulas, 2 examples, and 5 reflective questions."
                )},
                {"role": "user", "content": (
                    f"Write a comprehensive and self-contained lesson on '{topic}' using this exact format with [[Section Name]] delimiters.\n"
                    "[[Introduction]]\n<short paragraph>\n\n[[Key Definitions]]\n- Definition 1\n- Definition 2\n- Definition 3\n\n[[Relevant Formulas]]\n"
                    "- For each formula, use a bold title and then place the math expression on its own line in \\( ... \\)\n\n"
                    "[[Examples]]\n<Include at least 2 real-world intuitive examples>\n\n[[Reflective Questions]]\n"
                    "1. Question 1\n2. Question 2\n3. Question 3\n4. Question 4\n5. Question 5"
                )}
            ],
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()

        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)

        generation_config = genai.types.GenerationConfig(
            temperature=0.2
        )

        model_name = "gemini-2.0-flash" 
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
        )

        verify_prompt = (
            "You are a factual checker for educational content.\n"
            "Your job is to read the following lesson and correct any factual errors, math mistakes, or misleading information.\n"
            "Do NOT alter the structure, formatting, section headers, or LaTeX math delimiters (\\( ... \\)).\n"
            "Keep bullet points, numbering, and headings exactly as they are.\n"
            "If the lesson is already correct, return it unchanged.\n\n"
            "Return ONLY the revised lesson text — no commentary, explanation, or summary.\n\n"
            f"{content}"
        )

        revision = model.generate_content(verify_prompt)

        content = revision.text.strip() 
        
        blocks = []
        section = None

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            # Section detection
            if line.startswith("[[") and line.endswith("]]"):
                section = line[2:-2].strip().lower()
                if section in section_map:
                    blocks.append(self._heading_block(section_map[section]))
                continue

            # Clean awkward (\( ... \)) patterns
            line = re.sub(r"\(\\\((.*?)\\\)\)", r"\\(\1\\)", line)

            if section == "key definitions":
                blocks.append(self._bulleted(self._clean_list_prefix(line)))
            elif section == "relevant formulas":
                # Keep minimal formula display inline
                if re.search(r"\\\(.*?\\\)", line):
                    blocks.append(self._paragraph(line))
                else:
                    blocks.append(self._paragraph(line))
            elif section == "reflective questions":
                blocks.append(self._numbered(self._clean_list_prefix(line)))
            else:
                blocks.append(self._paragraph(line))

        return blocks, content

    def _clean_list_prefix(self, text):
        return re.sub(r"^(\d+\.\s+|[-*]\s+)", "", text)

    def _is_valid_latex(self, expr):
        expr = expr.strip()
        expr = re.sub(r"^\\\[|\\\]$|^\$\$|\$\$", "", expr)
        return expr.count("{") == expr.count("}") and not re.search(r"\\[^a-zA-Z]", expr)

    def _rich_text_from_marked_text(self, text):
        parts = []
        pattern = r'(\*\*(.*?)\*\*|_(.*?)_|`([^`]*)`|\\\((.*?)\\\)|([^*_`\\]+))'
        for match in re.finditer(pattern, text):
            bold, bold_text, italic_text, code_text, math_inline, plain = match.groups()
            if bold_text:
                parts.append({"type": "text", "text": {"content": bold_text}, "annotations": {"bold": True}})
            elif italic_text:
                parts.append({"type": "text", "text": {"content": italic_text}, "annotations": {"italic": True}})
            elif code_text:
                parts.append({"type": "text", "text": {"content": code_text}, "annotations": {"code": True}})
            elif math_inline and self._is_valid_latex(math_inline):
                parts.append({"type": "equation", "equation": {"expression": math_inline.strip()}})
            elif plain:
                parts.append({"type": "text", "text": {"content": plain}})
        return parts

    def _heading_block(self, text):
        return {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": self._rich_text_from_marked_text(text)
            }
        }

    def _paragraph(self, text):
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": self._rich_text_from_marked_text(text)
            }
        }

    def _bulleted(self, text):
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": self._rich_text_from_marked_text(text)
            }
        }

    def _numbered(self, text):
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": self._rich_text_from_marked_text(text)
            }
        }

    def _code(self, text):
        return self._paragraph(text)

    def _equation_block(self, text):
        match = re.search(r"\\\((.*?)\\\)", text)
        if match:
            expression = match.group(1).strip()
            if self._is_valid_latex(expression):
                return {
                    "object": "block",
                    "type": "equation",
                    "equation": {"expression": expression}
                }
        return self._paragraph(text)