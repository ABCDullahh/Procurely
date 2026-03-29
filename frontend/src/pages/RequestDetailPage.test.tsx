import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import RequestDetailPage from '@/pages/RequestDetailPage'
import { requestsApi } from '@/lib/requests-api'

// Mock the API module
vi.mock('@/lib/requests-api', () => ({
    requestsApi: {
        get: vi.fn(),
        listRuns: vi.fn(),
    },
}))

// Mock the child components
vi.mock('@/components/VendorResultsTable', () => ({
    default: () => <div data-testid="vendor-results-table">VendorResultsTable</div>,
}))

vi.mock('@/components/VendorQuickView', () => ({
    default: () => <div data-testid="vendor-quick-view">VendorQuickView</div>,
}))

describe('RequestDetailPage', () => {
    let queryClient: QueryClient

    beforeEach(() => {
        queryClient = new QueryClient({
            defaultOptions: {
                queries: {
                    retry: false,
                },
            },
        })
        vi.clearAllMocks()
    })

    const renderWithProviders = (requestId: string = '1') => {
        return render(
            <QueryClientProvider client={queryClient}>
                <MemoryRouter initialEntries={[`/requests/${requestId}`]}>
                    <Routes>
                        <Route path="/requests/:id" element={<RequestDetailPage />} />
                    </Routes>
                </MemoryRouter>
            </QueryClientProvider>
        )
    }

    it('renders loading skeleton initially', async () => {
        // Mock API to return pending promise
        vi.mocked(requestsApi.get).mockImplementation(() => new Promise(() => { }))
        vi.mocked(requestsApi.listRuns).mockImplementation(() => new Promise(() => { }))

        renderWithProviders()

        // Skeleton should be visible while loading
        expect(document.querySelector('.animate-pulse')).toBeTruthy()
    })

    it('renders request title when API returns data', async () => {
        const mockRequest = {
            id: 1,
            title: 'Test Procurement Request',
            description: 'A test request for vendors',
            status: 'DRAFT' as const,
            category: 'Software',
            location: 'Remote',
            budget_min: 10000,
            budget_max: 50000,
            timeline: 'Q1 2024',
            keywords: ['api', 'integration'],
            must_have_criteria: ['API Integration'],
            nice_to_have_criteria: ['24/7 Support'],
            selected_providers: null,
            locale: 'id_ID',
            country_code: 'ID',
            region_bias: true,
            research_config: null,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
            user_id: 1,
            created_by_email: 'test@procurely.dev',
            latest_run_status: null,
            vendors_found: 0,
        }

        vi.mocked(requestsApi.get).mockResolvedValue(mockRequest)
        vi.mocked(requestsApi.listRuns).mockResolvedValue([])

        renderWithProviders()

        await waitFor(() => {
            expect(screen.getByText('Test Procurement Request')).toBeInTheDocument()
        })

        // Check description is displayed
        expect(screen.getByText('A test request for vendors')).toBeInTheDocument()

        // Check status badge
        expect(screen.getByText('DRAFT')).toBeInTheDocument()
    })

    it('shows error state when request not found', async () => {
        vi.mocked(requestsApi.get).mockRejectedValue(new Error('Not found'))
        vi.mocked(requestsApi.listRuns).mockResolvedValue([])

        renderWithProviders()

        await waitFor(() => {
            expect(screen.getByText(/not found/i)).toBeInTheDocument()
        })
    })
})
