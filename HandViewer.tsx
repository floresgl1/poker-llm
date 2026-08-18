import React from 'react';
import { HandHistoryData, HandAction } from '../../types/poker';

interface HandViewerProps {
    hand: HandHistoryData;
    onClose: () => void;
}

const HandViewer: React.FC<HandViewerProps> = ({ hand, onClose }) => {
    const streets = ['Pre-flop', 'Flop', 'Turn', 'River'];
    const actionsByStreet: { [key: string]: HandAction[] } = {};
    let finalBoard: string[] = [];

    hand.actions.forEach(action => {
        if (!actionsByStreet[action.street]) {
            actionsByStreet[action.street] = [];
        }
        actionsByStreet[action.street].push(action);
        if (action.board) {
            finalBoard = action.board;
        }
    });

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Hand Details: {hand.hand_id}</h2>
                    <button onClick={onClose} className="close-button">&times;</button>
                </div>
                <div className="modal-body">
                    <div className="hand-summary">
                        <p><strong>Winner:</strong> {hand.winner} (Won ${hand.pot.toLocaleString()})</p>
                        <div className="player-hands">
                            {hand.players.map(p => (
                                <div key={p.name}>
                                    <strong>{p.name}:</strong> <span>{p.hand.join(' ')}</span>
                                </div>
                            ))}
                        </div>
                        {finalBoard.length > 0 && (
                            <p><strong>Final Board:</strong> {finalBoard.join(' ')}</p>
                        )}
                    </div>

                    <div className="action-log">
                        {streets.map(street => (
                            actionsByStreet[street] && (
                                <div key={street} className="street-actions">
                                    <h4>{street} {actionsByStreet[street][0].board ? `[ ${actionsByStreet[street][0].board?.join(' ')} ]` : ''}</h4>
                                    <ul>
                                        {actionsByStreet[street].map((action, index) => (
                                            <li key={index}>
                                                <strong>{action.player}:</strong> {action.action}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default HandViewer;