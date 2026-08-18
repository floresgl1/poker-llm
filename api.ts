import { LeaderboardData, TournamentData, HandHistoryData, PaginatedHandHistoryResponse } from '../types/poker';

// The base URL of your Python backend API
const API_BASE_URL = 'http://127.0.0.1:8000'; // Assuming your backend will run here

/**
 * Fetches model comparison leaderboard data from the backend.
 */
export const fetchLeaderboard = async (): Promise<LeaderboardData> => {
    console.log("Fetching leaderboard data...");
    const response = await fetch(`${API_BASE_URL}/leaderboard`);
    if (!response.ok) {
        throw new Error('Failed to fetch leaderboard data');
    }
    const data = await response.json();
    return data;
};

/**
 * Fetches the list of recent hand histories.
 */
export const fetchHandHistories = async (page: number, limit: number): Promise<PaginatedHandHistoryResponse> => {
    console.log(`Fetching hand history list for page ${page}...`);
    const response = await fetch(`${API_BASE_URL}/hands?page=${page}&limit=${limit}`);
    if (!response.ok) {
        throw new Error('Failed to fetch hand histories');
    }
    return await response.json();
};

/**
 * Fetches the detailed data for a single hand.
 * @param hand_id The ID of the hand to fetch.
 */
export const fetchHandDetails = async (hand_id: string): Promise<HandHistoryData> => {
    console.log(`Fetching details for hand ${hand_id}...`);
    const response = await fetch(`${API_BASE_URL}/hands/${hand_id}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch details for hand ${hand_id}`);
    }
    return await response.json();
};

/**
 * Fetches tournament results from the backend.
 */
export const fetchTournamentResults = async (): Promise<TournamentData> => {
    console.log("Fetching tournament results...");
    const response = await fetch(`${API_BASE_URL}/tournament`);
    if (!response.ok) {
        throw new Error('Failed to fetch tournament results');
    }
    const data = await response.json();
    return data;
};