import { NavLink } from 'react-router-dom';
import './Layout.css';

const navItems = [
  { path: '/', label: 'Home', icon: '🏠' },
  { path: '/chatbot', label: 'Wellness Chat', icon: '💬' },
  { path: '/yoga', label: 'Yoga', icon: '🧘' },
  { path: '/diet', label: 'Diet Plan', icon: '🥗' },
  { path: '/movies', label: 'Movies', icon: '🎬' },
];

export default function Layout({ children }) {
  return (
    <div className="layout">
      <header className="header">
        <div className="header-brand">
          <span className="logo">🌿</span>
          <h1>WellSync</h1>
        </div>
        <nav className="nav">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              end={item.path === '/'}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="main">{children}</main>
      <footer className="footer">
        <p>WellSync &copy; 2026 — Your holistic wellness companion</p>
      </footer>
    </div>
  );
}
