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


class PaperSummaryToolSchema(BaseModel):
    """Input schema for PaperSummaryTool."""
    topics: List[Dict[str, str]] = Field(description="The list of dictionaries (output from the NotionTool), each with 'topic', 'page_id' and 'content' keys.")
    # papers: List[Dict[str, str]] = Field(
    
    #     description="A list of dictionaries, each with 'title', 'link', and 'summary' fields. Take the output of ArxivTool."
    # )
    # pdf_texts: Dict[str, str] = Field(
    #     ..., 
    #     description="A dictionary mapping PDF filenames to their full extracted text content. Takes the output of PDFReaderTool."
    # )


class PaperSummaryTool(Tool[str]):
    """Creates a summary Notion subpage for the full paper with explanation and novelties."""

    id: ClassVar[str] = "paper_summary_tool"
    name: ClassVar[str] = "Paper Summary Tool"
    description: ClassVar[str] = "Populates the Notion subpage 'Page Summary' summarizing the full paper and its novelties."
    args_schema: type[BaseModel] = PaperSummaryToolSchema
    output_schema: ClassVar[tuple[str, str]] = (
        "str",
        "Confirmation of the summary page creation."
    )

    # def run(self, context: ToolRunContext, topics: List[Dict[str, str]], papers: List[Dict[str, str]], pdf_texts: Dict[str, str]) -> str:
    def run(self, context: ToolRunContext, topics: List[Dict[str, str]]) -> str:
        """Creates a summary Notion subpage for the full paper with explanation and novelties."""

        

        # paper = papers[0]
        # title = paper["title"]
        # summary = paper["summary"]
        # pdf_url = paper["link"]

        # pdf_text = next(iter(pdf_texts.values()), "")


        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        paper_topic = next((t for t in topics if t["topic"].lower() == "paper summary"), None)

        if not paper_topic:
            return "❌ 'Paper Summary' page not found in input."

        parent_id = paper_topic["page_id"]

        existing_blocks = notion.blocks.children.list(block_id=parent_id).get("results", [])
        for block in existing_blocks:
            try:
                notion.blocks.delete(block["id"])
            except:
                continue

        # Append blocks to the existing Paper Summary page
        notion.blocks.children.append(
            block_id=parent_id,
            children=[
                    # Title
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [{"type": "text", "text": {"content": "garbage"}}] #f"📄 {paper['title']}"}}]
                        }
                    },
                    # Summary
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": "garbage"}}] #paper["summary"]}}]
                        }
                    },
                    # Embed PDF
                    {
                        "object": "block",
                        "type": "bookmark",
                        "bookmark": {
                            "url": pdf_url
                        }
                    }
                ]
            )   
        # client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # response = client.chat.completions.create(
        #     model="gpt-4o",
        #     temperature=0.3,
        #     messages=[
        #         {"role": "system", "content": (
        #             "You are a scientific writing assistant helping summarize and analyze academic papers. "
        #             "Structure the output into clearly labeled sections. Each section MUST begin with [[Section Name]] on its own line. "
        #             "Sections: Intuitive Understanding, Method Breakdown, Novelties / Contributions, Critiques, Related Reading. "
        #             "Write clearly for an advanced undergraduate audience. Use bullet points if appropriate. DO NOT include LaTeX or math equations."
        #         )},
        #         {"role": "user", "content": (
        #             f"Summarize and explain the following academic paper content:\n\n{pdf_text}\n\n"
        #             "Use the following structure exactly, and ensure each section starts with [[Section Name]]:\n\n"
        #             "[[Intuitive Understanding]]\n"
        #             "Describe the core idea of the paper with conceptual depth and clarity. "
        #             "Explain the reasoning or motivation behind the approach in a way that reveals why it works, not just what it does. "
        #             "Write as if speaking to an intelligent undergraduate student — assume curiosity, not prior technical knowledge. "
        #             "Avoid metaphors and analogies, but aim to build real understanding through clear logic and plain language.\n\n"
        #             "[[Method Breakdown]]\n"
        #             "Describe the main techniques or pipeline steps used in the paper.\n\n"
        #             "[[Novelties / Contributions]]\n"
        #             "List what makes this work new, better, or different.\n\n"
        #             "[[Critiques]]\n"
        #             "Note assumptions, weaknesses, or areas for improvement.\n\n"
        #             "[[Related Reading]]\n"
        #             "Suggest 2-3 related topics or papers worth reading next."
        #         )}
        #     ]
        # )

        # generated_content = response.choices[0].message.content.strip()

        # # Parse into Notion blocks
        # section_blocks = []
        # current_section = None
        # section_heading_map = {
        #     "intuitive understanding": "🧠 Intuitive Understanding",
        #     "method breakdown": "⚙️ Method Breakdown",
        #     "novelties / contributions": "🌟 Novelties / Contributions",
        #     "critiques": "🧪 Critiques",
        #     "related reading": "📚 Related Reading"
        # }

        # for line in generated_content.splitlines():
        #     line = line.strip()
        #     if not line:
        #         continue
        #     if line.startswith("[[") and line.endswith("]]"):
        #         section_key = line[2:-2].strip().lower()
        #         readable_title = section_heading_map.get(section_key, section_key.title())
        #         current_section = readable_title
        #         section_blocks.append({
        #             "object": "block",
        #             "type": "heading_2",
        #             "heading_2": {
        #                 "rich_text": [{"type": "text", "text": {"content": readable_title}}]
        #             }
        #         })
        #     else:
        #         section_blocks.append({
        #             "object": "block",
        #             "type": "paragraph",
        #             "paragraph": {
        #                 "rich_text": [{"type": "text", "text": {"content": line}}]
        #             }
        #         })

        # # Add structured sections after base layout
        # notion.blocks.children.append(block_id=parent_id, children=section_blocks)

        # return "✅ 'Paper Summary' page updated with paper info and layout."