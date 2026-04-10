import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Layout({ children }) {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const onLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>AI Task Hub</h1>
        <p className="sidebar-sub">Knowledge + Workflows</p>
        <nav>
          <NavLink to="/tasks">Tasks</NavLink>
          <NavLink to="/documents">Documents</NavLink>
          <NavLink to="/search">Search</NavLink>
          {isAdmin && <NavLink to="/analytics">Analytics</NavLink>}
        </nav>
      </aside>

      <main className="content">
        <header className="topbar">
          <div>
            <strong>{user?.username}</strong>
            <span className="pill">{user?.role}</span>
          </div>
          <button onClick={onLogout}>Logout</button>
        </header>
        {children}
      </main>
    </div>
  );
}
