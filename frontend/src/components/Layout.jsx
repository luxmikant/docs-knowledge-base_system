import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Layout({ children }) {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const onLogout = () => {
    logout();
    navigate('/auth');
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>AI Task Hub</h1>
        <p className="sidebar-sub">Knowledge + Workflows</p>
        <nav>
          <NavLink to="/tasks">📋 Tasks</NavLink>
          <NavLink to="/documents">📄 Documents</NavLink>
          
          <div className="nav-section">
            <small className="nav-label">Search</small>
            <NavLink to="/search" className="nav-item">🔍 Basic Search</NavLink>
            <NavLink to="/search/advanced" className="nav-item">✨ Advanced Search</NavLink>
          </div>
          
          {isAdmin && (
            <div className="nav-section">
              <small className="nav-label">Admin</small>
              <NavLink to="/analytics" className="nav-item">📊 Analytics</NavLink>
              <NavLink to="/admin/index" className="nav-item">🛠️ Index Manager</NavLink>
            </div>
          )}
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
