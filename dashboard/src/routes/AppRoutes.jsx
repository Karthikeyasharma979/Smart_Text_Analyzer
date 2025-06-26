import React from "react";
import { Routes, Route } from "react-router-dom";

// Main Pages
import Home from "../pages/Home";
import Editor from "../pages/Editor";
import Upload from "../pages/Upload";
import Dashboard from "../pages/Dashboard";
import History from "../pages/History";
import Settings from "../pages/Settings";

// Auth Pages
import Login from "../pages/Login";
import Signup from "../pages/SignUp";

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/dashboard/editor" element={<Editor />} />
      <Route path="/dashboard/upload" element={<Upload />} />
      <Route path="/dashboard/history" element={<History />} />
      <Route path="/dashboard/settings" element={<Settings />} />

      <Route path="*" element={<div className="p-6 text-center text-red-500 text-lg">404 - Page Not Found</div>} />
    </Routes>
  );
};

export default AppRoutes;
