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


class PSToolSchema(BaseModel): 

    """Input Schema for PSTool."""
    papers: List[Dict[str, str]] = Field(description="The list of dictionaries (output from the arXivTool), each with 'title', 'summary' and 'link' keys.")

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

    def run(self, context, papers: List[Dict[str, str]]) -> None:
        """Adds Notion page and fills it with paper summary."""

        notion_api_key = os.getenv("NOTION_API_KEY")
        
        if not notion_api_key:
            raise EnvironmentError("Missing NOTION_API_KEY or GOOGLE_API_KEY")

        notion = Client(auth=notion_api_key)
        notion_parent_id = os.getenv("NOTION_PARENT_ID")

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

        response = notion.pages.create(
                parent={"type": "page_id", "page_id": notion_parent_id},
                properties={"title": [{"type": "text", "text": {"content": "Paper Summary"}}]},
                children=blocks
            )

        return 
