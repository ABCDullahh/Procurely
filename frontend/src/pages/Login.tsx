import { useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FileSearch, Loader2 } from 'lucide-react'
import { useAuth } from '@/hooks'
import { Button, Input, Label, Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui'

// Logo component with fallback to icon
const Logo = () => {
    const [imageError, setImageError] = useState(false)

    if (imageError) {
        return (
            <div className="mx-auto w-14 h-14 rounded-xl bg-crimson-600 flex items-center justify-center mb-4">
                <FileSearch className="w-7 h-7 text-white" />
            </div>
        )
    }

    return (
        <img
            src="/icon-logo.png"
            alt="Procurely"
            className="mx-auto w-14 h-14 rounded-xl mb-4"
            onError={() => setImageError(true)}
        />
    )
}

export function Login() {
    const navigate = useNavigate()
    const { login, isAuthenticated, isLoading: authLoading } = useAuth()
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    // Redirect if already authenticated
    if (authLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        )
    }

    if (isAuthenticated) {
        return <Navigate to="/" replace />
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        try {
            await login(email, password)
            navigate('/')
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Invalid credentials')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#FAF9F7] p-4">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="relative w-full max-w-md"
            >
                <Card className="border border-[#ECE8E1] shadow-sm">
                    <CardHeader className="text-center pb-2">
                        <Logo />
                        <CardTitle className="text-2xl font-display text-[#1A1816]">Welcome to Procurely</CardTitle>
                        <CardDescription className="text-[#A09A93]">
                            AI-powered procurement search copilot
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="email">Email</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="Enter your email"
                                    required
                                    autoComplete="email"
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="password">Password</Label>
                                <Input
                                    id="password"
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="Enter your password"
                                    required
                                    autoComplete="current-password"
                                />
                            </div>

                            {error && (
                                <motion.p
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="text-sm text-destructive text-center p-2 bg-destructive/10 rounded-lg"
                                >
                                    {error}
                                </motion.p>
                            )}

                            <Button
                                type="submit"
                                className="w-full bg-[#1A1816] hover:bg-[#1A1816]/90 text-white transition-all duration-200"
                                disabled={loading}
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                        Signing in...
                                    </>
                                ) : (
                                    'Sign in'
                                )}
                            </Button>

                        </form>
                    </CardContent>
                </Card>
            </motion.div>
        </div>
    )
}

export default Login
