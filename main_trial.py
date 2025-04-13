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

load_dotenv(override=True)
# Fetch the Notion API key and set up client
notion_api_key = os.getenv("NOTION_API_KEY")
notion_parent_id = os.getenv("NOTION_PARENT_ID")

# Initialize the Notion client
notion = Client(auth=notion_api_key)

# topic = "Using LLMs for Interior Design"
# constraints = []
# video_preference = False
# rec_reading_preference = False
# ready_to_proceed = False
#mini_project_ideas = False, quiz = False

def planner(topic, constraints, further_reading = False, youtube_videos = False):
    if constraints is None:
        constraints = []
    
    my_config = Config.from_default()
    complete_tool_registry = PortiaToolRegistry(my_config) + custom_tool_registry

    portia = Portia(config = my_config,
                  tools = complete_tool_registry)

    task = (
            lambda : f"""You are a research assistant running these tasks: 
                      - Find and download a paper on the topic of {topic} using the ArXivTool. 
                      - Run the PDFReaderTool to extract the full text from the pdfs in the local folder.
                      - From the full text, extract the core mathematical and scientific concepts required 
                        to understand the paper. Focus only on generalizable topics that could be included 
                        in a learning pathway or curriculum—avoid content specific to the study's location, 
                        data, or outcomes. List only the overarching topics, with no explanations or extra text.
                      - Then use the TopicSelectorTool on these topics. 
                      - Then use the Notion Tool to create Notion pages for these topics.
                      - {youtube_videos * "Use the YouTubeTool to find videos on each topic."}
                      - {further_reading * "Use the RecReadTool to find resources on each topic."}
                      
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
  


# def run_RAI(task_lambda, portia):
    # with execution_context(end_user_id="learning_enthusiast"):
    #     plan = portia.plan(task_lambda())
    #     run = portia.run_plan(plan)

    #     if run.state != PlanRunState.COMPLETE:
    #         return f"Plan failed with state {run.state}"
    
    #     return f"Run was successful. See your learning plan at link"
def run_RAI(plan, clarification_response=None, clarification_context=None):
    my_config = Config.from_default()
    complete_tool_registry = PortiaToolRegistry(my_config) + custom_tool_registry

    portia = Portia(
        config=my_config,
        tools=complete_tool_registry
    )

    if clarification_response and clarification_context:
        # Resume the plan with user's clarification
        # run = portia.run_plan(
        #     plan=None,
        #     clarifications={clarification_context["argument_name"]: clarification_response},
        #     resume_from=clarification_context["plan_run_id"]
        # )
        run = portia.resolve_clarification_by_id(
            plan_run_id=clarification_context["plan_run_id"],
            argument_name=clarification_context["argument_name"],
            value=clarification_response
        )
    else:
        # Initial full plan run
        run = portia.run_plan(plan)
    
    if run.state == PlanRunState.NEED_CLARIFICATION:
        clarification = run.get_outstanding_clarifications()[0]
        return{
            "clarification_required": True,
            "message": clarification.user_guidance,
            "plan_run_id": run.id,
            "argument_name": clarification.argument_name,
        }
    
    # Handle failed plan
    if run.state != PlanRunState.COMPLETE:
        raise Exception(f"Plan run failed with state {run.state}")
    
        # If successful
    return {
        "clarification_required": False,
        "output": "Your plan has executed successfully. Please visit your resource at link",
    }

    


# plan = planner(topic, constraints, video_preference, rec_reading_preference)
# while not ready_to_proceed:
#   user_input = input("Are you happy with the plan? (y/n):\n")
#   if user_input == "y":
#       ready_to_proceed = True
#   else:
#       user_input = input("Any additional guidance for the planner?:\n")
#       constraints.append(user_input)
#       plan = planner(topic, constraints, video_preference, rec_reading_preference)
#       print("\nHere are the updated steps in the plan:")
#       [print(step.model_dump_json(indent=2)) for step in plan.steps]

# run_RAI(plan)