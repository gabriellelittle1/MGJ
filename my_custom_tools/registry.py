"""Registry containing my custom tools."""

from portia import InMemoryToolRegistry
from my_custom_tools.arXivTool import ArXivTool
from my_custom_tools.DownloadTool import DownloadPaperTool
from my_custom_tools.PDFReaderTool import PDFReaderTool

custom_tool_registry = InMemoryToolRegistry.from_local_tools(
    [
        ArXivTool(), 
        DownloadPaperTool(),
        PDFReaderTool(),
    ],
)