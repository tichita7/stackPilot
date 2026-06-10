import { FolderSearch, Bug, Code2, FileSearch } from "lucide-react";

export const AiToolsData = [
  {
    title: "Repo CoPilot",
    description:
      "Ask questions about your codebase and get contextual answers powered by repository-aware AI.",
    Icon: FolderSearch,
    bg: { from: "#5C6AF1", to: "#427DF5" },
    path: "/ai/repository-copilot",
  },
  {
    title: "Debug Assistant",
    description:
      "Analyze errors, identify root causes, and receive AI-powered debugging suggestions.",
    Icon: Bug,
    bg: { from: "#c33620", to: "#b94c11" },
    path: "/ai/debug-assistant",
  },
  {
    title: "Code Explain",
    description:
      "Paste code snippets and receive clear explanations of logic, structure, and behavior.",
    Icon: Code2,
    bg: { from: "#B153EA", to: "#E549A3" },
    path: "/ai/code-explain",
  },
  {
    title: "Review Resume",
    description:
      "Upload your resume and receive actionable ATS and content improvement suggestions.",
    Icon: FileSearch,
    bg: { from: "#eab308", to: "#eacc37" },
    path: "/ai/review-resume",
  },
];
