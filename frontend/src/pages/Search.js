import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Search as SearchIcon, Ship, MapPin, ChevronDown, ChevronUp, Loader } from 'lucide-react';

const Search = () => {
    const [schedules, setSchedules] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [polId, setPolId] = useState('');
    const [podId, setPodId] = useState('');
    const [expandedRows, setExpandedRows] = useState(new Set());
    const [searchResults, setSearchResults] = useState({ pol: [], pod: [] });

    const fetchSchedules = useCallback(async () => {
        setLoading(true);
        try {
            const params = {};
            if (polId) params.from_port_id = polId;
            if (podId) params.to_port_id = podId;

            const response = await axios.get('http://localhost:8000/api/schedules/', { params });
            let data = response.data;

            if (searchTerm) {
                data = data.filter(s =>
                    s.vessel_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    s.voyage.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    s.service_code?.toLowerCase().includes(searchTerm.toLowerCase())
                );
            }
            setSchedules(data);
        } catch (err) {
            console.error("Error fetching schedules:", err);
        } finally {
            setLoading(false);
        }
    }, [searchTerm, polId, podId]);

    useEffect(() => {
        fetchSchedules();
    }, [fetchSchedules]);

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

    return (
        <div className="container">
            <div className="card">
                <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                    <h1 style={{ color: 'var(--primary-color)', margin: '0 0 8px 0', fontSize: '28px', fontWeight: '800' }}>Vessel Schedules</h1>
                    <p style={{ color: 'var(--text-muted)' }}>Browse individual vessel rotations and availability.</p>
                </div>

                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '16px',
                    background: '#f8fafc',
                    padding: '24px',
                    borderRadius: '16px',
                    border: '1px solid var(--border-color)',
                    marginBottom: '32px',
                    alignItems: 'end'
                }}>
                    <div style={{ position: 'relative' }}>
                        <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', marginBottom: '8px', color: 'var(--primary-color)', textTransform: 'uppercase' }}>Filter by POL</label>
                        <div style={{ position: 'relative' }}>
                            <MapPin size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
                            <input
                                placeholder="Search Port..."
                                value={polSearch}
                                onChange={(e) => handlePortSearch(e.target.value, 'pol')}
                                style={{ width: '100%', padding: '10px 10px 10px 36px', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '14px' }}
                            />
                        </div>
                        {searchResults.pol?.length > 0 && (
                            <div style={{ position: 'absolute', background: 'white', border: '1px solid var(--border-color)', width: '100%', zIndex: 10, borderRadius: '8px', boxShadow: 'var(--shadow-md)', marginTop: '4px', maxHeight: '200px', overflowY: 'auto' }}>
                                {searchResults.pol.map(p => (
                                    <div key={p.id} onClick={() => {
                                        setPolId(p.id);
                                        setPolSearch(`${p.code} - ${p.name}`);
                                        setSearchResults(prev => ({ ...prev, pol: [] }));
                                    }} style={{ padding: '8px 12px', cursor: 'pointer', borderBottom: '1px solid #f1f5f9', fontSize: '13px' }}>
                                        <strong>{p.code}</strong> - {p.name}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div style={{ position: 'relative' }}>
                        <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', marginBottom: '8px', color: 'var(--primary-color)', textTransform: 'uppercase' }}>Filter by POD</label>
                        <div style={{ position: 'relative' }}>
                            <MapPin size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
                            <input
                                placeholder="Search Port..."
                                value={podSearch}
                                onChange={(e) => handlePortSearch(e.target.value, 'pod')}
                                style={{ width: '100%', padding: '10px 10px 10px 36px', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '14px' }}
                            />
                        </div>
                        {searchResults.pod?.length > 0 && (
                            <div style={{ position: 'absolute', background: 'white', border: '1px solid var(--border-color)', width: '100%', zIndex: 10, borderRadius: '8px', boxShadow: 'var(--shadow-md)', marginTop: '4px', maxHeight: '200px', overflowY: 'auto' }}>
                                {searchResults.pod.map(p => (
                                    <div key={p.id} onClick={() => {
                                        setPodId(p.id);
                                        setPodSearch(`${p.code} - ${p.name}`);
                                        setSearchResults(prev => ({ ...prev, pod: [] }));
                                    }} style={{ padding: '8px 12px', cursor: 'pointer', borderBottom: '1px solid #f1f5f9', fontSize: '13px' }}>
                                        <strong>{p.code}</strong> - {p.name}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div>
                        <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', marginBottom: '8px', color: 'var(--primary-color)', textTransform: 'uppercase' }}>Vessel / Voyage</label>
                        <div style={{ position: 'relative' }}>
                            <SearchIcon size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
                            <input
                                placeholder="Search..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                style={{ width: '100%', padding: '10px 10px 10px 36px', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '14px' }}
                            />
                        </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px' }}>
                        <button
                            onClick={fetchSchedules}
                            style={{ flex: 1, height: '40px', background: 'var(--primary-color)', color: 'white', border: 'none', borderRadius: '8px', fontWeight: '700', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                        >
                            <SearchIcon size={18} /> Search
                        </button>
                        {(polId || podId) && (
                            <button onClick={() => { setPolId(''); setPodId(''); fetchSchedules(); }} style={{ height: '40px', padding: '0 12px', background: 'white', border: '1px solid var(--border-color)', borderRadius: '8px', cursor: 'pointer' }}>Reset</button>
                        )}
                    </div>
                </div>

                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 8px' }}>
                        <thead>
                            <tr style={{ color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase', fontWeight: '700' }}>
                                <th style={{ textAlign: 'left', padding: '0 16px' }}>Vessel / Voyage</th>
                                <th style={{ textAlign: 'left', padding: '0 16px' }}>Rotation</th>
                                <th style={{ textAlign: 'center', padding: '0 16px' }}>Status</th>
                                <th style={{ textAlign: 'center', padding: '0 16px' }}>Balance</th>
                                <th style={{ textAlign: 'right', padding: '0 16px' }}>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="5" style={{ textAlign: 'center', padding: '60px' }}><Loader className="animate-spin" style={{ margin: '0 auto' }} /></td></tr>
                            ) : schedules.length === 0 ? (
                                <tr><td colSpan="5" style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>No schedules found.</td></tr>
                            ) : schedules.map(s => (
                                <React.Fragment key={s.id}>
                                    <tr style={{ background: 'white', boxShadow: 'var(--shadow-sm)' }}>
                                        <td style={{ padding: '16px', borderTopLeftRadius: '12px', borderBottomLeftRadius: '12px' }}>
                                            <div style={{ fontWeight: '800', color: 'var(--primary-color)' }}>{s.vessel_name}</div>
                                            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{s.voyage}</div>
                                        </td>
                                        <td style={{ padding: '16px' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', fontSize: '12px', color: '#475569' }}>
                                                {s.port_calls.slice(0, 3).map((pc, i) => (
                                                    <span key={i}>{pc.port_code}{i < Math.min(s.port_calls.length, 3) - 1 ? ' → ' : ''}</span>
                                                ))}
                                                {s.port_calls.length > 3 && ' ...'}
                                            </div>
                                        </td>
                                        <td style={{ padding: '16px', textAlign: 'center' }}>
                                            <span style={{ padding: '4px 10px', borderRadius: '20px', fontSize: '10px', fontWeight: '800', background: '#dcfce7', color: '#166534' }}>{s.status}</span>
                                        </td>
                                        <td style={{ padding: '16px', textAlign: 'center', fontWeight: '800' }}>{s.total_balance}</td>
                                        <td style={{ padding: '16px', textAlign: 'right', borderTopRightRadius: '12px', borderBottomRightRadius: '12px' }}>
                                            <button onClick={() => toggleRow(s.id)} style={{ padding: '8px 16px', borderRadius: '8px', background: 'white', border: '1px solid var(--border-color)', fontWeight: '700', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                                                Itinerary {expandedRows.has(s.id) ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                                            </button>
                                        </td>
                                    </tr>
                                    {expandedRows.has(s.id) && (
                                        <tr>
                                            <td colSpan="5" style={{ padding: '0 16px 16px 16px' }}>
                                                <div style={{ background: '#f8fafc', padding: '24px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                                                    <table style={{ width: '100%', fontSize: '13px' }}>
                                                        <thead style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border-color)' }}>
                                                            <tr>
                                                                <th style={{ textAlign: 'left', paddingBottom: '12px' }}>Port</th>
                                                                <th style={{ textAlign: 'center', paddingBottom: '12px' }}>ETA</th>
                                                                <th style={{ textAlign: 'center', paddingBottom: '12px' }}>ETD</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {s.port_calls.map((pc, idx) => (
                                                                <tr key={idx}>
                                                                    <td style={{ padding: '12px 0' }}>
                                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                                            <MapPin size={14} color="#94a3b8" />
                                                                            {pc.port_name} ({pc.port_code})
                                                                        </div>
                                                                    </td>
                                                                    <td style={{ textAlign: 'center' }}>{pc.eta ? new Date(pc.eta).toLocaleDateString() : '--'}</td>
                                                                    <td style={{ textAlign: 'center' }}>{pc.etd ? new Date(pc.etd).toLocaleDateString() : '--'}</td>
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default Search;
