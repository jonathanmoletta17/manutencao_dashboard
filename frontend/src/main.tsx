import React from "react";
import ReactDOM from "react-dom/client";
import MaintenanceDashboard from "./MaintenanceDashboard";
import "./dtic-index.css";
import "./overflow-hotfix.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <MaintenanceDashboard />
  </React.StrictMode>
);