import api from './api';

export interface FiscalResultItem {
    symbol: string;
    date_sell: string;
    date_buy: string;
    quantity: number;
    price_sell: number;
    price_buy: number;
    result: number;
}

export interface FiscalResultResponse {
    items: FiscalResultItem[];
    total_result: number;
}

export const fiscalService = {
    async getFiscalResults(portfolioId: string, startDate?: string, endDate?: string): Promise<FiscalResultResponse> {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);

        const response = await api.get(`/fiscal/${portfolioId}?${params.toString()}`);
        return response.data;
    }
};
