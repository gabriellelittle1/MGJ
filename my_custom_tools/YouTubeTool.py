from dotenv import load_dotenv
from portia.cli import CLIExecutionHooks
from portia import *
import requests
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, ClassVar, Dict, Literal
from notion_client import Client
import os
load_dotenv(override=True)


class YouTubeToolSchema(BaseModel): 

    """Input Schema for YoutubeTool."""
    topics: List[Dict[str, str]] = Field(description="The list of dictionaries (output from the NotionTool), each with 'topic', 'page_id' and 'content' keys.")

class YouTubeTool(Tool[None]):

    """A tool to find YouTube videos for given topics, and link them to Notion."""

    id: ClassVar[str] = "youtube_tool"
    name: ClassVar[str] = "YouTube Tool"
    description: ClassVar[str] = "A tool to find YouTube videos for given topics, and link them to Notion."
    args_schema = YouTubeToolSchema
    output_schema: ClassVar[tuple[str, str]] = (
        "None",
        "This tool does not return anything."
    )

    def run(self, context, topics: List[Dict[str, str]]) -> None:
        """Adds multiple YouTube video links to Notion pages for each topic."""

        max_results = 3

        notion_api_key = os.getenv("NOTION_API_KEY")
        youtube_api_key = os.getenv("GOOGLE_API_KEY")
        
        if not notion_api_key or not youtube_api_key:
            raise EnvironmentError("Missing NOTION_API_KEY or GOOGLE_API_KEY")

        notion = Client(auth=notion_api_key)

        for page in topics:
            topic = page["topic"]
            page_id = page["page_id"]
            query = f"Explain {topic}"

            url = (
                f'https://www.googleapis.com/youtube/v3/search'
                f'?part=snippet&type=video&q={query}'
                f'&maxResults={max_results}&key={youtube_api_key}'
            )

            response = requests.get(url).json()
            items = response.get("items", [])

            if not items:
                print(f"No videos found for topic: {topic}")
                continue

            video_blocks = []

            # Add a heading before the videos
            video_blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "🎥 Recommended Videos"},
                            "annotations": {"bold": True}
                        }
                    ]
                }
            })

            for item in items:
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                description = item["snippet"]["description"]
                channel = item["snippet"]["channelTitle"]
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                video_blocks.extend([
                    # Video title + link
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"▶ {title} by {channel} – ",
                                        "link": {"url": video_url}
                                    },
                                    "annotations": {
                                        "bold": True,
                                        "color": "blue"
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "Watch",
                                        "link": {"url": video_url}
                                    },
                                    "annotations": {
                                        "italic": True,
                                        "color": "blue"
                                    }
                                }
                            ]
                        }
                    },
                    # Short description
                    {
                        "object": "block",
                        "type": "quote",
                        "quote": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": description[:200] + "...",
                                    },
                                    "annotations": {
                                        "color": "gray"
                                    }
                                }
                            ]
                        }
                    },
                    # Spacer block (optional)
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": []
                        }
                    }
                ])

            # Append everything to the Notion page
            notion.blocks.children.append(
                block_id=page_id,
                children=video_blocks
            )
        return 