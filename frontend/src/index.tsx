import App from "./App";
import React from "react";
import ReactDOM from "react-dom/client";

// Importing the Bootstrap CSS
import "bootstrap/dist/css/bootstrap.min.css";

// Render the App component into the #root div
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
