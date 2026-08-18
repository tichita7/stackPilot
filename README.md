# 🚀 StackPilot

StackPilot is an AI-powered developer platform that brings multiple developer workflows into one place.

It helps developers debug code, understand and analyze repositories, explain code snippets, and improve resumes through specialized AI-powered workflows.

---

## 🌟 Features

### 🐞 Debug Assistant

Analyze code and error logs to identify problems and receive actionable debugging assistance.

Capabilities include:

- Root cause analysis
- Error explanation
- Suggested fixes
- Corrected code snippets
- Debugging recommendations
- Potential runtime issues
- Logical issue detection

---

### 📂 Repository Copilot

Connect a GitHub repository and analyze the codebase using a natural-language goal.

Repository Copilot can help developers understand unfamiliar codebases by providing:

- Project architecture overview
- Technology stack identification
- Important file identification
- Folder and file structure analysis
- Route mapping
- Component relationships
- Authentication flow analysis
- Database/schema insights
- Dependency understanding
- Repository-specific developer insights
- Relevant files to inspect
- Step-by-step investigation plans
- Step-by-step implementation plans

The analysis adapts to the user's goal.

For example, users can ask:

> Find the Code Explainer implementation and explain how a user's code travels from the React frontend to the FastAPI backend and finally to the AI service.

Repository Copilot can then identify the relevant files and map the data flow across the application.

---

### 💡 Code Explain

Paste a code snippet and receive an AI-powered explanation of the code.

Capabilities include:

- Step-by-step explanation
- Logic breakdown
- Time complexity analysis
- Space complexity analysis
- Optimization suggestions
- Syntax and compilation issue detection
- Potential runtime issue detection
- Logical/behavioral issue detection
- Missing import/include detection
- Undefined variable or function detection
- Suggestions for correcting problematic code

Code Explain first analyzes whether the provided code appears valid and complete before explaining its behavior.

If the code contains an obvious issue, StackPilot identifies the problem instead of pretending that the code is valid.

> **Note:** Code analysis is AI-based. StackPilot does not claim to compile or execute code unless an actual execution environment is used.

---

### 📄 Resume Reviewer

Upload a resume and receive AI-powered feedback designed to improve its effectiveness for software engineering applications.

Capabilities include:

- ATS compatibility feedback
- Resume scoring
- Skill-gap analysis
- Content improvement recommendations
- Technical keyword suggestions
- Role-specific optimization
- Bullet-point improvement suggestions

---

## 🛠 Tech Stack

### Frontend

- React 19
- Vite
- Tailwind CSS
- React Router
- Firebase Authentication
- Lucide Icons

### Backend

- Python
- FastAPI
- Groq API

### AI

- GPT OSS 20B through Groq
- Prompt Engineering
- Structured AI responses
- Agentic AI workflows
- Repository-aware analysis

### Deployment & Infrastructure

- Vercel — Frontend deployment
- Render — Backend deployment
- GitHub — Source control and repository integration
- Firebase — Authentication

---

## 🧠 AI Architecture

StackPilot uses specialized AI workflows for different developer tasks instead of treating every request as a generic chatbot interaction.

```text
                         ┌───────────────────┐
                         │     StackPilot    │
                         └─────────┬─────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
       Debug Assistant     Repository Copilot     Code Explain
              │                    │                    │
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   │
                                   ▼
                            AI Processing
                                   │
                                   ▼
                             Groq / GPT OSS
                                   │
                                   ▼
                          Structured Response

                                   │
                                   ▼
                           Resume Reviewer
```
