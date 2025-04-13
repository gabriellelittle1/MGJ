import os
import requests
from pathlib import Path
from typing import List, Dict, ClassVar, Type
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from portia.cli import CLIExecutionHooks
from portia import *
import re

def strip_latex(text: str) -> str:
    """
    Remove LaTeX-style commands and math blocks from text.
    
    Args:
        text (str): Text potentially containing LaTeX formatting.
    
    Returns:
        str: Cleaned text.
    """
    text = re.sub(r"\$.*?\$", "", text)  # remove inline math
    text = re.sub(r"\\[a-zA-Z]+\{.*?\}", "", text)  # remove commands like \text{...}
    text = re.sub(r"\\[a-zA-Z]+", "", text)  # remove commands like \mathrm
    text = re.sub(r"[^a-zA-Z0-9\s\-]", "", text)  # keep letters/numbers/spaces/hyphens
    return text.strip()

def make_safe_filename(title: str, max_length: int = 25) -> str:
    """
    Create a safe file name from the paper title.
    
    Args:
        title (str): The title of the paper.
        max_length (int, optional): Maximum length of the file name. Defaults to 25.
    
    Returns:
        str: A sanitized file name ending with .pdf.
    """
    # Remove illegal characters
    cleaned = re.sub(r'[\\/*?:"<>|]', "", title)
    # Replace spaces with underscores
    cleaned = cleaned.replace(" ", "_")
    # Trim and limit length
    cleaned = cleaned.strip()[:max_length]
    return cleaned + ".pdf"

class DownloadPaperSchema(BaseModel):
    """
    Input schema for DownloadPaperTool.
    
    Expected input format:
    {
      "papers": [
        {
          "title": "Paper Title",
          "link": "https://example.com/paper.pdf",
          "summary": "A brief summary of the paper."
        },
        ...
      ]
    }
    """
    papers: List[Dict[str, str]] = Field(
        ...,
        description=(
            "A list of papers, each represented as a dictionary with keys 'title', 'link', and 'summary'. "
            "For example: {'title': 'Example Paper', 'link': 'https://example.com/paper.pdf', 'summary': 'A brief summary.'}"
        )
    )

class DownloadPaperTool(Tool[str]):
    id: ClassVar[str] = "download_tool"
    name: ClassVar[str] = "Download Tool"
    description: ClassVar[str] = (
        "Downloads the papers from the provided URLs and stores them in the 'papers' folder. "
        "Input must be a dictionary with a key 'papers' mapping to a list of paper dictionaries."
    )
    args_schema: Type[BaseModel] = DownloadPaperSchema
    output_schema: ClassVar[tuple[str, str]] = ("str", "A confirmation message indicating success.")

    def run(self, context: ToolRunContext, **kwargs) -> str:
        """
        Accepts keyword arguments so that even if the orchestration engine sends a parameter
        named 'papers', it will be caught in kwargs. Then, validate the input using the Pydantic model.
        """
        # Validate and process the input
        validated_input = DownloadPaperSchema(**kwargs)
        papers = validated_input.papers

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
            pdf_name = make_safe_filename(title)
            pdf_path = target_path / pdf_name
            if not pdf_path.exists():
                try:
                    print(f"ℹ️ Downloading '{title}' from {pdf_url}")
                    response = requests.get(pdf_url)
                    response.raise_for_status()
                    with open(pdf_path, "wb") as f:
                        f.write(response.content)
                    count += 1
                except Exception as e:
                    print(f"❌ Failed to download '{title}': {e}")
        
        return f"✅ Downloaded {count} paper{'s' if count != 1 else ''} into the '{folder_name}' folder"