import React from "react";
import { useUser, AuthenticateWithRedirectCallback } from "@clerk/clerk-react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import SignInPage from "./pages/SignInPage";
import SignUpPage from "./pages/SignUpPage";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import DebugAssistant from "./pages/DebugAssistant";
import CodeExplain from "./pages/CodeExplain";
import ReviewResume from "./pages/ReviewResume";
import RepositoryCopilot from "./pages/RepositoryCopilot";

const ProtectedRoute = ({ children }) => {
  const { isSignedIn, isLoaded } = useUser();
  const location = useLocation();
  if (!isLoaded) return null;
  if (!isSignedIn) {
    return <Navigate to="/sign-in" state={{ from: location }} replace />;
  }
  return children;
};

const App = () => {
  return (
    <Routes>
      {/* PUBLIC */}
      <Route path="/" element={<Home />} />
      <Route path="/sign-in" element={<SignInPage />} />
      <Route path="/sign-up" element={<SignUpPage />} />
      <Route
        path="/sso-callback"
        element={
          <AuthenticateWithRedirectCallback
            signInForceRedirectUrl="/ai"
            signUpForceRedirectUrl="/ai"
          />
        }
      />

      {/* PROTECTED */}
      <Route
        path="/ai"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai/repository-copilot"
        element={
          <ProtectedRoute>
            <RepositoryCopilot />
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai/code-explain"
        element={
          <ProtectedRoute>
            <CodeExplain />
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai/debug-assistant"
        element={
          <ProtectedRoute>
            <DebugAssistant />
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai/review-resume"
        element={
          <ProtectedRoute>
            <ReviewResume />
          </ProtectedRoute>
        }
      />

      {/* FALLBACK */}
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
};

export default App;
