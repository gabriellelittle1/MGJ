from pathlib import Path
import fitz  # PyMuPDF
from pydantic import BaseModel
from portia import Tool, ToolHardError, ToolRunContext
from typing import ClassVar, Dict


class PDFReaderToolSchema(BaseModel):
    """No input needed. Reads all PDFs from the papers folder."""
    pass


class PDFReaderTool(Tool[Dict[str, str]]):
    """Reads and returns full text from all PDFs in the ./papers/ folder."""

    id: ClassVar[str] = "pdf_reader_tool"
    name: ClassVar[str] = "PDF reader tool"
    description: ClassVar[str] = "Reads all PDFs from the local 'papers' folder and returns their full text"
    args_schema = PDFReaderToolSchema
    output_schema: ClassVar[tuple[str, str]] = ("dict", "Dictionary of filename -> full text")

    def run(self, ctx: ToolRunContext) -> Dict[str, str]:
        """Extracts and returns full text from all PDFs in the ./papers folder."""
        
        papers_dir = Path.cwd() / "papers"

        if not papers_dir.exists() or not papers_dir.is_dir():
            raise ToolHardError("The 'papers/' folder does not exist.")

        pdf_files = list(papers_dir.glob("*.pdf"))
        if not pdf_files:
            raise ToolHardError("No PDF files found in the 'papers/' folder.")

        texts = {}
        for file_path in pdf_files:
            try:
                full_text = self.read_pdf(file_path)
                texts[file_path.name] = full_text
            except Exception as e:
                texts[file_path.name] = f"Error reading file: {str(e)}"

        return texts

    def read_pdf(self, file_path: Path) -> str:
        """Extracts and cleans text from a PDF file, stopping before References/Bibliography."""
        text = []
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc):
                page_text = page.get_text("text")
                cleaned_text = self._remove_arxiv_footer(page_text)

                #Check for 'References' or 'Bibliography' section header
                if self._is_bibliography_page(cleaned_text):
                    print(f"Stopping at page {page_num + 1} (found References section).")
                    break

                text.append(f"--- Page {page_num + 1} ---\n{cleaned_text.strip()}")
        return "\n\n".join(text)

    def _remove_arxiv_footer(self, text: str) -> str:
        """Removes common arXiv-style footers."""
        lines = text.splitlines()
        return "\n".join(
            line for line in lines
            if "arxiv" not in line.lower() and "preprint" not in line.lower()
        )
    
    def _is_bibliography_page(self, text: str) -> bool:
        """Returns True if the page looks like it's starting the bibliography or references."""
        lowered = text.lower()
        # Check if 'references' or 'bibliography' is a standalone word early in the text
        return (
            "references\n" in lowered
            or lowered.strip().startswith("references")
            or lowered.strip().startswith("bibliography")
        )
    
