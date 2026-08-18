// frontend/src/views/Dashboard.tsx

import React, { useState, useEffect, useMemo } from 'react';
import { fetchLeaderboard, fetchTournamentResults, fetchHandDetails, fetchHandHistories } from '@/services/api';
import { LeaderboardData, TournamentData, LeaderboardModel, HandHistoryData } from '@/types/poker';
import '@/styles/Dashboard.css';
import LeaderboardChart from '@/components/dashboard/LeaderboardChart';
import HandHistoryList from '@/components/dashboard/HandHistoryList';
import HandViewer from '@/components/dashboard/HandViewer';
import H2HMatrix from '@/components/dashboard/H2HMatrix';
import WinRatePieChart from '@/components/dashboard/WinRatePieChart';
import EliminationsTimeline from '@/components/dashboard/EliminationsTimeline';
import { unparse } from 'papaparse';

const Dashboard: React.FC = () => {
    const [leaderboard, setLeaderboard] = useState<LeaderboardData | null>(null);
    const [tournament, setTournament] = useState<TournamentData | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [selectedHand, setSelectedHand] = useState<HandHistoryData | null>(null);
    const [searchQuery, setSearchQuery] = useState<string>('');

    // Sorting state for the leaderboard
    type SortKey = keyof LeaderboardModel;
    const [sortKey, setSortKey] = useState<SortKey>('rank');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

    const handleSort = (key: SortKey) => {
        if (sortKey === key) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortKey(key);
            setSortOrder('asc');
        }
    };

    const handleSelectHand = async (handId: string) => {
        try {
            const handDetails = await fetchHandDetails(handId);
            setSelectedHand(handDetails);
        } catch (error) {
            console.error("Failed to fetch hand details:", error);
        }
    };

    const handleExportCSV = (data: any[], filename: string) => {
        if (!data || data.length === 0) {
            console.error("No data to export.");
            return;
        }
        const csv = unparse(data);
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const sortedModels = useMemo(() => {
        if (!leaderboard) return [];

        const filteredModels = leaderboard.models.filter(model =>
            model.name.toLowerCase().includes(searchQuery.toLowerCase())
        );

        // Create a mutable copy before sorting
        return [...filteredModels].sort((a, b) => {
            const valA = a[sortKey];
            const valB = b[sortKey];
            return (valA < valB ? -1 : 1) * (sortOrder === 'asc' ? 1 : -1);
        });
    }, [leaderboard, sortKey, sortOrder, searchQuery]);

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            try {
                const [leaderboardData, tournamentData] = await Promise.all([
                    fetchLeaderboard(),
                    fetchTournamentResults()
                ]);
                setLeaderboard(leaderboardData);
                setTournament(tournamentData);
            } catch (error) {
                console.error("Failed to fetch dashboard data:", error);
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    if (loading) {
        return <div className="loading">Loading Dashboard...</div>;
    }

    return (
        <div className="dashboard">
            <h1>Poker LLM Engine Dashboard</h1>

            <div className="widget-container">
                {leaderboard && (
                    <div className="widget card">
                        <div className="widget-header">
                            <h2>{leaderboard.title}</h2>
                            <button onClick={() => handleExportCSV(sortedModels, 'leaderboard_results.csv')} className="export-button">Export CSV</button>
                        </div>
                        <div className="chart-grid">
                            <LeaderboardChart data={leaderboard.models} />
                            <WinRatePieChart data={leaderboard.models} />
                        </div>
                        <div className="filter-container">
                            <input
                                type="text"
                                placeholder="Filter models by name..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="filter-input"
                            />
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    {['rank', 'name', 'winRate', 'profit'].map((key) => (
                                        <th key={key} onClick={() => handleSort(key as SortKey)} className="sortable">
                                            {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                                            {sortKey === key && (
                                                <span className={`sort-arrow ${sortOrder}`}></span>
                                            )}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {sortedModels.map((model) => (
                                    // Using model.name as key because rank changes with sorting
                                    <tr key={model.name}>
                                        <td>{model.rank}</td>
                                        <td>{model.name}</td>
                                        <td>{model.winRate.toFixed(1)}</td>
                                        <td className={model.profit >= 0 ? 'profit' : 'loss'}>
                                            {model.profit.toLocaleString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        <H2HMatrix models={leaderboard.models} />
                    </div>
                )}

                {tournament && (
                     <div className="widget card">
                        <div className="widget-header">
                            <h2>{tournament.title}</h2>
                            <button onClick={() => handleExportCSV(tournament.players, 'tournament_standings.csv')} className="export-button">Export CSV</button>
                        </div>
                        <div className="tournament-meta">
                            <span>Blinds: <strong>${tournament.blinds[0]}/${tournament.blinds[1]}</strong></span>
                            <span>Level: <strong>{tournament.current_blind_level}</strong></span>
                            <span>Hands Played: <strong>{tournament.hands_played}</strong></span>
                        </div>

                        <h3>Standings</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Pos</th>
                                    <th>Player</th>
                                    <th>Stack</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {tournament.players.map((player) => (
                                    <tr key={player.position}>
                                        <td>{player.position}</td>
                                        <td>{player.name}</td>
                                        <td>${player.stack.toLocaleString()}</td>
                                        <td>{player.stack > 0 ? 'Active' : 'Eliminated'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        <EliminationsTimeline data={tournament.eliminations} />

                        {tournament.eliminations.length > 0 && (
                            <div className="eliminations-log">
                                <h3>Eliminations</h3>
                                <ul>
                                    {tournament.eliminations.map((elim, index) => (
                                        <li key={index}>Hand #{elim.hand_number}: <strong>{elim.player_name}</strong> finished in {elim.finished_place}th place.</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                )}

                <div className="widget card">
                    <HandHistoryList onSelectHand={handleSelectHand} />
                </div>
            </div>

            {selectedHand && <HandViewer hand={selectedHand} onClose={() => setSelectedHand(null)} />}
        </div>
    );
};

export default Dashboard;