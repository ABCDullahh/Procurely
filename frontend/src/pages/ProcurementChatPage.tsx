/**
 * ProcurementChatPage - Full-page AI chat interface for vendor search
 */

import { useNavigate, useSearchParams } from 'react-router-dom'
import { ProcurementChat } from '@/components/procurement-chat'

export default function ProcurementChatPage() {
    const navigate = useNavigate()
    const [searchParams] = useSearchParams()
    const runId = searchParams.get('run_id')
        ? parseInt(searchParams.get('run_id')!, 10)
        : undefined

    const handleVendorClick = (vendorId: number) => {
        navigate(`/vendors/${vendorId}`)
    }

    return (
        <div className="h-[calc(100vh-1rem)]">
            <ProcurementChat
                runId={runId}
                onVendorClick={handleVendorClick}
                className="h-full"
            />
        </div>
    )
}
