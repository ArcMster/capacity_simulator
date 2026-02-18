import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Search, Upload, Ship, Compass, Calendar } from 'lucide-react';

const Navbar = () => {
    const location = useLocation();

    const navItemStyle = (path) => ({
        display: 'flex',
        alignItems: 'center',
        padding: '8px 16px',
        borderRadius: '8px',
        textDecoration: 'none',
        color: location.pathname === path ? 'white' : 'rgba(255, 255, 255, 0.8)',
        background: location.pathname === path ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
        fontWeight: '600',
        fontSize: '14px',
        transition: 'all 0.2s',
        gap: '8px'
    });

    const NavItem = ({ to, icon, label }) => (
        <Link to={to} style={navItemStyle(to)}>
            {icon} {label}
        </Link>
    );

    return (
        <nav style={{
            background: 'var(--primary-color)',
            padding: '12px 40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: 'var(--shadow-md)',
            position: 'sticky',
            top: 0,
            zIndex: 1000
        }}>
            <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '12px', textDecoration: 'none', color: 'white' }}>
                <div style={{ background: 'white', padding: '6px', borderRadius: '8px', display: 'flex' }}>
                    <Ship size={24} color="var(--primary-color)" />
                </div>
                <div style={{ fontWeight: '800', fontSize: '20px', letterSpacing: '-0.02em', display: 'flex', alignItems: 'baseline' }}>
                    i<span style={{ color: 'var(--primary-light)' }}>Route</span>
                </div>
            </Link>

            <div style={{ display: 'flex', gap: '8px' }}>
                <NavItem to="/" icon={<LayoutDashboard size={18} />} label="Dashboard" />
                <NavItem to="/search" icon={<Calendar size={18} />} label="Schedules" />
                <NavItem to="/routes" icon={<Compass size={18} />} label="Route Finder" />
                <NavItem to="/upload" icon={<Upload size={18} />} label="Import" />
            </div>
        </nav>
    );
};

export default Navbar;
