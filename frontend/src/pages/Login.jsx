import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import '../styles/auth.css';
import img from "../img/organiza-app.png";
import { useContext } from 'react';
import { Context } from '../store/appContext';
import { useAlert}from '../hooks/useAlert.js';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const { store, actions } = useContext(Context);
  const { success, error } = useAlert();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const loginResponse = await actions.login(email, password);

    if (loginResponse.success) {
      success('Inicio de sesión exitoso');
      navigate('/home');
    } else {
      error('Error en inicio de sesión');
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <div className="logo">
                <img src={img} alt="Logo" className="logo" />
            </div>
            <h2 className="auth-title">Iniciar Sesión</h2>
          </div>
          
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="input-group">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Correo electrónico"
                required
                className="auth-input"
              />
            </div>
            
            <div className="input-group">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Contraseña"
                required
                className="auth-input"
              />
            </div>
            
            <button type="submit" className="auth-btn">Ingresar</button>
            
            <div className="auth-footer">
              <p>¿No tienes cuenta? <Link to="/signup" className="auth-link">Regístrate</Link></p>
              <p><Link to="/home" className="auth-link">Regresar</Link></p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}