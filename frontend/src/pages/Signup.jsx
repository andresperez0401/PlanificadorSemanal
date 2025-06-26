import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import PhoneInput from 'react-phone-number-input';
import 'react-phone-number-input/style.css';
import '../styles/auth.css';

export default function Signup() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!name || !email || !phone || !password || !confirmPassword) {
      toast.error('Por favor complete todos los campos');
      return;
    }
    if (password !== confirmPassword) {
      toast.error('Las contraseñas no coinciden');
      return;
    }
    if (!phone) {
      toast.error('Por favor ingrese un número de teléfono válido');
      return;
    }
    
    // Simular registro exitoso
    toast.success('Registro exitoso! Bienvenido');
    navigate('/home');
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <div className="logo">📅</div>
            <h1 className="app-title">Planificación Semanal</h1>
            <h2 className="auth-title">Crear Cuenta</h2>
          </div>
          
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="input-group">
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Nombre completo"
                required
                className="auth-input"
              />
            </div>
            
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
              <PhoneInput
                international
                defaultCountry="ES"
                value={phone}
                onChange={setPhone}
                placeholder="Teléfono"
                className="phone-input"
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
            
            <div className="input-group">
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirmar contraseña"
                required
                className="auth-input"
              />
            </div>
            
            <button type="submit" className="auth-btn">Registrarse</button>
            
            <div className="auth-footer">
              <p>¿Ya tienes cuenta? <Link to="/login" className="auth-link">Inicia sesión</Link></p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}