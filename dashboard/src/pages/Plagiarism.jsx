import React, { useState } from 'react';
import TextInputPanel from '../components/Plagrism/TextInputPanel';
import CheckboxGroup from '../components/Plagrism/CheckboxGroup';
import ComparisonReport from '../components/Plagrism/ComparisonReport';

function Plagiarism() {
  const placeholder = `Upload an image. It returns: Tags, Descriptions...`;
  const fakeDocText = `Yes :) Here are some free and reliable websites...`;
  const [textArea1,setTextArea1]=useState("")
  const [textArea2,setTextArea2]=useState("")
  const [common,setCommon]=useState(false)
  const [similar,setSimilar]=useState(false)

  const onCompare=()=>{
      if(textArea1.length<=1 || textArea2<=2){
        alert("Please enter the text more than two words ")
      }
      else{
        const res={
          "textArea1":textArea1,
          "textArea2":textArea2,
          "common":common,
          "similar":similar
        }
        console.log(res)
      }
  } 

  return (
    <div className="bg-gray-100 min-h-screen flex flex-col items-center py-6">
      <div className="w-full max-w-6xl bg-white rounded-lg shadow-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <TextInputPanel  count={textArea1.length} setTextArea={setTextArea1} />
          <TextInputPanel count={textArea2.length} setTextArea={setTextArea2} />
        </div>
        <div className="mt-6 flex flex-col items-center">
          <CheckboxGroup setCommon={setCommon} setSimilar={setSimilar}/>
          <button className="btn-primary w-full max-w-xs mt-2" onClick={onCompare}>Compare Now</button>
          <p className="text-xs text-gray-500 mt-2">Note: We don't save any data on our servers.</p>
        </div>
        {/* <TipSection /> */}
        <ComparisonReport firstDoc={fakeDocText} secondDoc={fakeDocText} />
      </div>
    </div>
  );
}

export default Plagiarism;
