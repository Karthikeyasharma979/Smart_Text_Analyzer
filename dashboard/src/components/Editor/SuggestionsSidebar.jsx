import "./Editor.css";
import React from "react";
import { Route, Routes } from "react-router-dom";
import GrammerSidebar from "./GrammerSidebar";
import WriteAISidebar from "./WriteAISidebar";
import PlagirarismSidebar from "./PlagirarismSidebar";

function SuggestionsSidebar({inputText}) {
  
  return (
    <Routes>
      <Route index element={<GrammerSidebar  inputText={inputText}/>} />
      <Route path="generativeAI" element={<WriteAISidebar  inputText={inputText}/>} />
      <Route path="plagiarism" element={<PlagirarismSidebar   inputText={inputText}/>} />
    </Routes>
  );
}

export default SuggestionsSidebar;