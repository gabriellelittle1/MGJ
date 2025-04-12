from dotenv import load_dotenv
from portia.cli import CLIExecutionHooks
from portia import *
import requests
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Literal
import os
from notion_client import Client
from my_custom_tools.registry import custom_tool_registry

load_dotenv(override=True)
# Fetch the Notion API key and set up client
notion_api_key = os.getenv("NOTION_API_KEY")
notion_parent_id = os.getenv("NOTION_PARENT_ID")

# Initialize the Notion client
notion = Client(auth=notion_api_key)

def run_RAI(topic, video_preference = False, rec_reading_preference = False, number_of_videos = 2):


  my_config = Config.from_default()
  complete_tool_registry = PortiaToolRegistry(my_config) + custom_tool_registry

  portia = Portia(config = my_config,
                  tools = complete_tool_registry,
                  execution_hooks=CLIExecutionHooks(),)


  constraints = []

  # topic = "Using LLMs for Interior Design"
  # number_of_papers = 1
  # video_preference = False
  # number_of_videos = 2

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
                      - {video_preference * "Use the YouTubeTool to find videos on each topic."}
                      - {rec_reading_preference * "Use the RecReadTool to find resources on each topic."}
                      
                        Take into account these constraints: {constraints}
                      """

        )


  # Iterate on the plan with the user until they are happy with it
  with execution_context(end_user_id="learning_enthusiast",):
      plan = portia.plan(task())
      print("\nHere are the steps in the generated plan:")
      [print(step.model_dump_json(indent=2)) for step in plan.steps]
      ready_to_proceed = False
      while not ready_to_proceed:
          user_input = input("Are you happy with the plan? (y/n):\n")
          if user_input == "y":
              ready_to_proceed = True
          else:
              user_input = input("Any additional guidance for the planner?:\n")
              constraints.append(user_input)
              plan = portia.plan(task())
              print("\nHere are the updated steps in the plan:")
              [print(step.model_dump_json(indent=2)) for step in plan.steps]

      # Execute the plan
      print("\nThe plan will now be executed. Please wait...")
      run = portia.run_plan(plan)
      
      if run.state != PlanRunState.COMPLETE:
          raise Exception(
              f"Plan run failed with state {run.state}. Check logs for details."
          )
  return 