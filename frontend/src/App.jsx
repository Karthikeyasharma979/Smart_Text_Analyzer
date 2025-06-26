import React from "react";
import { BrowserRouter } from "react-router-dom";
import AppRoutes from "./routes/AppRoutes";
import Navbar from "./components/Common/Navbar"; // optional

const App = () => {
  return (
    <BrowserRouter>
      <Navbar /> {/* You can include your Navbar globally here */}
      <AppRoutes />
    </BrowserRouter>
  );
};

export default App;
