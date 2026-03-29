/**
 * Procurely Design Tokens
 * Brand identity, typography, and spacing system
 */

export const designTokens = {
    // Brand Colors
    colors: {
        brand: {
            primary: '#0c86ef',
            secondary: '#006acc',
            accent: '#36a5ff',
        },
        // Semantic
        success: '#22c55e',
        warning: '#eab308',
        error: '#ef4444',
        info: '#0ea5e9',
        // Scores
        score: {
            high: '#22c55e',
            medium: '#eab308',
            low: '#ef4444',
        },
    },

    // Typography Scale
    typography: {
        fontFamily: {
            sans: 'Inter, system-ui, sans-serif',
            display: 'Inter, system-ui, sans-serif',
        },
        fontSize: {
            'display-lg': '3rem',     // 48px - Hero headings
            'display': '2.25rem',     // 36px - Page titles
            'heading': '1.5rem',      // 24px - Section headings
            'subheading': '1.125rem', // 18px - Card titles
            'body': '1rem',           // 16px - Body text
            'caption': '0.875rem',    // 14px - Labels, captions
            'small': '0.75rem',       // 12px - Small text
        },
        fontWeight: {
            normal: 400,
            medium: 500,
            semibold: 600,
            bold: 700,
        },
    },

    // Spacing Scale (in rem)
    spacing: {
        0: '0',
        1: '0.25rem',   // 4px
        2: '0.5rem',    // 8px
        3: '0.75rem',   // 12px
        4: '1rem',      // 16px
        5: '1.25rem',   // 20px
        6: '1.5rem',    // 24px
        8: '2rem',      // 32px
        10: '2.5rem',   // 40px
        12: '3rem',     // 48px
        16: '4rem',     // 64px
    },

    // Border Radius
    radius: {
        none: '0',
        sm: '0.25rem',  // 4px
        md: '0.5rem',   // 8px
        lg: '0.75rem',  // 12px
        xl: '1rem',     // 16px
        '2xl': '1.25rem', // 20px
        '3xl': '1.5rem',  // 24px
        full: '9999px',
    },

    // Shadows
    shadows: {
        card: '0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06)',
        cardHover: '0 10px 40px rgba(0, 0, 0, 0.12)',
        glow: '0 0 20px rgba(12, 134, 239, 0.15)',
    },

    // Z-Index Scale
    zIndex: {
        dropdown: 50,
        modal: 100,
        toast: 150,
        tooltip: 200,
    },

    // Transitions
    transitions: {
        fast: '150ms ease',
        normal: '200ms ease',
        slow: '300ms ease',
    },
} as const

export type DesignTokens = typeof designTokens
