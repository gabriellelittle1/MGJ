from dotenv import load_dotenv
from portia.cli import CLIExecutionHooks
from portia import *
import requests
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Literal
import os
import json
from notion_client import Client
from my_custom_tools.registry import custom_tool_registry
from portia.clarification import InputClarification
from portia.plan_run import PlanRunState
import shutil

load_dotenv(override=True)

# Fetch the Notion API key and set up client
notion_api_key = os.getenv("NOTION_API_KEY")
notion_parent_id = os.getenv("NOTION_PARENT_ID")

# Initialize the Notion client
notion = Client(auth=notion_api_key)



def planner(topic, constraints, further_reading = False, youtube_videos = False, quiz = False):
    if constraints is None:
        constraints = []
    
    my_config = Config.from_default()
    complete_tool_registry = PortiaToolRegistry(my_config) + custom_tool_registry

    portia = Portia(config = my_config,
                  tools = complete_tool_registry)
    
    # Define the path to your papers folder
    papers_folder = "papers"
    
    # Ensure the papers folder exists
    if not os.path.exists(papers_folder):
        os.makedirs(papers_folder)
    else:
        # If it exists, clear its contents
        for filename in os.listdir(papers_folder):
            file_path = os.path.join(papers_folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # remove file or symlink
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # remove directory
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

    task = (
            lambda : f"""You are a research assistant running these tasks: 
                      - Find and download 1 paper on the topic of {topic} using the ArXivTool. 
                      - Run the PDFReaderTool to extract the full text from the pdfs in the local folder.
                     - Use PSTool to create and populate the Page Summary subpage.
                      - From the text, extract the core mathematical and scientific concepts required 
                        to understand the paper. Focus only on generalizable topics that could be included 
                        in a learning pathway or curriculum—avoid content specific to the study's location, 
                        data, or outcomes. List only the overarching topics, with no explanations or extra text.
                      - Then use the TopicSelectorTool on these topics. 
                      - Then use the Notion Tool to create Notion pages for these topics.
                      - {youtube_videos * "Use the YouTubeTool to find videos on each topic."}
                      - {further_reading * "Use the RecReadTool to find resources on each topic."}
                      - {quiz * "Use the QuizTool to create quizzes for each topic."}
                      
                        Take into account these constraints: {constraints}
                      """

        )

    
    
    with execution_context(end_user_id="learning_enthusiast"):
        plan = portia.plan(task())
        steps = [step.model_dump_json(indent=2) for step in plan.steps]
        
        return plan, steps, task, portia  

def format_plan_steps(raw_json_line):
    steps = []
    for i, line in enumerate(raw_json_line):
        try:
            step = json.loads(line)
            task = step.get("task", "[No task found]")
            steps.append(f"{task}")
        except json.JSONDecodeError:
            steps.append(f"Step {i + 1}: Invalid JSON step")

    return steps
  


portia = None
run = None

def run_RAI(task_fn, clarification_response=None, clarification_context=None, extract_user_guidance:bool = False):
    global portia
    global run
    
    my_config = Config.from_default()
    complete_tool_registry = PortiaToolRegistry(my_config) + custom_tool_registry

    if portia is None:
        portia = Portia(
            config=my_config,
            tools=complete_tool_registry
        )

        plan = portia.plan(task_fn())
        run = portia.run_plan(plan)
        clarification = run.get_outstanding_clarifications()[0]
        return{
            "clarification_required": True,
            "message": clarification.user_guidance,
            "plan_run_id": run.id,
            "argument_name": clarification.argument_name,
        }

    
    if run is None:
        # print("bad penis")
        raise Exception(f"Plan run failed with bad penis")
    
       
    
    while run.state == PlanRunState.NEED_CLARIFICATION:
        clarification = run.get_outstanding_clarifications()[0]
        run = portia.resolve_clarification(clarification, str(clarification_response), run)
        run = portia.resume(run)

    
    # Handle failed plan
    if run.state != PlanRunState.COMPLETE:
        raise Exception(f"Plan run failed with state {run.state}")
    
        # If successful
    return {
        "clarification_required": False,
        "notion_parent_id": notion_parent_id,
        "output": "Your plan has executed successfully!",
    }

    

