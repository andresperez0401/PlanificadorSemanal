import { Link } from 'react-router-dom';
import '../styles/navbar.css';
import img from "../img/organiza-app.png";
import { useContext, useEffect } from 'react';
import { Context } from '../store/appContext';

export default function Navbar() {


  const { store, actions } = useContext(Context);

  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
  };

  const onLogout = () => {
    actions.logout();
  }

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <img src={img} alt="Logo" className="logo" />
      </div>
      <div className="navbar-links">
        {store.token ? (
          <>
            <div className="user-avatar">
              {getInitials(store.usuario.nombre)}
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