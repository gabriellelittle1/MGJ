# MGJ
Github for Encode AI Hackathon Project


Plan for Saturday Morning;
- Josh Learning Pages Content + Some kind of verification of information.
- Malini Front End. 


- Run "conda env create -f environment.yaml" to create the environment from this repository
- Then activate with "conda activate RA"


Project Goal: 

  Our goal is to create an agentic workflow using Portia that acts as a Research Assistant / Tutor. The user will input a topic and the first agent will find the most relevant / recent papers in that area. It then downloads the papers, and finds subtopics in the papers that it is necessary for the user to understand in order to understand the paper in depth. 

  It then asks the user, do you want a lesson on subtopic "xyz"? And the user decides whether or not to take a lesson, which we want to then ask - what is your preferred method of learning - video (youtube) , podcast (check for podcasts? then generate?), reading (find resource or generate resource) etc.

  Then, ask if they want to be quizzed on the topic (whether or not they had a lesson). If they didn't have a lesson, and they did not do well on the quiz, then ask if they want a lesson. 

  Then once all lessons are finished, summarise the current research landscape (including what the papers are about, where the gaps are, open questions, and maybe pose some thoughtful questions). 


Tools and Workflow so far: 

  1. Input topic and number of papers.
  2. ArXivTool finds papers.
  3. DownloadPaperTool downloads papers.
  4. PDFReaderTool reads the papers, and finds subtopics.
  5. TopicPickerTool allows user to choose which topics to have lessons on.
  6. NotionTool creates folder called "Learning Plans" with a page for each topic and populating it.
  7. YouTubeTool optionally adds links to 3 videos on the subtopics (on each page). 

Next Steps: 
  1. Page for the paper, with the paper broken down and explained using the concepts already explained.
  2. Quiz for each topic with some form of Gameification. 
  3. Front end
  4. Much Cooler lessons with multimodal learning - recommended reading, podcasts, mini project suggestions, diagrams
  5. Do we want optional image inputs - potentially for 

Instructions for Google API: 
- Remember that we require permission to use the Youtube API 
Instructions for setting up parent page for Notion API: 

1. Create Integration with Notion: https://www.notion.so/profile/integrations
   - Choose your Workspace (making sure you are the owner) and add a name.
2. Get API key from the configuration page (Internal Integration Secret) and it it to the env file. 
3. Create a new page in your workspace.
  - Click on the three dots on the top right of the page, and scroll to "Connections".
  - Hover over "Connections", then type the name of the Integration into the searchbar, and give permission.
4. Get the ID of the page: 
  - If the URL is https://www.notion.so/1d26ccbbecba807587c1d438baa16104
  - The ID is 1d26ccbbecba807587c1d438baa16104
