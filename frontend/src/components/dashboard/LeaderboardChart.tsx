import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { LeaderboardModel } from '@/types/poker';

interface LeaderboardChartProps {
    data: LeaderboardModel[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="custom-tooltip">
                <p className="label">{`${label}`}</p>
                <p className="intro">{`Profit: $${payload[0].value.toLocaleString()}`}</p>
                <p className="desc">{`Win Rate: ${payload[0].payload.winRate.toFixed(1)}%`}</p>
            </div>
        );
    }
    return null;
};

const LeaderboardChart: React.FC<LeaderboardChartProps> = ({ data }) => {
    return (
        <ResponsiveContainer width="100%" height={300}>
            <BarChart
                data={data}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="profit" fill="#8884d8" name="Profit/Loss ($)" />
            </BarChart>
        </ResponsiveContainer>
    );
};

export default LeaderboardChart;