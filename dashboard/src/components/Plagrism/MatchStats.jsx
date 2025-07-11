
function MatchStats({percentage,words,totalwords1,totalwords2}) {
  return (
    <div className="p-4 bg-gray-50 rounded-b-lg border-t border-gray-200 grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="text-center">
        <p className="text-sm text-gray-700">{totalwords1} words</p>
        <p className="text-2xl font-bold text-green-600">{percentage}</p>
        <p className="text-xs text-gray-500">Matched</p>
      </div>
      <div className="text-center md:border-l md:border-r border-gray-200 px-4"></div>
      <div className="text-center">
        <p className="text-sm text-gray-700">{totalwords2} words</p>
        <p className="text-2xl font-bold text-green-600">{words}</p>
        <p className="text-xs text-gray-500">Matched</p>
      </div>
    </div>
  );
}

export default MatchStats;
