import React, { useState, useEffect } from "react";
import "./Editor.css";
import { Link } from "react-router-dom";

function GrammarSidebar({ inputText }) {
  const [correctness, setCorrectness] = useState(false);
  const [clarity, setClarity] = useState(false);
  const [engagement, setEngagement] = useState(false);
  const [delivery, setDelivery] = useState(false);
  const [score, setScore] = useState(85);

  const [improveText, setImproveText] = useState([
    { word: "We're", highlight: false },
    { word: "We", highlight: true, color: "bg-purple-100 text-purple-700" },
    { word: "sorry", highlight: false },
    { word: "apologize", highlight: true, color: "bg-red-100 text-red-700" },
    { word: ",", highlight: false },
    { word: "but", highlight: false },
    { word: "an", highlight: false },
    { word: "unexpected", highlight: false },
    { word: "error", highlight: false },
    { word: "has", highlight: true, color: "bg-green-100 text-green-700" },
    { word: "occurred", highlight: false },
    { word: "while", highlight: false },
    { word: "processing", highlight: false },
    { word: "your", highlight: false },
    { word: "request.", highlight: false },
  ]);

  useEffect(() => {
    // Debounce update on text change
    const handler = setTimeout(() => {
      setCorrectness(true);
      setClarity(true);
      setEngagement(true);
      setDelivery(true);
      setScore(85); // static, can be dynamic later
    }, 1000);
    console.log("Every Time check")
    return () => clearTimeout(handler);
  }, [inputText]);

  const useSuggestedVersion = () => {
    const result = improveText
      .map((item) => (item.highlight ? item.word : ""))
      .filter(Boolean)
      .join(" ");
    alert("Suggested version used:\n" + result);
  };

  const dismissSuggestions = () => {
    setImproveText((prev) =>
      prev.map((item) => ({ ...item, highlight: false }))
    );
  };

  const applySuggestions = () => {
    const updatedText = improveText.map((item) => item.word).join(" ");
    alert("Final Text with Suggestions:\n" + updatedText);
    dismissSuggestions();
  };

  return (
    <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
      {/* Top Navigation */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex justify-around">
          <Link
            to="/dashboard/editor"
            className="flex flex-col items-center text-purple-600 border-b-2 border-purple-600 py-2 px-3"
          >
            <span className="material-icons text-xl">edit_note</span>
            <span className="text-xs mt-1">Review suggestions</span>
          </Link>
          <Link
            to="/dashboard/editor/generativeAI"
            className="flex flex-col items-center text-gray-500 hover:text-gray-700 py-2 px-3"
          >
            <span className="material-icons text-xl">auto_awesome</span>
            <span className="text-xs mt-1">Write with generative AI</span>
          </Link>
          <Link
            to="/dashboard/editor/plagiarism"
            className="flex flex-col items-center text-gray-500 hover:text-gray-700 py-2 px-3"
          >
            <span className="material-icons text-xl">plagiarism</span>
            <span className="text-xs mt-1">Check for AI text & plagiarism</span>
          </Link>
        </div>
      </div>

      <div className="p-4 flex-grow overflow-y-auto">
        {/* Feedback categories */}
        <div className="grid grid-cols-2 gap-2 mb-6 text-xs">
          {[
            { label: "Correctness", value: correctness },
            { label: "Clarity", value: clarity },
            { label: "Engagement", value: engagement },
            { label: "Delivery", value: delivery },
          ].map(({ label, value }) => (
            <div key={label} className="flex items-center cursor-pointer">
              <span
                className={`material-icons text-base mr-1 ${
                  value ? "text-green-500" : "text-red-500"
                }`}
              >
                {value ? "check_circle" : "cancel"}
              </span>
              {label}
            </div>
          ))}
        </div>

        {/* Readability Score */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center">
              <span className="material-icons text-blue-500 text-base mr-1">
                visibility
              </span>
              <h3 className="text-xs font-medium text-gray-800">
                Readability Analysis
              </h3>
            </div>
            <button className="text-gray-400 hover:text-gray-600">
              <span className="material-icons text-sm">expand_more</span>
            </button>
          </div>
          <p className="text-xs text-gray-600 mb-2">
            Your text is{" "}
            {score < 80
              ? "hard to read. Try to improve your spelling and clarity."
              : "easy to read. Aim for a score of 80+ for most audiences."}
          </p>
          <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
            <div
              className="bg-green-500 h-1.5 rounded-full"
              style={{ width: `${score}%` }}
            ></div>
          </div>
          <span
            className={`text-xs font-medium ${
              score < 80 ? "text-red-600" : "text-green-600"
            }`}
          >
            {score}/100
          </span>
        </div>

        {/* Improvement Suggestions */}
        <div className="border border-gray-200 rounded-lg p-3">
          <div className="flex items-center text-xs text-blue-600 mb-2">
            <span className="material-icons text-base mr-1">lightbulb</span>
            <span>Improve your text</span>
            <button className="text-gray-400 hover:text-gray-600 ml-auto">
              <span className="material-icons text-base">more_vert</span>
            </button>
          </div>

          <p className="text-sm text-gray-700 mb-3 flex flex-wrap gap-1">
            {improveText.map((item, index) => (
              <span
                key={index}
                className={`px-1 rounded ${
                  item.highlight ? item.color : ""
                }`}
              >
                {item.word}
              </span>
            ))}
          </p>

          <div className="flex items-center space-x-2">
            <button
              onClick={useSuggestedVersion}
              className="bg-teal-500 text-white text-xs px-3 py-1.5 rounded-md hover:bg-teal-600"
            >
              Use this version
            </button>
            <button
              onClick={dismissSuggestions}
              className="text-gray-500 text-xs hover:text-gray-700"
            >
              Dismiss
            </button>
            <button className="text-gray-400 hover:text-gray-600 ml-auto">
              <span className="material-icons text-base">more_horiz</span>
            </button>
          </div>
        </div>
      </div>

      {/* Apply All Suggestions */}
      <div className="p-4 border-t border-gray-200">
        <button
          onClick={applySuggestions}
          className="bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium py-2 px-4 rounded-md w-full flex items-center justify-center"
        >
          <span className="material-icons mr-2 text-base">done</span>
          Apply All Suggestions
        </button>
      </div>
    </div>
  );
}

export default GrammarSidebar;
