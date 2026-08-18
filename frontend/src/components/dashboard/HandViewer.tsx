import React from 'react';
import { HandHistoryData, HandAction } from '@/types/poker';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog";

interface HandViewerProps {
    hand: HandHistoryData | null;
    onClose: () => void;
}

const HandViewer: React.FC<HandViewerProps> = ({ hand, onClose }) => {
    if (!hand) return null;

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
        <Dialog open={!!hand} onOpenChange={onClose}>
            <DialogContent className="max-w-3xl">
                <DialogHeader>
                    <DialogTitle>Hand Details: {hand.hand_id}</DialogTitle>
                    <DialogDescription>
                        A step-by-step replay of the hand's action.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4 max-h-[70vh] overflow-y-auto">
                    <div className="bg-gray-50 p-4 rounded-lg border">
                        <p><strong>Winner:</strong> {hand.winner} (Won ${hand.pot.toLocaleString()})</p>
                        <div className="flex gap-6 my-2">
                            {hand.players.map(p => (
                                <div key={p.name}>
                                    <strong>{p.name}:</strong> <span className="font-mono">{p.hand.join(' ')}</span>
                                </div>
                            ))}
                        </div>
                        {finalBoard.length > 0 && (
                            <p><strong>Final Board:</strong> <span className="font-mono">{finalBoard.join(' ')}</span></p>
                        )}
                    </div>

                    <div className="space-y-4">
                        {streets.map(street => (
                            actionsByStreet[street] && (
                                <div key={street}>
                                    <h4 className="font-semibold bg-gray-100 p-2 rounded-md">{street} {actionsByStreet[street][0].board ? <span className="font-mono">[ {actionsByStreet[street][0].board?.join(' ')} ]</span> : ''}</h4>
                                    <ul className="pl-4 mt-2 space-y-1">
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
            </DialogContent>
        </Dialog>
    );
};

export default HandViewer;