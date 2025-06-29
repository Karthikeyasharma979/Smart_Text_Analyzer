import React from "react";
import { Routes, Route } from "react-router-dom";

// Main Pages
import Editor from "../pages/Editor";
import Upload from "../pages/Upload";
import Dashboard from "../pages/Dashboard";
import History from "../pages/History";
import Settings from "../pages/Settings";
import Page404 from "../pages/Page404";
// Auth Pages

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/dashboard/editor/*" element={<Editor />} />
      <Route path="/dashboard/upload/*" element={<Upload />} />
      <Route path="/dashboard/generativeAI" element={<History />} />
      <Route path="/dashboard/settings" element={<Settings />} />
      <Route path="*" element={<Page404/>} />
    </Routes>
  );
};

export default AppRoutes;
