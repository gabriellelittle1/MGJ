from dotenv import load_dotenv
from portia.cli import CLIExecutionHooks
from portia import *
import requests
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, ClassVar, Dict

class ArXivToolSchema(BaseModel):
    """Input schema for ArXiv Tool"""
    topic: str = Field(..., description="The topic to learn about")

# Step 2: Define the Tool
class ArXivTool(Tool[List[Dict[str, str]]]):
    """Find the most relevant papers on arXiv for a given topic."""

    id: ClassVar[str] = "arxiv_tool"
    name: ClassVar[str] = "arXiv Tool"
    description: ClassVar[str] = "Get the most relevant papers on arXiv for a given topic."
    args_schema = ArXivToolSchema
    output_schema: ClassVar[tuple[str, str]] = (
        "list[dict[str, str]]",
        "A list of dictionaries containing paper data like title, authors, and pdf_url"
    )

    def run(self, context: ToolRunContext, topic: str) -> List[Dict[str, str]]:
    def run(self, context: ToolRunContext, topic: str) -> List[Dict[str, str]]:
        
        """Run the arXiv Tool."""
        max_results = 1
        max_results = 1
        base_url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{topic}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }

        response = requests.get(base_url, params=params)
        root = ET.fromstring(response.text)

        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('atom:entry', ns)

        papers = []
        for entry in entries:
            paper = {}
            paper['title'] = entry.find('atom:title', ns).text.strip()
            paper['summary'] = entry.find('atom:summary', ns).text.strip()
            arxiv_id = entry.find('atom:id', ns).text.strip().split('/')[-1]
            paper['link'] = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            papers.append(paper)
            
            
        return papers