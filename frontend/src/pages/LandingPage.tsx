/**
 * LandingPage - World-class premium SaaS landing
 * Warm editorial aesthetic with CSS-only animations
 * Fonts: Fraunces (serif headings), Instrument Sans (body)
 */

import { useEffect, useRef, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
    Search,
    BarChart3,
    FileText,
    MessageSquare,
    Scale,
    Star,
    ArrowRight,
    CheckCircle2,
    Layers,
    Zap,
    Users,
    Shield,
    Globe,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks'

/* ------------------------------------------------------------------ */
/*  Inline styles (injected once)                                     */
/* ------------------------------------------------------------------ */
const LANDING_STYLES = `
/* Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,500;0,9..144,600;0,9..144,700&family=Instrument+Sans:wght@400;500;600;700&display=swap');

/* ---- Root variables ---- */
.lp-root {
    --lp-bg: #FAF9F7;
    --lp-card: #FFFFFF;
    --lp-border: #ECE8E1;
    --lp-text-1: #1A1816;
    --lp-text-2: #6B6560;
    --lp-text-3: #A09A93;
    --lp-crimson: #C8102E;
    --lp-crimson-light: #C8102E14;
    --lp-serif: 'Fraunces', Georgia, 'Times New Roman', serif;
    --lp-sans: 'Instrument Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.lp-root {
    font-family: var(--lp-sans);
    background: var(--lp-bg);
    color: var(--lp-text-1);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

.lp-root *, .lp-root *::before, .lp-root *::after {
    box-sizing: border-box;
}

/* ---- Serif heading ---- */
.lp-serif {
    font-family: var(--lp-serif);
    letter-spacing: -0.03em;
}

/* ---- Animations ---- */
@keyframes lp-fade-up {
    from {
        opacity: 0;
        transform: translateY(28px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes lp-fade-in {
    from { opacity: 0; }
    to   { opacity: 1; }
}

@keyframes lp-scale-in {
    from {
        opacity: 0;
        transform: scale(0.96);
    }
    to {
        opacity: 1;
        transform: scale(1);
    }
}

@keyframes lp-slide-left {
    from {
        opacity: 0;
        transform: translateX(40px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes lp-float {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-8px); }
}

@keyframes lp-pulse-dot {
    0%, 100% { opacity: 1; }
    50%      { opacity: 0.5; }
}

/* ---- Hero entrance animations ---- */
.lp-hero-badge {
    opacity: 0;
    animation: lp-fade-up 0.7s cubic-bezier(0.22, 1, 0.36, 1) 0.1s both;
}

.lp-hero-heading {
    opacity: 0;
    animation: lp-fade-up 0.8s cubic-bezier(0.22, 1, 0.36, 1) 0.25s both;
}

.lp-hero-sub {
    opacity: 0;
    animation: lp-fade-up 0.8s cubic-bezier(0.22, 1, 0.36, 1) 0.4s both;
}

.lp-hero-ctas {
    opacity: 0;
    animation: lp-fade-up 0.8s cubic-bezier(0.22, 1, 0.36, 1) 0.55s both;
}

.lp-hero-preview {
    opacity: 0;
    animation: lp-scale-in 1s cubic-bezier(0.22, 1, 0.36, 1) 0.7s both;
}

.lp-hero-stat-1 {
    opacity: 0;
    animation: lp-fade-in 0.6s ease 1.1s both;
}

.lp-hero-stat-2 {
    opacity: 0;
    animation: lp-fade-in 0.6s ease 1.3s both;
}

.lp-hero-stat-3 {
    opacity: 0;
    animation: lp-fade-in 0.6s ease 1.5s both;
}

/* ---- Scroll reveal ---- */
.lp-reveal {
    opacity: 0;
    transform: translateY(32px);
    transition: opacity 0.7s cubic-bezier(0.22, 1, 0.36, 1),
                transform 0.7s cubic-bezier(0.22, 1, 0.36, 1);
}

.lp-reveal.lp-visible {
    opacity: 1;
    transform: translateY(0);
}

/* Stagger children */
.lp-stagger > .lp-reveal:nth-child(1) { transition-delay: 0s; }
.lp-stagger > .lp-reveal:nth-child(2) { transition-delay: 0.1s; }
.lp-stagger > .lp-reveal:nth-child(3) { transition-delay: 0.2s; }
.lp-stagger > .lp-reveal:nth-child(4) { transition-delay: 0.3s; }

/* ---- Cards hover ---- */
.lp-card-hover {
    transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1),
                box-shadow 0.3s ease,
                border-color 0.3s ease;
}

.lp-card-hover:hover {
    transform: scale(1.02);
    box-shadow: 0 8px 30px rgba(26, 24, 22, 0.06);
    border-color: #C8102E33;
}

/* ---- Reduced motion ---- */
@media (prefers-reduced-motion: reduce) {
    .lp-hero-badge,
    .lp-hero-heading,
    .lp-hero-sub,
    .lp-hero-ctas,
    .lp-hero-preview,
    .lp-hero-stat-1,
    .lp-hero-stat-2,
    .lp-hero-stat-3 {
        animation: none;
        opacity: 1;
        transform: none;
    }

    .lp-reveal {
        opacity: 1;
        transform: none;
        transition: none;
    }

    .lp-card-hover:hover {
        transform: none;
    }
}

/* ---- Misc ---- */
.lp-gradient-line {
    background: linear-gradient(90deg, transparent, #C8102E33, transparent);
    height: 1px;
}

.lp-evidence-card {
    position: relative;
}

.lp-evidence-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 12px;
    bottom: 12px;
    width: 3px;
    border-radius: 3px;
    background: var(--lp-crimson);
    opacity: 0.6;
}

/* Float animation for preview stats */
.lp-float-slow {
    animation: lp-float 6s ease-in-out infinite;
}

.lp-float-mid {
    animation: lp-float 5s ease-in-out 1s infinite;
}

.lp-float-fast {
    animation: lp-float 4s ease-in-out 0.5s infinite;
}

/* Score bar fill */
.lp-score-bar {
    transition: width 1s cubic-bezier(0.22, 1, 0.36, 1);
}

/* Nav blur */
.lp-nav {
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}
`

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */
export default function LandingPage() {
    const navigate = useNavigate()
    const { isAuthenticated } = useAuth()
    const observerRef = useRef<IntersectionObserver | null>(null)

    // Redirect if authenticated
    useEffect(() => {
        if (isAuthenticated) {
            navigate('/dashboard', { replace: true })
        }
    }, [isAuthenticated, navigate])

    // Set page title
    useEffect(() => {
        document.title = 'Procurely — AI-Powered Vendor Discovery'
    }, [])

    // Intersection Observer for scroll reveals
    const setupObserver = useCallback(() => {
        if (observerRef.current) observerRef.current.disconnect()

        observerRef.current = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('lp-visible')
                        observerRef.current?.unobserve(entry.target)
                    }
                })
            },
            { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
        )

        document.querySelectorAll('.lp-reveal').forEach((el) => {
            observerRef.current?.observe(el)
        })
    }, [])

    useEffect(() => {
        // Small delay to ensure DOM is rendered
        const timer = setTimeout(setupObserver, 100)
        return () => {
            clearTimeout(timer)
            observerRef.current?.disconnect()
        }
    }, [setupObserver])

    const scrollToSection = (id: string) => {
        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
    }

    return (
        <div className="lp-root min-h-screen overflow-x-hidden" style={{ background: 'var(--lp-bg)' }}>
            {/* Inject styles */}
            <style dangerouslySetInnerHTML={{ __html: LANDING_STYLES }} />

            {/* ============================================================ */}
            {/*  NAVIGATION                                                  */}
            {/* ============================================================ */}
            <nav
                className="lp-nav fixed top-0 left-0 right-0 z-50 border-b"
                style={{
                    background: '#FAF9F7ee',
                    borderColor: 'var(--lp-border)',
                }}
            >
                <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link to="/" className="flex items-center gap-2.5 no-underline">
                        <div
                            className="w-8 h-8 rounded-lg flex items-center justify-center"
                            style={{ background: 'var(--lp-crimson)' }}
                        >
                            <Search className="w-4 h-4 text-white" />
                        </div>
                        <span
                            className="lp-serif text-xl font-semibold"
                            style={{ color: 'var(--lp-text-1)' }}
                        >
                            Procurely
                        </span>
                    </Link>
                    <div className="flex items-center gap-5">
                        <button
                            onClick={() => scrollToSection('how-it-works')}
                            className="hidden sm:block text-sm font-medium bg-transparent border-none cursor-pointer"
                            style={{ color: 'var(--lp-text-2)' }}
                            onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--lp-text-1)')}
                            onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--lp-text-2)')}
                        >
                            How it works
                        </button>
                        <button
                            onClick={() => scrollToSection('features')}
                            className="hidden sm:block text-sm font-medium bg-transparent border-none cursor-pointer"
                            style={{ color: 'var(--lp-text-2)' }}
                            onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--lp-text-1)')}
                            onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--lp-text-2)')}
                        >
                            Features
                        </button>
                        <button
                            onClick={() => scrollToSection('pricing')}
                            className="hidden sm:block text-sm font-medium bg-transparent border-none cursor-pointer"
                            style={{ color: 'var(--lp-text-2)' }}
                            onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--lp-text-1)')}
                            onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--lp-text-2)')}
                        >
                            Pricing
                        </button>
                        <Button
                            variant="outline"
                            asChild
                            className="rounded-lg border-[#ECE8E1] text-[#1A1816] hover:bg-[#F3F0EB]"
                        >
                            <Link to="/login">Sign in</Link>
                        </Button>
                    </div>
                </div>
            </nav>

            {/* ============================================================ */}
            {/*  HERO                                                        */}
            {/* ============================================================ */}
            <section className="relative pt-36 sm:pt-44 pb-8 px-6">
                <div className="max-w-5xl mx-auto text-center">
                    {/* Badge */}
                    <div className="lp-hero-badge mb-8">
                        <span
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium"
                            style={{
                                background: 'var(--lp-crimson-light)',
                                color: 'var(--lp-crimson)',
                            }}
                        >
                            <Zap className="w-3.5 h-3.5" />
                            AI-Powered Procurement
                        </span>
                    </div>

                    {/* Heading */}
                    <h1
                        className="lp-hero-heading lp-serif mb-6"
                        style={{
                            fontSize: 'clamp(2.5rem, 6vw, 4.5rem)',
                            fontWeight: 650,
                            lineHeight: 1.08,
                            color: 'var(--lp-text-1)',
                        }}
                    >
                        Find the right vendors,
                        <br />
                        <span style={{ color: 'var(--lp-crimson)' }}>faster</span>
                    </h1>

                    {/* Subtitle */}
                    <p
                        className="lp-hero-sub mx-auto mb-10"
                        style={{
                            fontSize: 'clamp(1.05rem, 2vw, 1.25rem)',
                            lineHeight: 1.7,
                            color: 'var(--lp-text-2)',
                            maxWidth: '560px',
                        }}
                    >
                        Procurely searches, scores, and compares vendors using AI — so you
                        can make confident decisions with evidence, not guesswork.
                    </p>

                    {/* CTAs */}
                    <div className="lp-hero-ctas flex flex-col sm:flex-row gap-4 justify-center mb-20">
                        <Button
                            size="lg"
                            asChild
                            className="text-base px-8 h-12 rounded-xl font-semibold shadow-none"
                            style={{
                                background: 'var(--lp-text-1)',
                                color: '#fff',
                            }}
                        >
                            <Link to="/login">
                                Get started
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Link>
                        </Button>
                        <Button
                            size="lg"
                            variant="outline"
                            className="text-base px-8 h-12 rounded-xl font-medium"
                            style={{
                                borderColor: 'var(--lp-border)',
                                color: 'var(--lp-text-1)',
                                background: 'transparent',
                            }}
                            onClick={() => scrollToSection('how-it-works')}
                        >
                            See how it works
                        </Button>
                    </div>
                </div>

                {/* App Preview Mockup */}
                <div className="max-w-5xl mx-auto relative">
                    <div
                        className="lp-hero-preview rounded-2xl border overflow-hidden"
                        style={{
                            background: 'var(--lp-card)',
                            borderColor: 'var(--lp-border)',
                            boxShadow: '0 20px 60px rgba(26, 24, 22, 0.08), 0 1px 3px rgba(26, 24, 22, 0.04)',
                        }}
                    >
                        {/* Window chrome */}
                        <div
                            className="flex items-center gap-2 px-5 py-3 border-b"
                            style={{ borderColor: 'var(--lp-border)', background: '#FDFDFC' }}
                        >
                            <div className="flex gap-1.5">
                                <div className="w-3 h-3 rounded-full" style={{ background: '#E8E4DD' }} />
                                <div className="w-3 h-3 rounded-full" style={{ background: '#E8E4DD' }} />
                                <div className="w-3 h-3 rounded-full" style={{ background: '#E8E4DD' }} />
                            </div>
                            <div
                                className="ml-4 flex-1 max-w-xs h-7 rounded-md flex items-center px-3 text-xs"
                                style={{ background: 'var(--lp-bg)', color: 'var(--lp-text-3)' }}
                            >
                                procurely.app/search/crm-solution
                            </div>
                        </div>

                        {/* Dashboard mockup content */}
                        <div className="p-6 sm:p-8">
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-3">
                                <div>
                                    <h3
                                        className="lp-serif text-lg font-semibold mb-1"
                                        style={{ color: 'var(--lp-text-1)' }}
                                    >
                                        Enterprise CRM Solution
                                    </h3>
                                    <p className="text-sm" style={{ color: 'var(--lp-text-3)' }}>
                                        12 vendors found &middot; Completed 2 min ago
                                    </p>
                                </div>
                                <span
                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold"
                                    style={{ background: '#ECFDF5', color: '#059669' }}
                                >
                                    <span
                                        className="w-1.5 h-1.5 rounded-full inline-block"
                                        style={{
                                            background: '#059669',
                                            animation: 'lp-pulse-dot 2s ease-in-out infinite',
                                        }}
                                    />
                                    Completed
                                </span>
                            </div>

                            {/* Vendor cards */}
                            <div className="grid sm:grid-cols-3 gap-4">
                                {[
                                    { name: 'Salesforce', score: 92, tag: 'Enterprise CRM', rank: 1 },
                                    { name: 'HubSpot', score: 88, tag: 'Marketing + CRM', rank: 2 },
                                    { name: 'Pipedrive', score: 84, tag: 'Sales CRM', rank: 3 },
                                ].map((v) => (
                                    <div
                                        key={v.name}
                                        className="p-4 rounded-xl border"
                                        style={{
                                            background: 'var(--lp-bg)',
                                            borderColor: 'var(--lp-border)',
                                        }}
                                    >
                                        <div className="flex items-center justify-between mb-3">
                                            <span
                                                className="text-xs font-medium"
                                                style={{ color: 'var(--lp-text-3)' }}
                                            >
                                                #{v.rank}
                                            </span>
                                            <span
                                                className="lp-serif text-xl font-bold"
                                                style={{ color: 'var(--lp-crimson)' }}
                                            >
                                                {v.score}
                                            </span>
                                        </div>
                                        <h4
                                            className="font-semibold text-sm mb-1"
                                            style={{ color: 'var(--lp-text-1)' }}
                                        >
                                            {v.name}
                                        </h4>
                                        <p className="text-xs" style={{ color: 'var(--lp-text-3)' }}>
                                            {v.tag}
                                        </p>
                                        {/* Score bar */}
                                        <div
                                            className="mt-3 h-1.5 rounded-full overflow-hidden"
                                            style={{ background: '#ECE8E1' }}
                                        >
                                            <div
                                                className="h-full rounded-full lp-score-bar"
                                                style={{
                                                    width: `${v.score}%`,
                                                    background: 'var(--lp-crimson)',
                                                    opacity: 0.7 + v.rank * 0.1,
                                                }}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Floating stats */}
                    <div
                        className="lp-hero-stat-1 lp-float-slow absolute -left-2 sm:left-[-40px] top-[30%] rounded-xl border px-4 py-3 hidden md:block"
                        style={{
                            background: 'var(--lp-card)',
                            borderColor: 'var(--lp-border)',
                            boxShadow: '0 8px 24px rgba(26, 24, 22, 0.06)',
                        }}
                    >
                        <p
                            className="lp-serif text-2xl font-bold"
                            style={{ color: 'var(--lp-crimson)' }}
                        >
                            12
                        </p>
                        <p className="text-xs font-medium" style={{ color: 'var(--lp-text-3)' }}>
                            Vendors found
                        </p>
                    </div>

                    <div
                        className="lp-hero-stat-2 lp-float-mid absolute -right-2 sm:right-[-40px] top-[20%] rounded-xl border px-4 py-3 hidden md:block"
                        style={{
                            background: 'var(--lp-card)',
                            borderColor: 'var(--lp-border)',
                            boxShadow: '0 8px 24px rgba(26, 24, 22, 0.06)',
                        }}
                    >
                        <p
                            className="lp-serif text-2xl font-bold"
                            style={{ color: 'var(--lp-crimson)' }}
                        >
                            48
                        </p>
                        <p className="text-xs font-medium" style={{ color: 'var(--lp-text-3)' }}>
                            Sources analyzed
                        </p>
                    </div>

                    <div
                        className="lp-hero-stat-3 lp-float-fast absolute right-[10%] sm:right-[60px] -bottom-6 rounded-xl border px-4 py-3 hidden md:block"
                        style={{
                            background: 'var(--lp-card)',
                            borderColor: 'var(--lp-border)',
                            boxShadow: '0 8px 24px rgba(26, 24, 22, 0.06)',
                        }}
                    >
                        <p
                            className="lp-serif text-2xl font-bold"
                            style={{ color: 'var(--lp-crimson)' }}
                        >
                            86
                        </p>
                        <p className="text-xs font-medium" style={{ color: 'var(--lp-text-3)' }}>
                            Avg. score
                        </p>
                    </div>
                </div>
            </section>

            {/* Gradient divider */}
            <div className="max-w-4xl mx-auto my-16 px-6">
                <div className="lp-gradient-line" />
            </div>

            {/* ============================================================ */}
            {/*  HOW IT WORKS                                                */}
            {/* ============================================================ */}
            <section
                id="how-it-works"
                className="py-20 sm:py-28 px-6"
                style={{ background: 'var(--lp-card)' }}
            >
                <div className="max-w-5xl mx-auto">
                    {/* Section header */}
                    <div className="text-center mb-16 lp-reveal">
                        <p
                            className="text-xs font-semibold tracking-[0.15em] uppercase mb-4"
                            style={{ color: 'var(--lp-crimson)' }}
                        >
                            How it works
                        </p>
                        <h2
                            className="lp-serif mb-4"
                            style={{
                                fontSize: 'clamp(1.75rem, 4vw, 2.5rem)',
                                fontWeight: 600,
                                color: 'var(--lp-text-1)',
                            }}
                        >
                            From requirements to recommendations
                        </h2>
                        <p
                            className="mx-auto"
                            style={{
                                maxWidth: '480px',
                                color: 'var(--lp-text-2)',
                                fontSize: '1.05rem',
                                lineHeight: 1.7,
                            }}
                        >
                            Four steps. Minutes, not weeks. Let AI handle the research while
                            you focus on the decision.
                        </p>
                    </div>

                    {/* Steps */}
                    <div className="grid md:grid-cols-4 gap-6 lp-stagger">
                        {[
                            {
                                step: '01',
                                icon: FileText,
                                title: 'Define your needs',
                                desc: 'Enter your requirements, budget range, and must-have criteria for the perfect vendor match.',
                            },
                            {
                                step: '02',
                                icon: Search,
                                title: 'AI searches & scores',
                                desc: 'We crawl the web, extract evidence, and score every vendor against your specific criteria.',
                            },
                            {
                                step: '03',
                                icon: Scale,
                                title: 'Compare & shortlist',
                                desc: 'Side-by-side comparisons with real citations and evidence. No guesswork involved.',
                            },
                            {
                                step: '04',
                                icon: BarChart3,
                                title: 'Export & decide',
                                desc: 'Generate polished reports, share with stakeholders, and take action with confidence.',
                            },
                        ].map((item) => (
                            <div
                                key={item.step}
                                className="lp-reveal lp-card-hover rounded-2xl border p-6"
                                style={{
                                    background: 'var(--lp-bg)',
                                    borderColor: 'var(--lp-border)',
                                }}
                            >
                                <span
                                    className="lp-serif block text-4xl font-light mb-5"
                                    style={{ color: '#E8E4DD' }}
                                >
                                    {item.step}
                                </span>
                                <div
                                    className="w-10 h-10 rounded-xl flex items-center justify-center mb-4"
                                    style={{ background: 'var(--lp-crimson-light)' }}
                                >
                                    <item.icon
                                        className="w-5 h-5"
                                        style={{ color: 'var(--lp-crimson)' }}
                                    />
                                </div>
                                <h3
                                    className="lp-serif font-semibold text-lg mb-2"
                                    style={{ color: 'var(--lp-text-1)' }}
                                >
                                    {item.title}
                                </h3>
                                <p
                                    className="text-sm leading-relaxed"
                                    style={{ color: 'var(--lp-text-2)' }}
                                >
                                    {item.desc}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ============================================================ */}
            {/*  FEATURES                                                    */}
            {/* ============================================================ */}
            <section id="features" className="py-20 sm:py-28 px-6" style={{ background: 'var(--lp-bg)' }}>
                <div className="max-w-5xl mx-auto">
                    {/* Section header */}
                    <div className="text-center mb-16 lp-reveal">
                        <p
                            className="text-xs font-semibold tracking-[0.15em] uppercase mb-4"
                            style={{ color: 'var(--lp-crimson)' }}
                        >
                            Features
                        </p>
                        <h2
                            className="lp-serif mb-4"
                            style={{
                                fontSize: 'clamp(1.75rem, 4vw, 2.5rem)',
                                fontWeight: 600,
                                color: 'var(--lp-text-1)',
                            }}
                        >
                            Everything you need to decide
                        </h2>
                        <p
                            className="mx-auto"
                            style={{
                                maxWidth: '480px',
                                color: 'var(--lp-text-2)',
                                fontSize: '1.05rem',
                                lineHeight: 1.7,
                            }}
                        >
                            A complete toolkit for evidence-based vendor selection,
                            built for modern procurement teams.
                        </p>
                    </div>

                    {/* Feature cards */}
                    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 lp-stagger">
                        {[
                            {
                                icon: Star,
                                title: 'Shortlists',
                                desc: 'Organize vendor candidates, add notes, and reorder by preference with drag-and-drop.',
                            },
                            {
                                icon: Layers,
                                title: 'Compare',
                                desc: 'Side-by-side matrix with highlighted best scores across every evaluation criterion.',
                            },
                            {
                                icon: FileText,
                                title: 'Reports',
                                desc: 'Export polished, stakeholder-ready reports with full evidence citations and scoring.',
                            },
                            {
                                icon: MessageSquare,
                                title: 'AI Assistant',
                                desc: 'Ask questions, get vendor insights, and take action — all within a single conversation.',
                            },
                        ].map((feat) => (
                            <div
                                key={feat.title}
                                className="lp-reveal lp-card-hover rounded-2xl border p-6 text-center"
                                style={{
                                    background: 'var(--lp-card)',
                                    borderColor: 'var(--lp-border)',
                                }}
                            >
                                <div
                                    className="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-5"
                                    style={{ background: 'var(--lp-bg)' }}
                                >
                                    <feat.icon
                                        className="w-5 h-5"
                                        style={{ color: 'var(--lp-text-2)' }}
                                    />
                                </div>
                                <h3
                                    className="lp-serif font-semibold text-base mb-2"
                                    style={{ color: 'var(--lp-text-1)' }}
                                >
                                    {feat.title}
                                </h3>
                                <p
                                    className="text-sm leading-relaxed"
                                    style={{ color: 'var(--lp-text-2)' }}
                                >
                                    {feat.desc}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ============================================================ */}
            {/*  EVIDENCE SECTION                                            */}
            {/* ============================================================ */}
            <section className="py-20 sm:py-28 px-6" style={{ background: 'var(--lp-card)' }}>
                <div className="max-w-5xl mx-auto">
                    <div className="grid md:grid-cols-2 gap-12 lg:gap-20 items-center">
                        {/* Left: copy */}
                        <div className="lp-reveal">
                            <p
                                className="text-xs font-semibold tracking-[0.15em] uppercase mb-4"
                                style={{ color: 'var(--lp-crimson)' }}
                            >
                                Transparency
                            </p>
                            <h2
                                className="lp-serif mb-5"
                                style={{
                                    fontSize: 'clamp(1.75rem, 4vw, 2.5rem)',
                                    fontWeight: 600,
                                    color: 'var(--lp-text-1)',
                                    lineHeight: 1.2,
                                }}
                            >
                                Evidence-first
                                <br />
                                decisions
                            </h2>
                            <p
                                className="mb-8"
                                style={{
                                    color: 'var(--lp-text-2)',
                                    fontSize: '1.05rem',
                                    lineHeight: 1.7,
                                }}
                            >
                                Every score is backed by real citations from vendor websites,
                                analyst reviews, and documentation. No black boxes, no
                                hidden algorithms.
                            </p>
                            <ul className="space-y-4">
                                {[
                                    'Extracted pricing quotes with source links',
                                    'Feature claims verified from official docs',
                                    'Trust signals from reviews and case studies',
                                ].map((item) => (
                                    <li key={item} className="flex items-start gap-3">
                                        <CheckCircle2
                                            className="w-5 h-5 mt-0.5 flex-shrink-0"
                                            style={{ color: 'var(--lp-crimson)' }}
                                        />
                                        <span
                                            className="text-sm font-medium"
                                            style={{ color: 'var(--lp-text-1)' }}
                                        >
                                            {item}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* Right: evidence examples */}
                        <div className="lp-reveal space-y-4">
                            {[
                                {
                                    quote: '"Pricing starts at $25/user/month for the Professional tier, with enterprise pricing available on request. Volume discounts apply for 100+ seats."',
                                    source: 'vendor-pricing.com/enterprise',
                                    label: 'Pricing',
                                },
                                {
                                    quote: '"SOC 2 Type II certified, GDPR compliant with data residency options in EU, US, and APAC regions. Annual penetration testing by third party."',
                                    source: 'trustpage.com/compliance',
                                    label: 'Compliance',
                                },
                                {
                                    quote: '"4.6/5 average rating across 2,847 reviews. Customers highlight ease of onboarding and responsive support team."',
                                    source: 'g2.com/products/reviews',
                                    label: 'Reviews',
                                },
                            ].map((ev, i) => (
                                <div
                                    key={i}
                                    className="lp-evidence-card rounded-xl border p-5 pl-7"
                                    style={{
                                        background: 'var(--lp-bg)',
                                        borderColor: 'var(--lp-border)',
                                    }}
                                >
                                    <span
                                        className="inline-block text-[10px] font-semibold tracking-[0.12em] uppercase px-2 py-0.5 rounded mb-3"
                                        style={{
                                            background: 'var(--lp-crimson-light)',
                                            color: 'var(--lp-crimson)',
                                        }}
                                    >
                                        {ev.label}
                                    </span>
                                    <p
                                        className="text-sm italic leading-relaxed mb-3"
                                        style={{ color: 'var(--lp-text-2)' }}
                                    >
                                        {ev.quote}
                                    </p>
                                    <span
                                        className="text-xs font-medium"
                                        style={{ color: 'var(--lp-crimson)' }}
                                    >
                                        {ev.source}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* ============================================================ */}
            {/*  TRUST / ABOUT                                               */}
            {/* ============================================================ */}
            <section className="py-20 sm:py-28 px-6" style={{ background: 'var(--lp-bg)' }}>
                <div className="max-w-5xl mx-auto">
                    {/* Section header */}
                    <div className="text-center mb-16 lp-reveal">
                        <p
                            className="text-xs font-semibold tracking-[0.15em] uppercase mb-4"
                            style={{ color: 'var(--lp-crimson)' }}
                        >
                            Trusted platform
                        </p>
                        <h2
                            className="lp-serif mb-5"
                            style={{
                                fontSize: 'clamp(1.75rem, 4vw, 2.5rem)',
                                fontWeight: 600,
                                color: 'var(--lp-text-1)',
                            }}
                        >
                            Built for procurement teams
                        </h2>
                        <p
                            className="mx-auto"
                            style={{
                                maxWidth: '540px',
                                color: 'var(--lp-text-2)',
                                fontSize: '1.05rem',
                                lineHeight: 1.7,
                            }}
                        >
                            Procurely combines AI-driven research with structured evaluation
                            frameworks, so your team can stop Googling and start deciding.
                        </p>
                    </div>

                    {/* Metrics */}
                    <div className="grid sm:grid-cols-3 gap-6 lp-stagger">
                        {[
                            {
                                icon: Globe,
                                value: 'Multi-source',
                                label: 'Search engine',
                                desc: 'Searches across Serper, Tavily, and Firecrawl simultaneously.',
                            },
                            {
                                icon: Users,
                                value: 'Indonesia-focused',
                                label: 'Vendor discovery',
                                desc: 'Optimized for Indonesian vendors with local marketplace integration.',
                            },
                            {
                                icon: Shield,
                                value: 'Evidence-backed',
                                label: 'Scoring system',
                                desc: 'Every vendor score includes source citations and confidence ratings.',
                            },
                        ].map((m) => (
                            <div
                                key={m.label}
                                className="lp-reveal lp-card-hover rounded-2xl border p-8 text-center"
                                style={{
                                    background: 'var(--lp-card)',
                                    borderColor: 'var(--lp-border)',
                                }}
                            >
                                <div
                                    className="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-5"
                                    style={{ background: 'var(--lp-crimson-light)' }}
                                >
                                    <m.icon
                                        className="w-5 h-5"
                                        style={{ color: 'var(--lp-crimson)' }}
                                    />
                                </div>
                                <p
                                    className="lp-serif text-xl sm:text-2xl font-bold mb-1"
                                    style={{ color: 'var(--lp-text-1)' }}
                                >
                                    {m.value}
                                </p>
                                <p
                                    className="text-sm font-semibold mb-2"
                                    style={{ color: 'var(--lp-text-1)' }}
                                >
                                    {m.label}
                                </p>
                                <p
                                    className="text-sm"
                                    style={{ color: 'var(--lp-text-2)' }}
                                >
                                    {m.desc}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ============================================================ */}
            {/*  CTA                                                         */}
            {/* ============================================================ */}
            <section className="py-20 sm:py-28 px-6" style={{ background: 'var(--lp-card)' }}>
                <div className="max-w-3xl mx-auto text-center lp-reveal">
                    <h2
                        className="lp-serif mb-5"
                        style={{
                            fontSize: 'clamp(1.75rem, 4vw, 2.5rem)',
                            fontWeight: 600,
                            color: 'var(--lp-text-1)',
                        }}
                    >
                        Ready to find better vendors?
                    </h2>
                    <p
                        className="mx-auto mb-10"
                        style={{
                            maxWidth: '460px',
                            color: 'var(--lp-text-2)',
                            fontSize: '1.05rem',
                            lineHeight: 1.7,
                        }}
                    >
                        Join procurement teams who make vendor decisions backed by
                        evidence, not guesswork. Start searching in under a minute.
                    </p>
                    <Button
                        size="lg"
                        asChild
                        className="text-base px-10 h-12 rounded-xl font-semibold shadow-none"
                        style={{ background: 'var(--lp-text-1)', color: '#fff' }}
                    >
                        <Link to="/login">
                            Start now — it's free
                            <ArrowRight className="ml-2 h-4 w-4" />
                        </Link>
                    </Button>
                </div>
            </section>

            {/* ============================================================ */}
            {/*  PRICING                                                     */}
            {/* ============================================================ */}
            <section id="pricing" className="py-20 sm:py-28 px-6" style={{ background: 'var(--lp-bg)' }}>
                <div className="max-w-4xl mx-auto">
                    {/* Section header */}
                    <div className="text-center mb-16 lp-reveal">
                        <p
                            className="text-xs font-semibold tracking-[0.15em] uppercase mb-4"
                            style={{ color: 'var(--lp-crimson)' }}
                        >
                            Pricing
                        </p>
                        <h2
                            className="lp-serif mb-4"
                            style={{
                                fontSize: 'clamp(1.75rem, 4vw, 2.5rem)',
                                fontWeight: 600,
                                color: 'var(--lp-text-1)',
                            }}
                        >
                            Simple, transparent pricing
                        </h2>
                        <p
                            className="mx-auto"
                            style={{
                                maxWidth: '480px',
                                color: 'var(--lp-text-2)',
                                fontSize: '1.05rem',
                                lineHeight: 1.7,
                            }}
                        >
                            Start with a free search to see the quality of results. Upgrade when you need more.
                        </p>
                    </div>

                    {/* Pricing cards */}
                    <div className="grid sm:grid-cols-2 gap-6 lp-stagger">
                        {/* Free tier */}
                        <div
                            className="lp-reveal lp-card-hover rounded-2xl border p-8"
                            style={{
                                background: 'var(--lp-card)',
                                borderColor: 'var(--lp-border)',
                            }}
                        >
                            <p
                                className="text-xs font-semibold tracking-[0.12em] uppercase mb-2"
                                style={{ color: 'var(--lp-text-3)' }}
                            >
                                Free
                            </p>
                            <h3
                                className="lp-serif text-2xl font-bold mb-2"
                                style={{ color: 'var(--lp-text-1)' }}
                            >
                                Try it once
                            </h3>
                            <p
                                className="text-sm mb-6"
                                style={{ color: 'var(--lp-text-2)', lineHeight: 1.7 }}
                            >
                                One full vendor search with complete results and evidence citations.
                            </p>
                            <ul className="space-y-3 mb-8">
                                {[
                                    '1 vendor search',
                                    'Full scored results',
                                    'Evidence citations',
                                ].map((item) => (
                                    <li key={item} className="flex items-center gap-2.5">
                                        <CheckCircle2
                                            className="w-4 h-4 flex-shrink-0"
                                            style={{ color: 'var(--lp-crimson)' }}
                                        />
                                        <span className="text-sm" style={{ color: 'var(--lp-text-1)' }}>
                                            {item}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                            <Button
                                size="lg"
                                asChild
                                className="w-full rounded-xl font-semibold"
                                style={{
                                    borderColor: 'var(--lp-border)',
                                    color: 'var(--lp-text-1)',
                                    background: 'transparent',
                                    border: '1px solid var(--lp-border)',
                                }}
                            >
                                <Link to="/login">Get started</Link>
                            </Button>
                        </div>

                        {/* Pro tier */}
                        <div
                            className="lp-reveal lp-card-hover rounded-2xl border p-8 relative"
                            style={{
                                background: 'var(--lp-card)',
                                borderColor: 'var(--lp-crimson)',
                                borderWidth: '2px',
                            }}
                        >
                            <span
                                className="absolute -top-3 left-6 inline-block text-[10px] font-semibold tracking-[0.12em] uppercase px-3 py-1 rounded-full"
                                style={{
                                    background: 'var(--lp-crimson)',
                                    color: '#fff',
                                }}
                            >
                                Recommended
                            </span>
                            <p
                                className="text-xs font-semibold tracking-[0.12em] uppercase mb-2"
                                style={{ color: 'var(--lp-crimson)' }}
                            >
                                Pro
                            </p>
                            <h3
                                className="lp-serif text-2xl font-bold mb-2"
                                style={{ color: 'var(--lp-text-1)' }}
                            >
                                For procurement teams
                            </h3>
                            <p
                                className="text-sm mb-6"
                                style={{ color: 'var(--lp-text-2)', lineHeight: 1.7 }}
                            >
                                Unlimited searches with priority support and custom reporting.
                            </p>
                            <ul className="space-y-3 mb-8">
                                {[
                                    'Unlimited vendor searches',
                                    'Priority support',
                                    'Custom reports',
                                    'Team collaboration',
                                ].map((item) => (
                                    <li key={item} className="flex items-center gap-2.5">
                                        <CheckCircle2
                                            className="w-4 h-4 flex-shrink-0"
                                            style={{ color: 'var(--lp-crimson)' }}
                                        />
                                        <span className="text-sm" style={{ color: 'var(--lp-text-1)' }}>
                                            {item}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                            <Button
                                size="lg"
                                asChild
                                className="w-full rounded-xl font-semibold shadow-none"
                                style={{ background: 'var(--lp-text-1)', color: '#fff' }}
                            >
                                <a href="mailto:faizal2jz@gmail.com">Contact us</a>
                            </Button>
                        </div>
                    </div>
                </div>
            </section>

            {/* ============================================================ */}
            {/*  FOOTER                                                      */}
            {/* ============================================================ */}
            <footer
                className="py-8 px-6 border-t"
                style={{ borderColor: 'var(--lp-border)', background: 'var(--lp-bg)' }}
            >
                <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-2.5">
                        <div
                            className="w-6 h-6 rounded flex items-center justify-center"
                            style={{ background: 'var(--lp-crimson)' }}
                        >
                            <Search className="w-3 h-3 text-white" />
                        </div>
                        <span
                            className="lp-serif text-sm font-semibold"
                            style={{ color: 'var(--lp-text-1)' }}
                        >
                            Procurely
                        </span>
                    </div>
                    <p className="text-sm" style={{ color: 'var(--lp-text-3)' }}>
                        &copy; 2026 Procurely. AI-powered vendor discovery.
                    </p>
                </div>
            </footer>
        </div>
    )
}
