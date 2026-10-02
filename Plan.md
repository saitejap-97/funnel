
# Problem Statement

HR automation tool that automates resume screening and ranking.

# Ideas

extraction of text from resumes and creating a profile for each.
ranking these profiles on various tags by AI
store the file on disc(update the file when new resumes are added)
rendering these profiles based on job description through LLM's

# Plan Prompt
Fullstack app for HR in our organization. Deployed internally.
Need to use some sort of LLM service, may be Openrouter (you decide).
Candidate resumes are put in some local folder for now.
Extract text, ask LLM for structured data along with some rubric (algorithm / idea to be decided; you can suggest).
We'll talk about the frontend later.
We'll want to create a plan and decide on the tech stack and design first before any implementation.
We want the codebase to be modular and reusable, say, like the following:
 - there can be a separate module that wraps around the python library for text extraction from pdf.
 - there can be another module that does the LLM Auth / Tool Calling.
 - there can be another module / struct / class whatever in Python that purely has data, like dumb data form without any methods.
 - there can be another module to mutate the data for the frontend or the API call handling (request handling)
 - there can be another module to purely serve and handle requests.
 - there can then be main module that composes all these to give the functionality.
You decide the low level design of all this.
We'll also do both front-end and back-end for this project.
For the back-end, the tech stack should be completely Python, and for the front-end, we'll take a good call on that later.
Like I said, frontend later.
Just enough of frontend thinking to think of API design.

Take as much time as you want.
Be very thorough about this.
This is a critical project.
Feel free to spawn background agents to review the code and design.
You can actually run some sort of autonomous loop of changes -> review -> changes etc.
Test cases are mandatory.
I can meanwhile create some test data. 
This folder is pretty much the whole project, both frontend and backend.
Create git repo and do some initial commit with a README, LICENCE etc. stuff.
Structure the project modularly.


