# ExplAIn

## Project Idea and Overview

ExplAIn is an intelligent learning assistant built using the Portia toolkit that transforms complex academic papers into structured, personalized learning experiences.

Have you ever started reading a paper, only to find yourself falling down a rabbit hole of Wikipedia pages, YouTube videos, and textbook chapters—just to grasp the basics? ExplAIn streamlines that entire process.

You can provide it with a research paper—or simply a topic, and it will find a relevant one for you. From there, ExplAIn identifies the key concepts necessary for deep comprehension and asks you which areas you'd like to explore. It then generates targeted lessons for each concept, including curated videos, textbook references, Wikipedia links, and interactive quizzes.

Once you've built a solid foundation, ExplAIn returns to the original paper and explains it in a clear, digestible format—grounded in your personalized knowledge path. The result is a seamless journey from confusion to clarity, so you can focus on learning instead of searching.

## How we used Portia AI

### Custom Tools
* ArXivTool: _Finds papers from arXiv using the arXiv API, given a topic._
* DownloadTool: _Download papers given urls._
* PDFReaderTool: _Reads file and returns it without citations._
* TopicSelectorTool: _Allows the user to choose which topics from topics found._
* NotionTool: _Uses the Notion API to create and populate Notion pages with lessons. Includes an information verification step._
* RecReadTool: _Finds wiki link and textbook urls related to the topic and adds to the Notion pages._
* YouTubeTool: _Finds YouTube urls related to the topic and adds to the Notion pages._
* QuizTool: _Creates custom quiz for each topic based on the lesson._

## Detailed Workflow

Tools and Workflow so far: 

  1. Input topic and number of papers.
  2. ArXivTool finds papers.
  3. DownloadPaperTool downloads papers.
  4. PDFReaderTool reads the papers, and finds subtopics.
  5. TopicPickerTool allows user to choose which topics to have lessons on.
  6. NotionTool creates folder called "Learning Plans" with a page for each topic and populating it (while using a secondary LLM to check if output is accurate).
  7. YouTubeTool optionally adds links to 3 videos on the subtopics (on each page).
  8. RecReadTool optionally adds resources on the subtopics (recommended text books, wikipedia pages)
  9. QuizTool creates subpages for each topic page consisting of a curated quiz + answers

## API Instructions 
_.env.example in repo_

### Portia API
1. Go to https://app.portialabs.ai/dashboard
2. Click Manage API Keys -> Create New API Key
3. Set **PORTIA_API_KEY** in the .env

### OpenAI API 
1. Go to https://platform.openai.com/logs
2. Open Dashboard -> API Keys -> Create new secret key
3. Set **OPENAI_API_KEY** in .env

### Notion API 
n.b. _If this is your first time using Notion you must create an account and setup a workspace before creating your API key_
1. Create Integration with Notion: https://www.notion.so/profile/integrations
    - Choose your Workspace (making sure you are the owner) and add a name.
2. Get API key from the configuration page (Internal Integration Secret) and set it to the env file (**NOTION_API_KEY**). 
3. Create a new page in your workspace.
    - Click on the three dots on the top right of the page, and scroll to "Connections".
    - Hover over "Connections", then type the name of the Integration into the searchbar, and give permission.
4. Get the ID of the page: 
    - If the URL is https://www.notion.so/1d26ccbbecba807587c1d438baa16104
    - The ID is 1d26ccbbecba807587c1d438baa16104
    - Set the ID in the .env (**NOTION_PARENT_ID**)  

### Google API
1. Go to https://cloud.google.com/apis
2. In a project, enable YouTube Data API v3
3. In the same project, search up credentials and create an API key, then set **GOOGLE_API_KEY** in .env

### Gemini API
1. Go to https://aistudio.google.com/app/apikey
2. Create API key and set **GEMINI_API_KEY** in .env

