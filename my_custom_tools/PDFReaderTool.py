from pathlib import Path
import fitz  # PyMuPDF
from pydantic import BaseModel
from portia import Tool, ToolHardError, ToolRunContext
from typing import ClassVar


class PDFReaderToolSchema(BaseModel):
    """No input needed. Reads all PDFs from the papers folder."""
    pass


class PDFReaderTool(Tool[dict[str, str]]):
    """Reads and returns full text from all PDFs in the ./papers/ folder."""

    id: ClassVar[str] = "pdf_reader_tool"
    name: ClassVar[str] = "PDF reader tool"
    description: ClassVar[str] = "Reads all PDFs from the local 'papers' folder and returns their full text"
    args_schema = PDFReaderToolSchema
    output_schema: ClassVar[tuple[str, str]] = ("dict", "Dictionary of filename -> full text")

    def run(self, ctx: ToolRunContext) -> dict[str, str]:
        """Extracts and returns full text from all PDFs in the ./papers folder."""
        papers_dir = Path(__file__).parent / "papers"
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
        """Extracts and cleans text from a PDF file."""
        text = []
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc):
                page_text = page.get_text("text")
                cleaned_text = self._remove_arxiv_footer(page_text)
                text.append(f"--- Page {page_num + 1} ---\n{cleaned_text.strip()}")
        return "\n\n".join(text)

    def _remove_arxiv_footer(self, text: str) -> str:
        """Removes common arXiv-style footers."""
        lines = text.splitlines()
        return "\n".join(
            line for line in lines
            if "arxiv" not in line.lower() and "preprint" not in line.lower()
        )
