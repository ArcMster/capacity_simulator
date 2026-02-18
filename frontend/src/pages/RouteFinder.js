import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Search as SearchIcon, Ship, MapPin, ChevronDown, ChevronUp, Loader, Layers } from 'lucide-react';

const RouteFinder = () => {
    const [routes, setRoutes] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [polId, setPolId] = useState('');
    const [podId, setPodId] = useState('');
    const [expandedRows, setExpandedRows] = useState(new Set());
    const [expandedVoyages, setExpandedVoyages] = useState(new Set());
    const [searchResults, setSearchResults] = useState({ pol: [], pod: [] });

    const fetchRoutes = useCallback(async () => {
        if (!polId || !podId) return;
        setLoading(true);
        try {
            const params = { from_port_id: polId, to_port_id: podId };
            const response = await axios.get('http://localhost:8000/api/schedules/find_routes/', { params });
            let data = response.data;

            if (searchTerm) {
                data = data.filter(route =>
                    route.legs.some(leg =>
                        leg.vessel_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        leg.voyage.toLowerCase().includes(searchTerm.toLowerCase())
                    )
                );
            }
            setRoutes(data);
        } catch (err) {
            console.error("Error fetching routes:", err);
        } finally {
            setLoading(false);
        }
    }, [searchTerm, polId, podId]);

    useEffect(() => {
        fetchRoutes();
    }, [fetchRoutes]);

    const [polSearch, setPolSearch] = useState('');
    const [podSearch, setPodSearch] = useState('');

    const handlePortSearch = async (val, type) => {
        if (type === 'pol') setPolSearch(val);
        else setPodSearch(val);

        if (val.length < 2) {
            setSearchResults(prev => ({ ...prev, [type]: [] }));
            return;
        }
        try {
            const res = await axios.get(`http://localhost:8000/api/autocomplete/port/?q=${val}`);
            setSearchResults(prev => ({ ...prev, [type]: res.data }));
        } catch (err) {
            console.error(err);
        }
    };

    const toggleRow = (id) => {
        const newExpanded = new Set(expandedRows);
        if (newExpanded.has(id)) newExpanded.delete(id);
        else newExpanded.add(id);
        setExpandedRows(newExpanded);
    };

    const toggleVoyage = (id) => {
        const newExpanded = new Set(expandedVoyages);
        if (newExpanded.has(id)) newExpanded.delete(id);
        else newExpanded.add(id);
        setExpandedVoyages(newExpanded);
    };

    return (
        <div className="container">
            <div className="card">
                <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                    <h1 style={{ color: 'var(--primary-color)', margin: '0 0 8px 0', fontSize: '28px', fontWeight: '800' }}>Intelligent Route Finder</h1>
                    <p style={{ color: 'var(--text-muted)' }}>Find the best direct and transshipment options between ports.</p>
                </div>

                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                    gap: '24px',
                    background: 'rgba(248, 250, 252, 0.8)',
                    backdropFilter: 'blur(8px)',
                    padding: '32px',
                    borderRadius: '24px',
                    border: '1px solid var(--border-color)',
                    marginBottom: '40px',
                    alignItems: 'end',
                    boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.02)'
                }}>
                    <div style={{ position: 'relative' }}>
                        <label style={{ display: 'block', fontSize: '11px', fontWeight: '800', marginBottom: '10px', color: 'var(--primary-color)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Port of Loading (POL)</label>
                        <div style={{ position: 'relative' }}>
                            <MapPin size={18} style={{ position: 'absolute', left: '14px', top: '13px', color: 'var(--text-muted)' }} />
                            <input
                                placeholder="Search POL..."
                                value={polSearch}
                                onChange={(e) => handlePortSearch(e.target.value, 'pol')}
                                style={{ width: '100%', padding: '12px 12px 12px 44px', borderRadius: '12px', border: '1px solid var(--border-color)', fontSize: '14px', fontWeight: '500', transition: 'border-color 0.2s' }}
                                onFocus={(e) => e.target.style.borderColor = 'var(--primary-color)'}
                                onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
                            />
                        </div>
                        {searchResults.pol?.length > 0 && (
                            <div style={{ position: 'absolute', background: 'white', border: '1px solid var(--border-color)', width: '100%', zIndex: 100, borderRadius: '12px', boxShadow: 'var(--shadow-lg)', marginTop: '8px', maxHeight: '250px', overflowY: 'auto' }}>
                                {searchResults.pol.map(p => (
                                    <div key={p.id} onClick={() => {
                                        setPolId(p.id);
                                        setPolSearch(`${p.code} - ${p.name}`);
                                        setSearchResults(prev => ({ ...prev, pol: [] }));
                                    }} style={{ padding: '12px 16px', cursor: 'pointer', borderBottom: '1px solid #f1f5f9', fontSize: '14px', transition: 'background 0.2s' }} onMouseOver={(e) => e.target.style.background = '#f8fafc'} onMouseOut={(e) => e.target.style.background = 'transparent'}>
                                        <strong style={{ color: 'var(--primary-color)' }}>{p.code}</strong> - {p.name}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div style={{ position: 'relative' }}>
                        <label style={{ display: 'block', fontSize: '11px', fontWeight: '800', marginBottom: '10px', color: 'var(--primary-color)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Port of Discharge (POD)</label>
                        <div style={{ position: 'relative' }}>
                            <MapPin size={18} style={{ position: 'absolute', left: '14px', top: '13px', color: 'var(--text-muted)' }} />
                            <input
                                placeholder="Search POD..."
                                value={podSearch}
                                onChange={(e) => handlePortSearch(e.target.value, 'pod')}
                                style={{ width: '100%', padding: '12px 12px 12px 44px', borderRadius: '12px', border: '1px solid var(--border-color)', fontSize: '14px', fontWeight: '500', transition: 'border-color 0.2s' }}
                                onFocus={(e) => e.target.style.borderColor = 'var(--primary-color)'}
                                onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
                            />
                        </div>
                        {searchResults.pod?.length > 0 && (
                            <div style={{ position: 'absolute', background: 'white', border: '1px solid var(--border-color)', width: '100%', zIndex: 100, borderRadius: '12px', boxShadow: 'var(--shadow-lg)', marginTop: '8px', maxHeight: '250px', overflowY: 'auto' }}>
                                {searchResults.pod.map(p => (
                                    <div key={p.id} onClick={() => {
                                        setPodId(p.id);
                                        setPodSearch(`${p.code} - ${p.name}`);
                                        setSearchResults(prev => ({ ...prev, pod: [] }));
                                    }} style={{ padding: '12px 16px', cursor: 'pointer', borderBottom: '1px solid #f1f5f9', fontSize: '14px', transition: 'background 0.2s' }} onMouseOver={(e) => e.target.style.background = '#f8fafc'} onMouseOut={(e) => e.target.style.background = 'transparent'}>
                                        <strong style={{ color: 'var(--primary-color)' }}>{p.code}</strong> - {p.name}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div>
                        <label style={{ display: 'block', fontSize: '11px', fontWeight: '800', marginBottom: '10px', color: 'var(--primary-color)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Filter Vessel</label>
                        <div style={{ position: 'relative' }}>
                            <SearchIcon size={18} style={{ position: 'absolute', left: '14px', top: '13px', color: 'var(--text-muted)' }} />
                            <input
                                placeholder="Optional filter..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                style={{ width: '100%', padding: '12px 12px 12px 44px', borderRadius: '12px', border: '1px solid var(--border-color)', fontSize: '14px', fontWeight: '500' }}
                            />
                        </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                        <button
                            onClick={fetchRoutes}
                            style={{
                                width: '100%',
                                height: '46px',
                                background: 'linear-gradient(135deg, var(--primary-color), var(--primary-light))',
                                color: 'white',
                                border: 'none',
                                borderRadius: '12px',
                                fontWeight: '800',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '10px',
                                boxShadow: '0 4px 12px rgba(0, 45, 92, 0.2)',
                                transition: 'all 0.2s'
                            }}
                            onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
                            onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
                        >
                            <SearchIcon size={20} /> Find Best Routes
                        </button>
                    </div>
                </div>

                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 8px' }}>
                        <thead>
                            <tr style={{ color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase', fontWeight: '700' }}>
                                <th style={{ textAlign: 'left', padding: '0 16px' }}>Leg Info</th>
                                <th style={{ textAlign: 'left', padding: '0 16px' }}>Vessel(s)</th>
                                <th style={{ textAlign: 'center', padding: '0 16px' }}>Connection</th>
                                <th style={{ textAlign: 'center', padding: '0 16px' }}>Est. Duration</th>
                                <th style={{ textAlign: 'right', padding: '0 16px' }}>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="5" style={{ textAlign: 'center', padding: '60px' }}><Loader className="animate-spin" style={{ margin: '0 auto', color: 'var(--primary-color)' }} /></td></tr>
                            ) : routes.length === 0 ? (
                                <tr><td colSpan="5" style={{ textAlign: 'center', padding: '100px', color: 'var(--text-muted)' }}>
                                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
                                        <Layers size={48} style={{ opacity: 0.2 }} />
                                        <p style={{ fontSize: '16px' }}>{polId && podId ? 'No routes found for this selection.' : 'Select POL and POD to find routes.'}</p>
                                    </div>
                                </td></tr>
                            ) : routes.map((route, idx) => {
                                const routeId = `route-${idx}`;
                                const isExpanded = expandedRows.has(routeId);

                                return (
                                    <React.Fragment key={routeId}>
                                        <tr className="animate-fade-in" style={{
                                            background: 'white',
                                            boxShadow: isExpanded ? 'var(--shadow-md)' : 'var(--shadow-sm)',
                                            transform: isExpanded ? 'scale(1.005)' : 'none',
                                            zIndex: isExpanded ? 5 : 1,
                                            position: 'relative'
                                        }}>
                                            <td style={{ padding: '20px', borderTopLeftRadius: '16px', borderBottomLeftRadius: '16px' }}>
                                                <div style={{
                                                    display: 'inline-flex',
                                                    alignItems: 'center',
                                                    gap: '8px',
                                                    padding: '6px 12px',
                                                    borderRadius: '30px',
                                                    fontSize: '11px',
                                                    fontWeight: '800',
                                                    background: route.type === 'DIRECT' ? '#ecfdf5' : '#eff6ff',
                                                    color: route.type === 'DIRECT' ? '#059669' : '#1d4ed8',
                                                    border: `1px solid ${route.type === 'DIRECT' ? '#d1fae5' : '#dbeafe'}`
                                                }}>
                                                    {route.type === 'DIRECT' ? <Ship size={14} /> : <Layers size={14} />}
                                                    {route.type}
                                                </div>
                                            </td>
                                            <td style={{ padding: '20px' }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                                    {(route.vessel_names || []).map((vName, i, arr) => (
                                                        <React.Fragment key={i}>
                                                            <span style={{ fontSize: '15px', fontWeight: '700', color: 'var(--primary-color)' }}>{vName}</span>
                                                            {i < arr.length - 1 && <span style={{ color: '#94a3b8', fontSize: '18px' }}>›</span>}
                                                        </React.Fragment>
                                                    ))}
                                                </div>
                                            </td>
                                            <td style={{ padding: '20px', textAlign: 'center' }}>
                                                {route.type === 'TRANSSHIPMENT' ? (
                                                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                                        <span style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: '700', letterSpacing: '0.05em' }}>Via Port</span>
                                                        <span style={{ fontSize: '14px', fontWeight: '800', color: 'var(--primary-color)' }}>{route.trans_port_code}</span>
                                                    </div>
                                                ) : (
                                                    <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: '600' }}>No Stops</span>
                                                )}
                                            </td>
                                            <td style={{ padding: '20px', textAlign: 'center' }}>
                                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                                    <span style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: '700', letterSpacing: '0.05em' }}>Total Transit</span>
                                                    <span style={{ fontSize: '16px', fontWeight: '900', color: 'var(--accent-color)' }}>{route.total_duration_days ? `${route.total_duration_days}d` : '--'}</span>
                                                </div>
                                            </td>
                                            <td style={{ padding: '20px', textAlign: 'right', borderTopRightRadius: '16px', borderBottomRightRadius: '16px' }}>
                                                <button
                                                    onClick={() => toggleRow(routeId)}
                                                    style={{
                                                        padding: '10px 20px',
                                                        borderRadius: '12px',
                                                        background: isExpanded ? 'var(--primary-color)' : 'white',
                                                        color: isExpanded ? 'white' : 'var(--primary-color)',
                                                        border: `1px solid ${isExpanded ? 'var(--primary-color)' : 'var(--border-color)'}`,
                                                        fontWeight: '700',
                                                        cursor: 'pointer',
                                                        display: 'inline-flex',
                                                        alignItems: 'center',
                                                        gap: '8px',
                                                        transition: 'all 0.2s',
                                                        boxShadow: isExpanded ? 'var(--shadow-md)' : 'none'
                                                    }}
                                                >
                                                    {isExpanded ? 'Collapse' : 'View Detail'} {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                                </button>
                                            </td>
                                        </tr>
                                        {isExpanded && (
                                            <tr>
                                                <td colSpan="5" style={{ padding: '8px 20px 24px 20px' }}>
                                                    <div style={{
                                                        background: 'white',
                                                        padding: '32px',
                                                        borderRadius: '0 0 16px 16px',
                                                        border: '1px solid var(--border-color)',
                                                        borderTop: 'none',
                                                        boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.05)'
                                                    }}>
                                                        <div style={{ display: 'flex', gap: '40px' }}>
                                                            {/* Vertical Timeline Track */}
                                                            <div className="timeline-track" style={{ minHeight: '100px', flexShrink: 0 }}>
                                                                {/* This is the line, we'll place nodes inside the port list */}
                                                            </div>

                                                            <div style={{ flex: 1 }}>
                                                                {/* Render Legs as Groups */}
                                                                {route.legs.reduce((acc, leg, idx) => {
                                                                    // Simple grouping: if vessel name is same as previous, add to same group
                                                                    const prevLeg = acc[acc.length - 1];
                                                                    if (prevLeg && prevLeg.vessel_name === leg.vessel_name) {
                                                                        prevLeg.voyages.push(leg);
                                                                    } else {
                                                                        acc.push({ vessel_name: leg.vessel_name, voyages: [leg] });
                                                                    }
                                                                    return acc;
                                                                }, []).map((vGroup, gIdx) => (
                                                                    <div key={gIdx} className="vessel-group" style={{
                                                                        marginBottom: '24px',
                                                                        position: 'relative',
                                                                        borderLeft: '4px solid var(--primary-color)',
                                                                        paddingLeft: '24px'
                                                                    }}>
                                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
                                                                            <Ship size={20} color="var(--primary-color)" />
                                                                            <h3 style={{ margin: 0, fontSize: '18px', color: 'var(--primary-color)', fontWeight: '800' }}>{vGroup.vessel_name}</h3>
                                                                            <span style={{ fontSize: '11px', background: '#e0f2fe', color: '#0369a1', padding: '2px 8px', borderRadius: '4px', fontWeight: '700' }}>
                                                                                {vGroup.voyages.length > 1 ? `${vGroup.voyages.length} Linked Voyages` : 'Direct Voyage'}
                                                                            </span>
                                                                        </div>

                                                                        {vGroup.voyages.map((v, vIdx) => {
                                                                            const voyageId = `voyage-${v.id}`;
                                                                            const isVoyageExpanded = expandedVoyages.has(voyageId);

                                                                            return (
                                                                                <div key={vIdx} style={{ marginBottom: vIdx < vGroup.voyages.length - 1 ? '16px' : 0 }}>
                                                                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                                                                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '600' }}>
                                                                                            Voyage: <span style={{ color: 'var(--primary-color)', fontWeight: '700' }}>{v.voyage}</span>
                                                                                        </div>
                                                                                        <button
                                                                                            onClick={() => toggleVoyage(voyageId)}
                                                                                            style={{
                                                                                                fontSize: '11px',
                                                                                                background: 'transparent',
                                                                                                border: 'none',
                                                                                                color: 'var(--primary-color)',
                                                                                                cursor: 'pointer',
                                                                                                fontWeight: '700',
                                                                                                display: 'flex',
                                                                                                alignItems: 'center',
                                                                                                gap: '4px'
                                                                                            }}
                                                                                        >
                                                                                            {isVoyageExpanded ? 'Show less ports' : `Show all ${v.port_calls.length} ports`}
                                                                                            {isVoyageExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                                                                                        </button>
                                                                                    </div>
                                                                                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                                                                        <thead>
                                                                                            <tr style={{ color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                                                                                <th style={{ textAlign: 'left', paddingBottom: '12px', fontWeight: '700' }}>Port Call</th>
                                                                                                <th style={{ textAlign: 'center', paddingBottom: '12px', fontWeight: '700' }}>Date Information</th>
                                                                                            </tr>
                                                                                        </thead>
                                                                                        <tbody>
                                                                                            {v.port_calls.map((pc, pIdx) => {
                                                                                                const isLoad = pc.id === v.route_loading_pc_id;
                                                                                                const isDischarge = pc.id === v.route_discharging_pc_id;
                                                                                                const isTrans = route.type === 'TRANSSHIPMENT' && pc.port_code === route.trans_port_code;
                                                                                                const isSpecial = isLoad || isDischarge || isTrans;

                                                                                                if (!isVoyageExpanded && !isSpecial) return null;

                                                                                                return (
                                                                                                    <tr key={pIdx} style={{
                                                                                                        background: isSpecial ? 'rgba(0, 45, 92, 0.05)' : 'transparent',
                                                                                                        borderBottom: '1px solid #f1f5f9',
                                                                                                        transition: 'background 0.2s'
                                                                                                    }}>
                                                                                                        <td style={{ padding: '14px 16px' }}>
                                                                                                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', position: 'relative' }}>
                                                                                                                <div className={`timeline-node ${isLoad ? 'pol' : isDischarge ? 'pod' : isTrans ? 'ts' : ''}`} style={{ left: '-44px', top: '50%', transform: 'translateY(-50%)' }}></div>
                                                                                                                <div style={{ display: 'flex', flexDirection: 'column' }}>
                                                                                                                    <span style={{ fontWeight: isSpecial ? '800' : '600', color: isSpecial ? 'var(--primary-color)' : 'inherit', fontSize: '14px' }}>
                                                                                                                        {pc.port_name} ({pc.port_code})
                                                                                                                    </span>
                                                                                                                    <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
                                                                                                                        {isLoad && <span style={{ fontSize: '9px', background: '#059669', color: 'white', padding: '2px 6px', borderRadius: '4px', fontWeight: '800', textTransform: 'uppercase' }}>LOADED</span>}
                                                                                                                        {isDischarge && <span style={{ fontSize: '9px', background: '#dc2626', color: 'white', padding: '2px 6px', borderRadius: '4px', fontWeight: '800', textTransform: 'uppercase' }}>DISCHARGED</span>}
                                                                                                                        {isTrans && !isLoad && !isDischarge && <span style={{ fontSize: '9px', background: '#0369a1', color: 'white', padding: '2px 6px', borderRadius: '4px', fontWeight: '800', textTransform: 'uppercase' }}>TRANSIT HUB</span>}
                                                                                                                    </div>
                                                                                                                </div>
                                                                                                            </div>
                                                                                                        </td>
                                                                                                        <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                                                                                                            <div style={{ display: 'flex', justifyContent: 'center', gap: '24px' }}>
                                                                                                                <div style={{ display: 'flex', flexDirection: 'column', minWidth: '80px' }}>
                                                                                                                    <span style={{ fontSize: '9px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Arrival</span>
                                                                                                                    <span style={{ fontWeight: '600' }}>{pc.eta ? new Date(pc.eta).toLocaleDateString([], { month: 'short', day: 'numeric' }) : '--'}</span>
                                                                                                                </div>
                                                                                                                <div style={{ display: 'flex', flexDirection: 'column', minWidth: '80px' }}>
                                                                                                                    <span style={{ fontSize: '9px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Departure</span>
                                                                                                                    <span style={{ fontWeight: '600' }}>{pc.etd ? new Date(pc.etd).toLocaleDateString([], { month: 'short', day: 'numeric' }) : '--'}</span>
                                                                                                                </div>
                                                                                                            </div>
                                                                                                        </td>
                                                                                                    </tr>
                                                                                                );
                                                                                            })}
                                                                                        </tbody>
                                                                                    </table>
                                                                                </div>
                                                                            );
                                                                        })}
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </React.Fragment>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default RouteFinder;
