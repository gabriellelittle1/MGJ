from dotenv import load_dotenv
from portia.cli import CLIExecutionHooks
from portia import *
import requests
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, ClassVar, Dict, Literal, Type
from notion_client import Client
import os
from my_custom_tools.utils import truncate_at_sentence
import openai


class PSToolSchema(BaseModel): 

    """Input Schema for PSTool."""
    papers: List[Dict[str, str]] = Field(..., description="The list of dictionaries (output from the arXivTool), each with 'title', 'summary' and 'link' keys.")
    pdf_texts: Dict[str, str] = Field(..., description="The dictionary of filename -> full text (output from the PDFReaderTool).")

class PSTool(Tool[None]):

    """A tool to create a Notion page for a paper summary, and populate it."""

    id: ClassVar[str] = "pstool"
    name: ClassVar[str] = "PS Tool"
    description: ClassVar[str] = "A tool to create a Notion page for a paper summary, and populate it."
    args_schema: Type[BaseModel] = PSToolSchema
    output_schema: ClassVar[tuple[str, str]] = (
        "None",
        "This tool does not return anything."
    )

    def run(self, context, papers: List[Dict[str, str]], pdf_texts: Dict[str, str]) -> None:
        """Adds Notion page and fills it with paper summary."""

        notion_api_key = os.getenv("NOTION_API_KEY")
        
        if not notion_api_key:
            raise EnvironmentError("Missing NOTION_API_KEY or GOOGLE_API_KEY")

        notion = Client(auth=notion_api_key)
        notion_parent_id = os.getenv("NOTION_PARENT_ID")
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        pdf_text = next(iter(pdf_texts.values()), "")

        blocks = []
        paper = papers[0]
        title = paper["title"]
        summary = paper["summary"]
        summary = truncate_at_sentence(summary, 300)
        link = paper["link"]

        title_block = {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [{"type": "text", "text": {"content": f"📄 {title}"}}]
                        }
                    }

        blocks.append(title_block)

        summary_block = {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": paper["summary"]}}]
                        }
                    }

        blocks.append(summary_block)

        link_block = {
                        "object": "block",
                        "type": "bookmark",
                        "bookmark": {
                            "url": link
                        }
                    }

        blocks.append(link_block)

        response1 = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.3,
            messages=[
                {"role": "system", "content": (
                    "You are a scientific writing assistant helping summarize and analyze academic papers. "
                    "Structure the output into clearly labeled sections. Each section MUST begin with [[Section Name]] on its own line. "
                    "Sections: Intuitive Understanding, Method Breakdown, Novelties / Contributions, Critiques, Related Reading. "
                    "Write clearly for an advanced undergraduate audience. Use bullet points if appropriate. DO NOT include LaTeX or math equations."
                )},
                {"role": "user", "content": (
                    f"Summarize and explain the following academic paper content:\n\n{pdf_text}\n\n"
                    "Use the following structure exactly, and ensure each section starts with [[Section Name]]:\n\n"
                    "[[Intuitive Understanding]]\n"
                    "Describe the core idea of the paper with conceptual depth and clarity. "
                    "Explain the reasoning or motivation behind the approach in a way that reveals why it works, not just what it does. "
                    "Write as if speaking to an intelligent undergraduate student — assume curiosity, not prior technical knowledge. "
                    "Avoid metaphors and analogies, but aim to build real understanding through clear logic and plain language.\n\n"
                    "[[Method Breakdown]]\n"
                    "Describe the main techniques or pipeline steps used in the paper.\n\n"
                    "[[Novelties / Contributions]]\n"
                    "List what makes this work new, better, or different.\n\n"
                    "[[Critiques]]\n"
                    "Note assumptions, weaknesses, or areas for improvement.\n\n"
                    "[[Related Reading]]\n"
                    "Suggest 2-3 related topics or papers worth reading next."
                )}
            ]
        )

        generated_content = response1.choices[0].message.content.strip()

        # Parse into Notion blocks
        section_blocks = []
        section_heading_map = {
            "intuitive understanding": "🧠 Intuitive Understanding",
            "method breakdown": "⚙️ Method Breakdown",
            "novelties / contributions": "🌟 Novelties / Contributions",
            "critiques": "🧪 Critiques",
            "related reading": "📚 Related Reading"
        }

        for line in generated_content.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("[[") and line.endswith("]]"):
                section_key = line[2:-2].strip().lower()
                readable_title = section_heading_map.get(section_key, section_key.title())
                section_blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": readable_title}}]
                    }
                })
            else:
                section_blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": line}}]
                    }
                })

        blocks.extend(section_blocks)

        response = notion.pages.create(
                parent={"type": "page_id", "page_id": notion_parent_id},
                properties={"title": [{"type": "text", "text": {"content": "Paper Summary"}}]},
                children=blocks
            )
        
    
        return 
