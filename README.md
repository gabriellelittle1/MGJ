# MGJ
Github for Encode AI Hackathon Project


- Run "conda env create -f environment.yaml" to create the environment from this repository
- Then activate with "conda activate RA"


Project Goal: 

  Our goal is to create an agentic workflow using Portia that acts as a Research Assistant / Tutor. The user will input a topic and the first agent will find the most relevant / recent papers in that area. It then downloads the papers, and finds subtopics in the papers that it is necessary for the user to understand in order to understand the paper in depth. 

  It then asks the user, do you want a lesson on subtopic "xyz"? And the user decides whether or not to take a lesson, which we want to then ask - what is your preferred method of learning - video (youtube) , podcast (check for podcasts? then generate?), reading (find resource or generate resource) etc.

  Then, ask if they want to be quizzed on the topic (whether or not they had a lesson). If they didn't have a lesson, and they did not do well on the quiz, then ask if they want a lesson. 

  Then once all lessons are finished, summarise the current research landscape (including what the papers are about, where the gaps are, open questions, and maybe pose some thoughtful questions). 
