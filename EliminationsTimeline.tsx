import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ZAxis } from 'recharts';
import { Elimination } from '../../types/poker';

interface EliminationsTimelineProps {
    data: Elimination[];
}

const EliminationsTimeline: React.FC<EliminationsTimelineProps> = ({ data }) => {
    // Sort data by hand number for a clear timeline
    const sortedData = [...data].sort((a, b) => a.hand_number - b.hand_number);

    return (
        <div className="chart-container">
            <h3>Eliminations Timeline</h3>
            <ResponsiveContainer width="100%" height={300}>
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <CartesianGrid />
                    <XAxis type="number" dataKey="hand_number" name="Hand #" unit="" />
                    <YAxis type="number" dataKey="finished_place" name="Place" unit="th" reversed={true} domain={['dataMin', 'dataMax']} />
                    <ZAxis dataKey="player_name" name="Player" />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                    <Legend />
                    <Scatter name="Eliminations" data={sortedData} fill="#ff7300" />
                </ScatterChart>
            </ResponsiveContainer>
        </div>
    );
};

export default EliminationsTimeline;