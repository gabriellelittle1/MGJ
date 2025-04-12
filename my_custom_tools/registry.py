"""Registry containing my custom tools."""

from portia import InMemoryToolRegistry
from my_custom_tools.arXivTool import ArXivTool
from my_custom_tools.DownloadTool import DownloadPaperTool
from my_custom_tools.PDFReaderTool import PDFReaderTool
from my_custom_tools.TopicSelectorTool import TopicSelectorTool
from my_custom_tools.NotionTool import NotionTool
from my_custom_tools.YouTubeTool import YouTubeTool

custom_tool_registry = InMemoryToolRegistry.from_local_tools(
    [
        ArXivTool(), 
        DownloadPaperTool(),
        PDFReaderTool(),
        TopicSelectorTool(),
        NotionTool(),
        YouTubeTool(),
    ],
)