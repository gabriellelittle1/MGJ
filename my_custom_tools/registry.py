"""Registry containing my custom tools."""

from portia import InMemoryToolRegistry
from my_custom_tools.arXivTool import ArXivTool
from my_custom_tools.DownloadTool import DownloadPaperTool
from my_custom_tools.PDFReaderTool import PDFReaderTool
from my_custom_tools.TopicSelectorTool import TopicSelectorTool
from my_custom_tools.NotionTool import NotionTool
from my_custom_tools.YouTubeTool import YouTubeTool
from my_custom_tools.RecReadTool import RecReadTool
from my_custom_tools.Paper_Summary0 import PaperSummary0Tool
from my_custom_tools.QuizTool import QuizTool

custom_tool_registry = InMemoryToolRegistry.from_local_tools(
    [
        ArXivTool(), 
        DownloadPaperTool(),
        PDFReaderTool(),
        TopicSelectorTool(),
        NotionTool(),
        YouTubeTool(),
        RecReadTool(),
        PaperSummary0Tool(),
        QuizTool(),
    ],
)