import React, { useState, useEffect } from 'react';
import { fetchHandHistories } from '../../services/api';

interface HandHistoryListProps {
    onSelectHand: (handId: string) => void;
}

const HandHistoryList: React.FC<HandHistoryListProps> = ({ onSelectHand }) => {
    const [hands, setHands] = useState<{ hand_id: string; timestamp: number }[]>([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [loading, setLoading] = useState(true);
    const HANDS_PER_PAGE = 15;

    useEffect(() => {
        const loadHands = async () => {
            try {
                setLoading(true);
                const response = await fetchHandHistories(currentPage, HANDS_PER_PAGE);
                setHands(response.hands);
                setTotalPages(Math.ceil(response.total / HANDS_PER_PAGE));
            } catch (error) {
                console.error("Failed to load hand histories:", error);
            } finally {
                setLoading(false);
            }
        };
        loadHands();
    }, [currentPage]);

    if (loading) return <p>Loading hand histories...</p>;

    return (
        <div className="hand-history-list">
            <h2>Recent Hands</h2>
            <ul>
                {hands.map(hand => (
                    <li key={hand.hand_id} onClick={() => onSelectHand(hand.hand_id)}>
                        <span>{hand.hand_id}</span>
                        <small>{new Date(hand.timestamp * 1000).toLocaleString()}</small>
                    </li>
                ))}
            </ul>
            <div className="pagination-controls">
                <button onClick={() => setCurrentPage(p => p - 1)} disabled={currentPage <= 1}>Previous</button>
                <span>Page {currentPage} of {totalPages}</span>
                <button onClick={() => setCurrentPage(p => p + 1)} disabled={currentPage >= totalPages}>Next</button>
            </div>
        </div>
    );
};

export default HandHistoryList;