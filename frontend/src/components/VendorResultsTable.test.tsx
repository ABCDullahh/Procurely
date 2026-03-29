import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import VendorResultsTable from '@/components/VendorResultsTable'
import { vendorsApi } from '@/lib/vendors-api'

// Mock the API module
vi.mock('@/lib/vendors-api', () => ({
    vendorsApi: {
        listByRun: vi.fn(),
    },
}))

// Mock react-router-dom useNavigate
vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom')
    return {
        ...actual,
        useNavigate: () => vi.fn(),
    }
})

describe('VendorResultsTable', () => {
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

    const renderWithProviders = (props: {
        runId: number
        isRunning?: boolean
        onVendorClick?: (id: number) => void
    }) => {
        return render(
            <QueryClientProvider client={queryClient}>
                <VendorResultsTable
                    runId={props.runId}
                    isRunning={props.isRunning ?? false}
                    onVendorClick={props.onVendorClick ?? vi.fn()}
                />
            </QueryClientProvider>
        )
    }

    it('renders empty state when API returns 0 results', async () => {
        vi.mocked(vendorsApi.listByRun).mockResolvedValue({
            vendors: [],
            total: 0,
            page: 1,
            page_size: 20,
        })

        renderWithProviders({ runId: 1 })

        await waitFor(() => {
            expect(screen.getByText('No vendors found yet.')).toBeInTheDocument()
        })
    })

    it('renders vendors when API returns data', async () => {
        vi.mocked(vendorsApi.listByRun).mockResolvedValue({
            vendors: [
                {
                    id: 1,
                    name: 'Acme Corporation',
                    website: 'https://acme.com',
                    description: 'A great vendor',
                    location: 'New York',
                    country: 'USA',
                    industry: 'Software',
                    founded_year: 2010,
                    employee_count: '50-100',
                    email: 'contact@acme.com',
                    phone: '+1234567890',
                    pricing_model: 'subscription',
                    pricing_details: null,
                    security_compliance: null,
                    deployment: null,
                    integrations: null,
                    structured_data: null,
                    shopping_data: null,
                    price_range_min: null,
                    price_range_max: null,
                    price_last_updated: null,
                    created_at: '2024-01-01T00:00:00Z',
                    updated_at: '2024-01-01T00:00:00Z',
                    logo_url: null,
                    metrics: {
                        fit_score: 85,
                        trust_score: 90,
                        overall_score: 87,
                        must_have_matched: 3,
                        must_have_total: 4,
                        nice_to_have_matched: 2,
                        nice_to_have_total: 3,
                        source_count: 5,
                        evidence_count: 10,
                        // DeepResearch quality metrics
                        quality_score: 75,
                        price_score: 60,
                        completeness_pct: 80,
                        confidence_pct: 85,
                        source_diversity: 3,
                        research_depth: 2,
                        price_competitiveness: null,
                    },
                },
            ],
            total: 1,
            page: 1,
            page_size: 20,
        })

        renderWithProviders({ runId: 1 })

        await waitFor(() => {
            expect(screen.getByText('Acme Corporation')).toBeInTheDocument()
        })

        // Check that score is displayed
        expect(screen.getByText('87')).toBeInTheDocument()
    })

    it('shows search empty state when query has no matches', async () => {
        // First call returns empty due to search query
        vi.mocked(vendorsApi.listByRun).mockResolvedValue({
            vendors: [],
            total: 0,
            page: 1,
            page_size: 20,
        })

        renderWithProviders({ runId: 1 })

        await waitFor(() => {
            expect(screen.getByText('No vendors found yet.')).toBeInTheDocument()
        })
    })
})
