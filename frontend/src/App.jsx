import React from 'react';
import { useState, useEffect, useContext } from 'react'
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import './App.css'
import { ToastContainer } from "react-toastify";
import injectContext from "./store/appContext.jsx";
import Navbar from './components/Navbar.jsx';
import Home from './pages/Home.jsx';
import Signup from './pages/Signup.jsx';
import Login from './pages/Login.jsx';
import { Context } from './store/appContext.jsx';

const AppContent = () => {
  const location = useLocation();
  const { actions } = useContext(Context);

  useEffect(() => {
    // Al montar el componente principal
    const { success } = actions.restoreSession();
    // 2) Si hay token, bajar tareas
    if (success) actions.getTasks();
  }, []);

  //Esto sirve para ocultar ciertas rutas y que no se muestre el footer por ejemplo
  const hideNavbar = ['/login', '/signup'].includes(location.pathname);

   return (
    <div className="app-container">
      {!hideNavbar && <Navbar />}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/home" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
        </Routes>
      </main>
      
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        pauseOnHover
        draggable
        theme="colored"
      />
    </div>
  );
};

// 2️⃣ Ahora envolvemos ese component con nuestro HOC de Flux/Context:
const AppContentWithFlux = injectContext(AppContent);

function App() {
  return (
    <div className="App">
        <Router>
          <AppContentWithFlux />
        </Router>
    </div>
  );
}

export default App;