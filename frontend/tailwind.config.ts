import type { Config } from 'tailwindcss'

const config: Config = {
    content: [
        './index.html',
        './src/**/*.{js,ts,jsx,tsx}',
    ],
    theme: {
        container: {
            center: true,
            padding: '2rem',
            screens: {
                '2xl': '1400px',
            },
        },
        extend: {
            colors: {
                // === Brand Palette (Editorial Luxury) ===
                crimson: {
                    DEFAULT: 'hsl(var(--crimson))',
                    50: '#fef2f3',
                    100: '#fde3e6',
                    200: '#fcccd3',
                    300: '#f9a3af',
                    400: '#f4707f',
                    500: '#e84457',
                    600: '#C8102E',  // Primary crimson
                    700: '#aa0e27',
                    800: '#8d1025',
                    900: '#781224',
                    950: '#42040e',
                },
                rose: {
                    DEFAULT: 'hsl(var(--rose))',
                },
                blush: {
                    DEFAULT: 'hsl(var(--blush))',
                },
                cream: {
                    DEFAULT: 'hsl(var(--cream))',
                },
                // Semantic colors
                border: 'hsl(var(--border))',
                input: 'hsl(var(--input))',
                ring: 'hsl(var(--ring))',
                background: 'hsl(var(--background))',
                foreground: 'hsl(var(--foreground))',
                primary: {
                    DEFAULT: 'hsl(var(--primary))',
                    foreground: 'hsl(var(--primary-foreground))',
                },
                secondary: {
                    DEFAULT: 'hsl(var(--secondary))',
                    foreground: 'hsl(var(--secondary-foreground))',
                },
                destructive: {
                    DEFAULT: 'hsl(var(--destructive))',
                    foreground: 'hsl(var(--destructive-foreground))',
                },
                muted: {
                    DEFAULT: 'hsl(var(--muted))',
                    foreground: 'hsl(var(--muted-foreground))',
                },
                accent: {
                    DEFAULT: 'hsl(var(--accent))',
                    foreground: 'hsl(var(--accent-foreground))',
                },
                popover: {
                    DEFAULT: 'hsl(var(--popover))',
                    foreground: 'hsl(var(--popover-foreground))',
                },
                card: {
                    DEFAULT: 'hsl(var(--card))',
                    foreground: 'hsl(var(--card-foreground))',
                },
                // Score colors
                score: {
                    high: '#22c55e',
                    medium: '#eab308',
                    low: '#ef4444',
                },
            },
            borderRadius: {
                lg: 'var(--radius)',
                md: 'calc(var(--radius) - 2px)',
                sm: 'calc(var(--radius) - 4px)',
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                display: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
                body: ['Inter', 'system-ui', 'sans-serif'],
            },
            fontSize: {
                'display-xl': ['4rem', { lineHeight: '1.05', fontWeight: '500', letterSpacing: '-0.02em' }],
                'display-lg': ['3rem', { lineHeight: '1.1', fontWeight: '500', letterSpacing: '-0.02em' }],
                'display': ['2.25rem', { lineHeight: '1.2', fontWeight: '500', letterSpacing: '-0.01em' }],
                'heading': ['1.5rem', { lineHeight: '1.3', fontWeight: '600' }],
                'subheading': ['1.125rem', { lineHeight: '1.4', fontWeight: '600' }],
            },
            keyframes: {
                'accordion-down': {
                    from: { height: '0' },
                    to: { height: 'var(--radix-accordion-content-height)' },
                },
                'accordion-up': {
                    from: { height: 'var(--radix-accordion-content-height)' },
                    to: { height: '0' },
                },
                'fade-in': {
                    from: { opacity: '0' },
                    to: { opacity: '1' },
                },
                'fade-in-up': {
                    from: { opacity: '0', transform: 'translateY(20px)' },
                    to: { opacity: '1', transform: 'translateY(0)' },
                },
                'slide-in-right': {
                    from: { transform: 'translateX(100%)' },
                    to: { transform: 'translateX(0)' },
                },
                'slide-in-bottom': {
                    from: { transform: 'translateY(100%)', opacity: '0' },
                    to: { transform: 'translateY(0)', opacity: '1' },
                },
                'scale-in': {
                    from: { transform: 'scale(0.95)', opacity: '0' },
                    to: { transform: 'scale(1)', opacity: '1' },
                },
            },
            animation: {
                'accordion-down': 'accordion-down 0.2s ease-out',
                'accordion-up': 'accordion-up 0.2s ease-out',
                'fade-in': 'fade-in 0.3s ease-out',
                'fade-in-up': 'fade-in-up 0.4s ease-out',
                'slide-in-right': 'slide-in-right 0.3s ease-out',
                'slide-in-bottom': 'slide-in-bottom 0.3s ease-out',
                'scale-in': 'scale-in 0.2s ease-out',
            },
            boxShadow: {
                'editorial': '0 1px 2px rgba(0, 0, 0, 0.03)',
                'editorial-hover': '0 2px 8px rgba(0, 0, 0, 0.06)',
                'glow-crimson': '0 0 20px hsl(354 84% 43% / 0.15)',
                'card': '0 1px 2px rgba(0, 0, 0, 0.03)',
                'card-hover': '0 4px 12px rgba(0, 0, 0, 0.06)',
            },
            backgroundImage: {
                'grain': "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E\")",
            },
        },
    },
    plugins: [require('tailwindcss-animate')],
}

export default config
