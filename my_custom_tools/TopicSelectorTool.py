from typing import ClassVar, List, Union
from pydantic import BaseModel, Field
from portia import Tool, ToolRunContext, ToolHardError, MultipleChoiceClarification


class TopicSelectorToolSchema(BaseModel):
    raw_topics: str = Field(..., description="A numbered list of topics as a single string")


class TopicSelectorTool(Tool[List[str]]):
    id: ClassVar[str] = "topic_selector_tool"
    name: ClassVar[str] = "Topic Selector Tool"
    description: ClassVar[str] = "Lets the user choose from a numbered list of LLM-generated topics"
    args_schema = TopicSelectorToolSchema
    output_schema: ClassVar[tuple[str, str]] = ("list", "List of topics the user selected")

    def run(self, ctx: ToolRunContext, raw_topics: str) -> Union[List[str], MultipleChoiceClarification]:
        topics = self.parse_numbered_list(raw_topics)

        if not topics:
            raise ToolHardError("No valid topics found in the input.")

        return MultipleChoiceClarification(
            plan_run_id=ctx.plan_run_id,
            argument_name="raw_topics",
            user_guidance="Pick one or more topics you'd like to explore:",
            options=topics,
            allow_multiple=True
        )

    def parse_numbered_list(self, raw_text: str) -> list[str]:
        lines = raw_text.strip().splitlines()
        topics = []
        for line in lines:
            if "." in line:
                parts = line.split(".", 1)
                topic = parts[1].strip()
                if topic:
                    topics.append(topic)
        return topics
