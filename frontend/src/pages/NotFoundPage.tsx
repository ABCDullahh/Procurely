/**
 * NotFoundPage - 404 error page with editorial styling
 */

import { Link } from 'react-router-dom'
import { Home, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function NotFoundPage() {
    return (
        <div className="min-h-screen bg-background grain-overlay flex items-center justify-center px-6">
            <div className="text-center max-w-md">
                {/* Illustration */}
                <div className="mb-8 mx-auto w-48 h-48 relative">
                    <svg
                        viewBox="0 0 200 200"
                        className="w-full h-full"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                    >
                        {/* Paper background */}
                        <rect
                            x="30"
                            y="40"
                            width="140"
                            height="120"
                            rx="8"
                            fill="#F3F0EB"
                            fillOpacity="0.8"
                        />
                        {/* Magnifying glass */}
                        <circle
                            cx="100"
                            cy="90"
                            r="35"
                            stroke="#A09A93"
                            strokeWidth="3"
                            fill="none"
                        />
                        <line
                            x1="125"
                            y1="115"
                            x2="150"
                            y2="140"
                            stroke="#A09A93"
                            strokeWidth="3"
                            strokeLinecap="round"
                        />
                        {/* Question mark */}
                        <text
                            x="100"
                            y="100"
                            textAnchor="middle"
                            fontSize="36"
                            fontFamily="Plus Jakarta Sans, system-ui, sans-serif"
                            fill="#6B6560"
                            opacity="0.8"
                        >
                            ?
                        </text>
                    </svg>
                </div>

                <h1 className="font-display text-display mb-4">Page not found</h1>
                <p className="text-muted-foreground mb-8">
                    The page you're looking for doesn't exist or has been moved.
                    Let's get you back on track.
                </p>

                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <Button asChild>
                        <Link to="/">
                            <Home className="mr-2 h-4 w-4" />
                            Go home
                        </Link>
                    </Button>
                    <Button variant="outline" onClick={() => window.history.back()}>
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        Go back
                    </Button>
                </div>
            </div>
        </div>
    )
}
