from dotenv import load_dotenv
from portia.cli import CLIExecutionHooks
from portia import *
import requests
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field, RootModel
from typing import Generic, TypeVar, List, ClassVar, Dict, Optional, Type
from notion_client import Client
import openai
import os
from my_custom_tools.utils import truncate_at_sentence

### This one adds the first step 
class PaperSummary0Schema(BaseModel):
    papers: List[Dict[str, str]]

class PaperSummary0Tool(Tool[str]):
    """Creates a Summary Page in the Notion, and populates it."""

    id: ClassVar[str] = "paper_summary0_tool"
    name: ClassVar[str] = "Paper Summary 0 Tool"
    description: ClassVar[str] = "Creates a Notion subpage summarizing the full paper."
    args_schema: Type[BaseModel] = PaperSummary0Schema
    output_schema: ClassVar[tuple[str, str]] = (
        "str",
        "Confirmation of the summary added on the Notion page."
    )

    def run(self, context: ToolRunContext, input_data: PaperSummary0Schema) -> str:
        papers = input_data.papers
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        parent_id = os.getenv("NOTION_PARENT_ID")
        content = papers[0]['summary']
        title = papers[0]['title']

        blocks = []

        title_block = {
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": f" 📄 {title} Summary"
                        }
                    }
                ]
            }
        }

        summary_block = {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": content
                        }
                    }
                ]
            }
        }

        ## Intuitive block 
        intuitive_block = {
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": f"Intuitive Summary"
                        }
                    }
                ]
            }
        }

        intuitive_summary = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": f"Please summarize the following text in a more intuitive way: {content}"}
            ],
            temperature=0.7,
        )
        intuitive_summary_text = intuitive_summary.choices[0].message.content
        intuitive_summary_block = {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": intuitive_summary_text
                        }
                    }
                ]
            }
        }

        blocks.append(title_block)
        blocks.append(summary_block)
        blocks.append(intuitive_block)
        blocks.append(intuitive_summary_block)
        # Add a link to the original paper
        link_block = {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": f"Original Paper: {papers[0]['link']}"
                        }
                    }
                ]
            }
        }
        blocks.append(link_block)
                       
        # Add the summary to the Notion page
        response = notion.pages.create(
                parent={"type": "page_id", "page_id": parent_id},
                properties={"title": [{"type": "text", "text": {"content": "Paper Summary"}}]},
                children=blocks
            )
        
        return "Paper summary added to Notion page."
