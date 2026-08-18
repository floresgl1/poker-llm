import React from 'react';
import { LeaderboardModel } from '@/types/poker';

interface H2HMatrixProps {
    models: LeaderboardModel[];
}

const H2HMatrix: React.FC<H2HMatrixProps> = ({ models }) => {
    const modelNames = models.map(m => m.name);

    return (
        <div className="h2h-matrix">
            <h3>Head-to-Head Records</h3>
            <table>
                <thead>
                    <tr>
                        <th>vs</th>
                        {modelNames.map(name => <th key={name}>{name}</th>)}
                    </tr>
                </thead>
                <tbody>
                    {models.map(rowModel => (
                        <tr key={rowModel.name}>
                            <th>{rowModel.name}</th>
                            {models.map(colModel => {
                                if (rowModel.name === colModel.name) {
                                    return <td key={colModel.name} className="h2h-self">—</td>;
                                }
                                const record = rowModel.h2h_records?.[colModel.name];
                                if (!record) {
                                    return <td key={colModel.name} className="h2h-nodata">N/A</td>;
                                }
                                const { wins, losses, ties } = record;
                                return (
                                    <td key={colModel.name} className="h2h-record">
                                        {`${wins}-${losses}-${ties}`}
                                    </td>
                                );
                            })}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default H2HMatrix;