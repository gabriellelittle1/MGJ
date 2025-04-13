from typing import ClassVar, List, Optional
from pydantic import BaseModel, Field
from portia import Tool, ToolRunContext
from portia.clarification import InputClarification  # <- This is what you use!


class TopicSelectorToolSchema(BaseModel):
    raw_topics: List[str] = Field(..., description="List of topics to choose from")
    selected_indices: Optional[str] = Field(
        default=None,
        description="Comma-separated topic numbers (e.g. '1, 3, 5')"
    )

class TopicSelectorTool(Tool[List[str]]):
    id: ClassVar[str] = "topic_selector_tool"
    name: ClassVar[str] = "Topic Selector Tool"
    description: ClassVar[str] = "Prompts the user to choose topics by number"
    args_schema = TopicSelectorToolSchema
    output_schema: ClassVar[tuple[str, str]] = ("list", "The topics selected by the user")

    def run(self, ctx: ToolRunContext, raw_topics: List[str], selected_indices: Optional[str] = None) -> List[str] | InputClarification:

        if selected_indices is not None:
            try:
                indices = [int(i.strip()) - 1 for i in selected_indices.split(",")]
                selected = [raw_topics[i] for i in indices if 0 <= i < len(raw_topics)]
                return selected
            except Exception as e:
                raise ValueError(f"Invalid input: {e}")

        numbered_list = "\n".join(f"{i+1}. {topic}" for i, topic in enumerate(raw_topics))

        return InputClarification(
            plan_run_id=ctx.plan_run_id,
            argument_name="selected_indices",
            user_guidance=(
                "Please enter the numbers of the topics you'd like to learn about, "
                "separated by commas (e.g. 1, 3, 5):\n\n" + numbered_list
            ),
        )
