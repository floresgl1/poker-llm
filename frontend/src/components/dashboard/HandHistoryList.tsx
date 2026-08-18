import React, { useState, useEffect } from 'react';
import { fetchHandHistories } from '@/services/api';
import { Button } from '@/components/ui/button';

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
        <div>
            <ul className="max-h-96 overflow-y-auto">
                {hands.map(hand => (
                    <li key={hand.hand_id} onClick={() => onSelectHand(hand.hand_id)} className="flex justify-between p-3 border-b cursor-pointer hover:bg-gray-50">
                        <span>{hand.hand_id}</span>
                        <small>{new Date(hand.timestamp * 1000).toLocaleString()}</small>
                    </li>
                ))}
            </ul>
            <div className="flex items-center justify-between pt-4 mt-2 border-t">
                <Button variant="outline" onClick={() => setCurrentPage(p => p - 1)} disabled={currentPage <= 1}>Previous</Button>
                <span>Page {currentPage} of {totalPages}</span>
                <Button variant="outline" onClick={() => setCurrentPage(p => p + 1)} disabled={currentPage >= totalPages}>Next</Button>
            </div>
        </div>
    );
};

export default HandHistoryList;