import os
import requests
from pathlib import Path
from typing import List, Dict, ClassVar
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from portia.cli import CLIExecutionHooks
from portia import *
import re

def strip_latex(text: str) -> str:
    # Remove all LaTeX-style commands and math blocks
    text = re.sub(r"\$.*?\$", "", text)  # remove inline math
    text = re.sub(r"\\[a-zA-Z]+\{.*?\}", "", text)  # remove commands like \text{...}
    text = re.sub(r"\\[a-zA-Z]+", "", text)  # remove commands like \mathrm
    text = re.sub(r"[^a-zA-Z0-9\s\-]", "", text)  # keep letters/numbers/spaces/hyphens
    return text.strip()

def make_safe_filename(title: str, max_length: int = 25) -> str:
    # Remove illegal characters
    cleaned = re.sub(r'[\\/*?:"<>|]', "", title)
    # Replace spaces with underscores
    cleaned = cleaned.replace(" ", "_")
    # Trim and limit length
    cleaned = cleaned.strip()[:max_length]
    return cleaned + ".pdf"

class DownloadPaperSchema(BaseModel):
    """Input schema for DownloadPaperTool."""
    papers: List[Dict[str, str]] = Field(
        ..., 
        description="A list of dicts, each with 'title', 'link', and 'summary'."
    )

class DownloadPaperTool(Tool[str]):
    """Download the given papers from urls and create the papers folder."""

    id: ClassVar[str] = "download_tool"
    name: ClassVar[str] = "download Tool"
    description: ClassVar[str] = "Download the papers from the given urls and create the papers folder."
    args_schema: type[BaseModel] = DownloadPaperSchema
    output_schema: ClassVar[tuple[str, str]] = ("str", "A confirmation message indicating success.")

    def run(self, context: ToolRunContext, papers: List[Dict[str, str]]) -> str:

        print("DownloadPaperTool initialized")

        folder_name = "papers"
        target_path = Path(folder_name)
        target_path.mkdir(parents=True, exist_ok=True)
        count = 0
        for paper in papers:
            title = strip_latex(paper["title"])
            pdf_url = paper["link"]
            if not pdf_url:
                print(f"❌ Skipping paper with missing pdf_url: {title}")
                continue
            pdf_name = make_safe_filename(re.sub(r'[\\/*?:"<>|]', "", title))
            pdf_path = target_path / pdf_name
            if not pdf_path.exists():
                count += 1
                response = requests.get(pdf_url)
                with open(pdf_path, "wb") as f:
                    f.write(response.content)
        
        return f"✅ Downloaded {count} paper{'s' * (count > 1)} into the 'papers' folder"