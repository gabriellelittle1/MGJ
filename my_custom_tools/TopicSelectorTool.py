from typing import ClassVar, List, Union
from pydantic import BaseModel, Field
from portia import Tool, ToolRunContext
import re


class TopicSelectorToolSchema(BaseModel):
    raw_topics: Union[str, List[str]] = Field(
        ..., description="List of topics (numbered or unnumbered) to prompt the user for selection."
    )


class TopicSelectorTool(Tool[List[str]]):
    id: ClassVar[str] = "topic_selector_tool"
    name: ClassVar[str] = "Topic Selector Tool"
    description: ClassVar[str] = "Prompts the user to choose from a list of topics."
    args_schema = TopicSelectorToolSchema
    output_schema: ClassVar[tuple[str, str]] = ("list", "List of user-selected topics")

    def run(self, ctx: ToolRunContext, raw_topics: Union[str, List[str]]) -> List[str]:
        if isinstance(raw_topics, str):
            topics = self._parse_lines(raw_topics)
        else:
            topics = raw_topics

        if not topics:
            raise ValueError("No topics to choose from.")

        clean_topics = [self._clean_topic(t) for t in topics]

        print("\n📚 Please choose one or more topics to learn about:")
        for i, topic in enumerate(clean_topics, 1):
            print(f"{i}. {topic}")

        choice_str = input("Enter topic numbers separated by commas (e.g. 1,3,4):\n")
        try:
            indices = [int(i.strip()) - 1 for i in choice_str.split(",")]
            selected = [clean_topics[i] for i in indices if 0 <= i < len(clean_topics)]
            return selected
        except Exception as e:
            raise ValueError(f"Invalid input: {e}")


    def _parse_lines(self, text: str) -> List[str]:
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        parsed = []
        for line in lines:
            if "." in line:
                _, after = line.split(".", 1)
                parsed.append(after.strip())
            else:
                parsed.append(line)
        return parsed
    
    def _clean_topic(self, topic: str) -> str:
        return re.sub(r"^\s*\d+[\.\)]\s*", "", topic)

