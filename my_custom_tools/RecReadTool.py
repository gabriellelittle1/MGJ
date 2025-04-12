from dotenv import load_dotenv
from portia.cli import CLIExecutionHooks
from portia import *
import requests
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, ClassVar, Dict
from notion_client import Client
import os

class RecReadToolSchema(BaseModel): 

    """Input Schema for RecReadTool."""
    topics: List[Dict[str, str]] = Field(description="The list of topic pages and their IDs.")

class RecReadTool(Tool[None]):

    """A tool to find recommended reading for topics, and link them to Notion."""

    id: ClassVar[str] = "RecRead_tool"
    name: ClassVar[str] = "RecRead Tool"
    description: ClassVar[str] = "A tool to find recommended reading for given topics, and link them to Notion."
    args_schema = RecReadToolSchema
    output_schema: ClassVar[tuple[str, str]] = (
        "str",
        "Confirmation of task completion."
    )

    def run(self, context, topics: List[Dict[str, str]]) -> None:
        """Adds recommended Wikipedia reading to Notion pages for each topic."""

        notion_api_key = os.getenv("NOTION_API_KEY")
        notion = Client(auth=notion_api_key)
        
        output = []

        def truncate_at_sentence(text: str, n: int) -> str:
            """
            Truncates the input text to a maximum of `n` characters,
            ending at the last full stop (.) before the limit.
            Returns an empty string if no full stop is found within range.
            """
            if len(text) <= n:
                return text.strip()

            # Slice up to n characters and find the last full stop
            cutoff = text[:n].rfind(".")

            if cutoff == -1:
                return ""  # Or fallback to first n chars: return text[:n].strip()

            return text[:cutoff + 1].strip()

        for topic in topics:
            topic_name = topic["topic"]
            page_id = topic["page_id"]

            print(f"Processing topic: {topic_name}")

            # Wikipedia API: Search
            search_url = "https://en.wikipedia.org/w/api.php"
            summary_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": topic_name,
                "format": "json"
            }

            search_response = requests.get(search_url, params=search_params).json()
            results = search_response.get("query", {}).get("search", [])

            if not results:
                continue  # Skip this topic if nothing is found

            best_title = results[0]["title"]

            # Wikipedia API: Summary
            summary_response = requests.get(f"{summary_url}{best_title.replace(' ', '_')}")
            if summary_response.status_code != 200:
                continue

            data = summary_response.json()
            wiki_title = data.get("title")
            wiki_summary = data.get("extract")
            wiki_url = data["content_urls"]["desktop"]["page"]


            ### Free Textbooks
            google_books_url = f"https://www.googleapis.com/books/v1/volumes?q={topic_name.replace(' ', '+')}+textbook&maxResults=3"
            books_response = requests.get(google_books_url).json()
            textbooks = []

            for book in books_response.get("items", []):
                info = book["volumeInfo"]
                dictionary = {
                    "title": info.get("title"), 
                    "authors": ", ".join(info.get("authors", [])), 
                    "description": info.get("description", ""), 
                    "link": info.get("infoLink")
                }
                textbooks.append(dictionary)

            if len(textbooks) == 0: 
                textbooks_block = [{
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "No textbooks found for this topic."}
                                }
                            ]
                        }
                    }]

            else: 
                textbooks_block = []
                for book in textbooks: 
                    link_block = {"object": "block", "type": "paragraph","paragraph": 
                                  {
                                      "rich_text": [
                                          {
                                              "type": "text",
                                              "text": {
                                                  "content": f"🔗 {book['title']}" + (f" by {book['authors']}" if book.get('authors') else ""),
                                                  "link": {"url": book['link']}
                                                  },
                                                  "annotations": {
                                                  "color": "blue"
                                                  }
                                            }]
                                    }}
                    content_block = {"object": "block","type": "paragraph", 
                                  "paragraph": {
                                        "rich_text": [
                                            {
                                                "type": "text",
                                                "text": {"content": f"{truncate_at_sentence(book['description'], 400)}"}
                                            }]}}
                    textbooks_block.append(link_block)
                    textbooks_block.append(content_block)

            ### Article / Papers


            # Append blocks directly to Notion page
            notion.blocks.children.append(
                block_id=page_id,
                children=[
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "📘 Recommended Reading"}
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": f"🌐 Web Resources"}
                                }
                            ]
                        }},
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"🔗 {wiki_title} (Wikipedia)",
                                        "link": {"url": wiki_url}
                                    },
                                    "annotations": {
                                        "color": "blue"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": f"{wiki_summary}"}
                                }
                            ]
                        }
                    }, 
                    {
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": f"📚 Textbooks"}
                                }
                            ]
                        }},
                ] + textbooks_block 
            )

            output.append(f"Added reading for '{topic_name}'")

        return "✅ Recommended Reading added to Notion pages successfully."
