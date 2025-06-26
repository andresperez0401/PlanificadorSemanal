import { Link } from 'react-router-dom';
import '../styles/navbar.css';

export default function Navbar({ user, onLogout }) {
  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <span className="calendar-icon">📅</span>
        <h1 className="app-title">Planificación Semanal</h1>
      </div>
      <div className="navbar-links">
        {user ? (
          <>
            <div className="user-avatar">
              {getInitials(user.name)}
            </div>
            <button onClick={onLogout} className="nav-link logout-btn">Cerrar sesión</button>
          </>
        ) : (
          <Link to="/login" className="nav-link login-btn">Iniciar sesión</Link>
        )}
      </div>
    </nav>
  );
}