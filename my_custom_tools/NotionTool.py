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

class NotionToolSchema(BaseModel):
    """Input schema for ArXiv Tool"""
    topics: list[str] = Field(..., description="The topic to learn about")

# Step 2: Define the Tool
class NotionTool(Tool[str]):
    """Creates and populates a Notion Board and subpages for learning"""

    ### Eventually add in podcasts, youtube videos, further reading
    ### As well as 

    id: ClassVar[str] = "notion_tool"
    name: ClassVar[str] = "Notion Tool"
    description: ClassVar[str] = "Create and populate Notion Learning Plan."
    args_schema = NotionToolSchema
    output_schema: ClassVar[tuple[str, str]] = (
        "list[dict[str, str]]",
        "A list of topics to create Notion pages and learning plans for."
    )

    def run(self, context: ToolRunContext, topics: list[str]) -> str:
        
        """Run the Notion Tool."""

        notion_api_key = os.getenv(("NOTION_API_KEY"))
        notion_parent_id = os.getenv("NOTION_PARENT_ID")

        notion = Client(auth=notion_api_key)

        notion.pages.update(page_id=notion_parent_id,
        properties = {
            "title": [
                {
                    "type": "text",
                    "text": {"content": "Learning Boards"}
                }
            ]
        })

        # Step 1: Create subpages for each topic
        for topic in topics:
            notion.pages.create(
                parent={"type": "page_id", "page_id": notion_parent_id},
                properties={
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": topic}
                        }
                    ]
                },
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"This page is about {topic}."
                                    }
                                }
                            ]
                        }
                    }
                ]
            )
        
        # Step 2: Build a clean checkbox list with no links
        checkbox_blocks = []

        for topic in topics:
            checkbox_blocks.append({"object": "block", "type": "to_do",
                "to_do": {"rich_text": [
                        {
                            "type": "text",
                            "text": {"content": topic}
                        }
                    ],
                    "checked": False}})

        # Step 3: Add a section title + checklist to the main page
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

        return "Notion has been updated!"