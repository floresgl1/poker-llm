// frontend/src/types/poker.ts

export interface LeaderboardModel {
    rank: number;
    name: string;
    wins: number;
    winRate: number;
    roi: number;
    profit: number;
}

export interface LeaderboardData {
    title: string;
    models: LeaderboardModel[];
}

export interface TournamentPlayer {
    position: number;
    name: string;    stack: number;
    status: string;
}

export interface TournamentData {
    title: string;
    players: TournamentPlayer[];
}
export interface Elimination {
    player_name: string;
    hand_number: number;
    finished_place: number;
}

export interface TournamentData {
    title: string;
    players: TournamentPlayer[];
    hands_played: number;
    current_blind_level: number;
    blinds: [number, number];
    eliminations: Elimination[];
}

// --- Hand History Types ---

export interface HandAction {
    street: 'Pre-flop' | 'Flop' | 'Turn' | 'River';
    player: string;
    action: string;
    board?: string[];
}

export interface HandHistoryData {
    hand_id: string;
    players: { name: string; hand: string[] }[];
    actions: HandAction[];
    winner: string;
    pot: number;
}

export interface PaginatedHandHistoryResponse {
    hands: {
        hand_id: string;
        timestamp: number;
    }[];
    total: number;
    page: number;
    limit: number;
}