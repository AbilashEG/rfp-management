import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        beige: {
          50:  '#FAF8F4',
          100: '#F5F1E8',
          200: '#EDE8DC',
          300: '#E0D8C8',
          400: '#D4CBB8',
          500: '#C4B89E',
        },
        warm: {
          text:    '#2C2C2C',
          muted:   '#7A7265',
          border:  '#D4CBB8',
        },
        orange: {
          DEFAULT: '#E8A020',
          hover:   '#C97B1A',
          light:   '#FDF3E0',
        },
        success: '#5C8A4A',
        danger:  '#A63D2F',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'spin-slow': 'spin 2s linear infinite',
        'pulse-soft': 'pulse 3s ease-in-out infinite',
      },
      boxShadow: {
        'warm-sm': '0 1px 8px rgba(120,100,70,0.06)',
        'warm':    '0 4px 24px rgba(120,100,70,0.10)',
        'warm-lg': '0 8px 40px rgba(120,100,70,0.14)',
      },
    },
  },
  plugins: [],
}

export default config
