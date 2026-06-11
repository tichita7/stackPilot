import React, { useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { onAuthStateChanged } from "firebase/auth";
import { auth } from "./firebase";

import SignInPage from "./pages/SignInPage";
import SignUpPage from "./pages/SignUpPage";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import DebugAssistant from "./pages/DebugAssistant";
import CodeExplain from "./pages/CodeExplain";
import ReviewResume from "./pages/ReviewResume";
import RepositoryCopilot from "./pages/RepositoryCopilot";

const ProtectedRoute = ({ user, loaded, children }) => {
  const location = useLocation();
  if (!loaded)
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
        }}
      >
        <span>Loading...</span>
      </div>
    );
  if (!user)
    return <Navigate to="/sign-in" state={{ from: location }} replace />;
  return children;
};

const App = () => {
  const [user, setUser] = useState(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => {
      setUser(u);
      setLoaded(true);
    });
    return () => unsub();
  }, []);

  return (
    <Routes>
      {/* PUBLIC */}
      <Route path="/" element={<Home />} />
      <Route path="/sign-in" element={<SignInPage />} />
      <Route path="/sign-up" element={<SignUpPage />} />

      {/* PROTECTED */}
      <Route
        path="/ai"
        element={
          <ProtectedRoute user={user} loaded={loaded}>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai/repository-copilot"
        element={
          <ProtectedRoute user={user} loaded={loaded}>
            <RepositoryCopilot />
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai/code-explain"
        element={
          <ProtectedRoute user={user} loaded={loaded}>
            <CodeExplain />
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai/debug-assistant"
        element={
          <ProtectedRoute user={user} loaded={loaded}>
            <DebugAssistant />
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai/review-resume"
        element={
          <ProtectedRoute user={user} loaded={loaded}>
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
