from dotenv import load_dotenv
from portia.cli import CLIExecutionHooks
from portia import *
import requests
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, ClassVar, Dict
from notion_client import Client
import os
import openai
import json
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
        # Create a quiz for each topic

        for topic in topics: 
            quiz = self.create_quiz(topic)
            self.create_quiz_page(quiz, topic)

        return "Quizzes created successfully!"

    def create_quiz(self, topic: dict) -> List[Dict[any, str]]: 
        """Creates a quiz for the given topic and returns the quiz URL."""
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        quiz = {}
        quiz["topic"] = topic["topic"]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", 
                 "content": (
                        "You are a tutor who creates quizzes for students on given lessons. "
                        "All math must be written using inline LaTeX formatted as \\( ... \\). "
                        "Do NOT use display math like \\[...\\], $$...$$, or {{math: ...}}. "
                        "Do NOT wrap equations in square brackets [ ... ] or parentheses like (\\( ... \\)). "
                        "Only use valid LaTeX commands (e.g., \\frac, \\int, \\sum, \\left(, \\right)). "
                        "Each Question should be a multiple choice question with 4 options. "
                        "Output each question in the following format: "
                        "{\"question\": \"Question text\", \"options\": [\"Option A\", \"Option B\", \"Option C\", \"Option D\"], \"answer\": \"Correct answer (one of A, B, C, D)\"}."
                            )},
                {"role": "user", "content": (
                    f"Write a comprehensive multiple choice quiz on this lesson: {topic['content']} on this topic: {topic['topic']}.\n"
                )}
            ],
            temperature=0.5
        )
        
        data = response.choices[0].message.content
        escaped_data = data.replace('\\', '\\\\')
        pattern = r'\{.*?"question":.*?"options":\s*\[.*?\].*?"answer":\s*".*?"\}'
        # Find all JSON-like strings
        matches = re.findall(pattern, escaped_data, re.DOTALL) 
        quiz = [json.loads(match) for match in matches]
        
        return quiz
    
    def create_quiz_page(self, quiz: List[Dict[any, str]], topic: dict) -> None:
        notion_api_key = os.getenv("NOTION_API_KEY")
        notion = Client(auth=notion_api_key)
        
        parent_id = topic["page_id"]

        blocks = []
        answer_blocks = []

        for question in quiz: 
            title_block = {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": question["question"]}}]
                }
            }

            blocks.append(title_block)
            answer_blocks.append(title_block)

            option_labels = ["A", "B", "C", "D"]
            correct_index = option_labels.index(question["answer"])

            for i in range(4):
                # Normal quiz view (no indication of correct answer)
                option_block = {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": f"{option_labels[i]}. "},
                                "annotations": {"bold": True, "color": "default"}
                            },
                            {
                                "type": "text",
                                "text": {"content": question["options"][i]},
                                "annotations": {"bold": False, "color": "default"}
                            }
                        ]
                    }
                }
                blocks.append(option_block)

                # Answer view: highlight correct answer
                is_correct = (i == correct_index)
                answer_option_block = {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": f"{option_labels[i]}. "},
                                "annotations": {
                                    "bold": True,
                                    "color": "green" if is_correct else "default"
                                }
                            },
                            {
                                "type": "text",
                                "text": {
                                    "content": question["options"][i] + (" ✅" if is_correct else "")
                                },
                                "annotations": {
                                    "bold": False,
                                    "color": "green" if is_correct else "default"
                                }
                            }
                        ]
                    }
                }
                answer_blocks.append(answer_option_block)

            # Input field for user answer (only in quiz version)
            input_block = {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Your Answer: "},
                            "annotations": {"bold": True, "color": "blue"}
                        },
                        {
                            "type": "text",
                            "text": {"content": ""}
                        }
                    ]
                }
            }
            blocks.append(input_block)

        # Create the quiz page
        response1 = notion.pages.create(
            parent={"type": "page_id", "page_id": parent_id},
            properties={"title": [{"type": "text", "text": {"content": "📝 Quiz !"}}]},
            children=blocks
        )

        # Create the answer key page
        response2 = notion.pages.create(
            parent={"type": "page_id", "page_id": parent_id},
            properties={"title": [{"type": "text", "text": {"content": "🎯 Quiz Solutions"}}]},
            children=answer_blocks
        )

        return 

