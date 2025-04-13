from typing import Generic, TypeVar, List, ClassVar, Dict
from portia import * 
from dotenv import load_dotenv
from portia.cli import CLIExecutionHooks
import requests
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List
from notion_client import Client
import os
import openai
import re

class QuizToolSchema(BaseModel): 
    """Input Schema for QuizTool."""
    topics: List[Dict[str, str]] = Field(description="The list of topic pages, their IDs, and their page contents.")

class QuizTool(Tool[None]):
    """ Quiz Tool for creating quizzes for topics and creating separate pages for the quizzes. 
        It will base the quizzes on the lessons and topics provided.
    """

    id: ClassVar[str] = "Quiz_tool"
    name: ClassVar[str] = "Quiz Tool"
    description: ClassVar[str] = "A tool that creates quizzes for topics and creates separate pages for the quizzes." 
    args_schema = QuizToolSchema
    output_schema: ClassVar[tuple[str, str]] = (
        "str",
        "Confirmation of Quiz Creation"
    )

    def run(self, context: ToolRunContext, topics: List[Dict[str, str]]) -> str: 
        """Creates a quiz for each topic and creates separate pages for the quizzes."""
        for topic in topics: 
            quiz = self.create_quiz(topic)
            self.create_quiz_page(quiz, topic)
        return "Quizzes created successfully!"

    def create_quiz(self, topic: dict) -> List[Dict[str, str]]: 
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "You are a tutor generating quiz questions from a lesson.\n"
                    "⚠️ RULES FOR MATH FORMATTING:\n"
                    "- Use ONLY inline LaTeX like this: \\( ... \\)\n"
                    "- DO NOT use display math (\\[...\\], $$...$$, or {{math: ...}})\n"
                    "- DO NOT wrap inline math in extra brackets like (\\( ... \\)) or [\\( ... \\)]\n"
                    "- Use valid LaTeX: \\frac, \\int, \\sum, subscripts/superscripts, etc.\n\n"
                    "Each question should follow this exact format:\n"
                    "Question 1: <question text>\n"
                    "Options:\n"
                    "A. ...\nB. ...\nC. ...\nD. ...\n"
                    "Answer: A"
                )},
                {"role": "user", "content": f"Create a 5-question multiple choice quiz on the topic '{topic['topic']}' using this content: {topic['content']}"}
            ],
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()

        quiz_items = []
        question_blocks = re.split(r'\n(?=Question \d+:)', content)

        for block in question_blocks:
            block = block.strip()
            if not block:
                continue
            try:
                q_match = re.match(r"Question \d+:\s*(.*?)\nOptions:", block, re.DOTALL)
                options_match = re.search(r"Options:(.*?)Answer:", block, re.DOTALL)
                a_match = re.search(r"Answer:\s*([ABCD])", block)

                if not (q_match and options_match and a_match):
                    continue

                question = q_match.group(1).strip()
                raw_opts = options_match.group(1).strip().splitlines()
                options = [opt[2:].strip() for opt in raw_opts if len(opt) > 2 and opt[1] == '.']

                if len(options) == 4:
                    quiz_items.append({
                        "question": question,
                        "options": options,
                        "answer": a_match.group(1)
                    })
            except Exception:
                continue

        return quiz_items[:5]  # Ensure exactly 5 questions

    def render_option_blocks(self, option_text: str, label: str, is_correct: bool = False):
        color = "green" if is_correct else "default"
        suffix = " ✅" if is_correct else ""

        parts = []
        pattern = r'(\\\(.*?\\\))'
        last_end = 0
        for match in re.finditer(pattern, option_text):
            start, end = match.span()
            if start > last_end:
                parts.append({"type": "text", "text": {"content": option_text[last_end:start]}})
            expression = match.group(1)[2:-2].strip()
            parts.append({"type": "equation", "equation": {"expression": expression}})
            last_end = end

        if last_end < len(option_text):
            parts.append({"type": "text", "text": {"content": option_text[last_end:] + suffix}})

        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": f"{label}. "}, "annotations": {"bold": True, "color": color}},
                    *parts
                ]
            }
        }

    def render_question_title(self, text: str) -> List[Dict]:
        parts = []
        pattern = r'(\\\(.*?\\\))'
        last_end = 0
        for match in re.finditer(pattern, text):
            start, end = match.span()
            if start > last_end:
                parts.append({"type": "text", "text": {"content": text[last_end:start]}})
            expression = match.group(1)[2:-2].strip()
            parts.append({"type": "equation", "equation": {"expression": expression}})
            last_end = end
        if last_end < len(text):
            parts.append({"type": "text", "text": {"content": text[last_end:]}})
        return parts

    def create_quiz_page(self, quiz: List[Dict[str, str]], topic: dict) -> None:
        notion_api_key = os.getenv("NOTION_API_KEY")
        notion = Client(auth=notion_api_key)
        parent_id = topic["page_id"]

        blocks = []
        answer_blocks = []
        option_labels = ["A", "B", "C", "D"]

        for question in quiz: 
            question_title_rich = self.render_question_title(question["question"])

            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": question_title_rich}
            })

            answer_blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": question_title_rich}
            })

            correct_index = option_labels.index(question["answer"])

            for i in range(4):
                blocks.append(self.render_option_blocks(question["options"][i], option_labels[i]))
                answer_blocks.append(self.render_option_blocks(question["options"][i], option_labels[i], is_correct=(i == correct_index)))

            input_block = {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Your Answer: "}, "annotations": {"bold": True, "color": "blue"}},
                        {"type": "text", "text": {"content": ""}}
                    ]
                }
            }
            blocks.append(input_block)

        notion.pages.create(
            parent={"type": "page_id", "page_id": parent_id},
            properties={"title": [{"type": "text", "text": {"content": "📝 Quiz !"}}]},
            children=blocks
        )

        notion.pages.create(
            parent={"type": "page_id", "page_id": parent_id},
            properties={"title": [{"type": "text", "text": {"content": "🎯 Quiz Solutions"}}]},
            children=answer_blocks
        )