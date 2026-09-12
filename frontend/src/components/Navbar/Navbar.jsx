import { Link } from 'react-router-dom';
import './Navbar.css';

function Navbar() {
  return (
    <nav className="navbar">
      <Link to="/" className="navbar-title">MediScan</Link>
      <div className="navbar-links">
        <Link to="/search" className="navbar-link">Search</Link>
        <Link to="/upload" className="navbar-link">Upload</Link>
      </div>
    </nav>
  );
}

export default Navbar;
