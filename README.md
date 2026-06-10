# 🚀 StackPilot

StackPilot is an agentic AI-powered developer platform that helps developers debug code, understand repositories, explain code snippets, and optimize resumes using intelligent AI workflows.

---

## 🌟 Features

### 🐞 Debug Assistant

Analyze code and receive:

- Root cause analysis
- Error explanations
- Suggested fixes
- Corrected code snippets
- Debugging best practices

---

### 📂 Repository Copilot

Connect a GitHub repository and ask questions about your codebase.

Capabilities:

- Repository architecture overview
- Folder structure analysis
- Route mapping
- Component relationships
- Dependency understanding
- Future plan recommendations

---

### 💡 Code Explain

Paste code snippets and get:

- Step-by-step explanations
- Logic breakdown
- Time complexity analysis
- Space complexity analysis
- Optimization suggestions

---

### 📄 Resume Reviewer

Upload your resume and receive:

- ATS compatibility feedback
- Resume scoring
- Skill-gap analysis
- Content improvement recommendations

---

## 🛠 Tech Stack

### Frontend

- React 19
- Vite
- Tailwind CSS 4
- React Router
- Clerk Authentication
- Lucide Icons

### Backend

- Python
- Groq API
- Llama 3.3 70B

### AI

- Meta Llama 3.3 70B
- Prompt Engineering
- Agentic AI Workflows

---

## 📁 Project Structure

stackPilot/

├── client/

│ ├── src/

│ ├── public/

│ ├── package.json

│ └── ...

├── server/

│ ├── main.py

│ ├── routes/

│ └── ...

└── README.md

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/tichita7/stackPilot.git
cd stackpilot
```

### Install Frontend Dependencies

```bash
cd client
npm install
```

### Create Environment Variables

Create a `.env` file.

Frontend:

```env
VITE_CLERK_PUBLISHABLE_KEY=your_key
```

Backend:

```env
GROQ_API_KEY=your_groq_api_key
```

---

## 🚀 Running the Project

### Start Frontend

```bash
cd client
npm run dev
```

Frontend will run on:

```text
http://localhost:5173
```

### Start Backend

```bash
cd server

uvicorn main:app --reload
```

---

## 🤖 AI Model

StackPilot uses:

- Llama 3.3 70B
- Groq Inference Engine

for:

- Repository Analysis
- Debugging Assistance
- Code Explanation
- Resume Review

---

## 🎯 Why StackPilot?

Developers frequently switch between multiple tools for:

- Debugging
- Repository Analysis
- Code Understanding
- Resume Optimization

StackPilot brings these workflows together into a single AI-powered platform.

---

<!-- ## 🔮 Future Roadmap

- Repository visualizer
- Pull request review assistant
- AI-generated documentation
- Architecture diagrams
- Test case generation
- Team collaboration features
- Multi-agent workflows

--- -->

## 👩‍💻 Author

Tichita Dhiman

---
