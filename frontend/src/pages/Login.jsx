import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import '../styles/auth.css';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Por favor complete todos los campos');
      return;
    }
    
    // Simular inicio de sesión exitoso
    toast.success('Inicio de sesión exitoso');
    navigate('/home');
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <div className="logo">📅</div>
            <h1 className="app-title">Planificación Semanal</h1>
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
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}