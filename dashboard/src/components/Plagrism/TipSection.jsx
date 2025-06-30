import "./Plagiarism.css"
function TipSection() {
  return (
    <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md flex items-center justify-between">
      <div className="flex items-center">
        <span className="material-icons text-blue-600 mr-2">lightbulb</span>
        <p className="text-sm text-gray-700">
          Looking for an accurate plagiarism check for your content?
        </p>
      </div>
      <button className="btn-primary">
        Try Plagiarism Checker Now
        <span className="material-icons text-sm ml-1 align-middle">arrow_forward</span>
      </button>
    </div>
  );
}

export default TipSection;
