import React from 'react';
import { Link } from 'react-router-dom';
import { LayoutDashboard, Search, Upload, Ship, Compass } from 'lucide-react';

const Dashboard = () => {
    return (
        <div className="container">
            <h1 style={{ color: 'var(--primary-color)', marginBottom: '32px' }}>Capacity Management Dashboard</h1>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
                <ModuleCard
                    title="Vessel Schedules"
                    description="Browse direct vessel rotations and port calls."
                    icon={<Ship size={24} />}
                    link="/search"
                    color="#002D5C"
                />
                <ModuleCard
                    title="Route Finder"
                    description="Intelligent pathfinding for direct and transshipment routes."
                    icon={<Compass size={24} />}
                    link="/routes"
                    highlight
                />
                <ModuleCard
                    title="Import Schedule"
                    description="Upload new vessel schedules from PDF or image files using AI-powered parsing."
                    icon={<Upload size={48} />}
                    link="/upload"
                    color="#F58220"
                />
                <ModuleCard
                    title="Analytics"
                    description="Analyze historical utilization and forecast future capacity requirements."
                    icon={<LayoutDashboard size={48} />}
                    link="/"
                    color="#10b981"
                    disabled
                />
            </div>
        </div>
    );
};

const ModuleCard = ({ title, description, icon, link, color, disabled }) => (
    <div className="card" style={{ opacity: disabled ? 0.6 : 1, transition: 'transform 0.2s', cursor: disabled ? 'not-allowed' : 'pointer' }}>
        <Link to={disabled ? '#' : link} style={{ textDecoration: 'none', color: 'inherit' }}>
            <div style={{ color, marginBottom: '20px' }}>{icon}</div>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '20px' }}>{title}</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '14px', lineHeight: 1.6 }}>{description}</p>
            {!disabled && (
                <div style={{ marginTop: '20px', color, fontWeight: '600', display: 'flex', alignItems: 'center' }}>
                    Get Started →
                </div>
            )}
        </Link>
    </div>
);

export default Dashboard;
