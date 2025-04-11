from dotenv import load_dotenv
from portia import Config, Portia, PortiaToolRegistry
from portia.cli import CLIExecutionHooks

load_dotenv(override=True)

outline = """
This is a research assistant that will help you learn about a specific topic, by breaking
the topic down into smaller subtopics, and teaching you about each subtopic in detail. 
It will then provide you with a summary of the topic, and a list of resources for further reading.

"""
print(outline)

subject_topic = input(
    "Please enter the research topic you would like to learn about:\n"
)



