import os
import requests
from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from portia.cli import CLIExecutionHooks
from portia import *
import re

class DownloadPaperSchema(Tool):
    """Input schema for DownloadPaper Tool"""
    papers: list[dict[str, str]] = Field(
        ..., 
        description="A list of dicts, each with 'title' and 'pdf_url'."
    )

class DownloadPaperTool(BaseModel):
    """Download the given papers from urls and create the papers folder."""

    id: str = "download_tool"
    name: str = "download Tool"
    description: str = "Download the papers from the given urls and create the papers folder."
    args_schema: type[BaseModel] = DownloadPaperSchema
    output_schema: tuple[str, str] = ("str", "A confirmation message indicating success.")

    def run(self, context: ToolRunContext, papers: List[Dict[str, str]]) -> str:

        folder_name = "papers"
        target_path = Path(folder_name)
        target_path.mkdir(parents=True, exist_ok=True)
        count = 0
        for paper in papers:
            title = paper["title"]
            pdf_url = paper["link"]
            if not pdf_url:
                print(f"❌ Skipping paper with missing pdf_url: {title}")
                continue
            new_title = title.replace(" ", "_")
            pdf_name = re.sub(r'[\\/*?:"<>|]', "", new_title) + ".pdf"
            pdf_path = target_path / pdf_name
            if not pdf_path.exists():
                count += 1
                response = requests.get(pdf_url)
                with open(pdf_path, "wb") as f:
                    f.write(response.content)
        
        return f"✅ Downloaded {count} paper{'s' * (count > 1)} into the 'papers' folder"