/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        sky: {
          50: 'var(--color-sky-50)',
          100: 'var(--color-sky-100)',
          300: 'var(--color-sky-300)',
          500: 'var(--color-sky-500)',
          700: 'var(--color-sky-700)',
        },
        ink: {
          900: 'var(--color-ink-900)',
          600: 'var(--color-ink-600)',
        },
        mist: 'var(--color-mist)',
        aqua: 'var(--color-aqua)',
        leaf: 'var(--color-leaf)',
        amber: 'var(--color-amber)',
        coral: 'var(--color-coral)',
        background: 'var(--color-background)',
      },
      fontFamily: {
        sans: ['Onest', 'sans-serif'],
        tamil: ['"Anek Tamil"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        'card': '22px',
        'btn': '12px',
        'pill': '999px',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(58, 143, 218, 0.08)',
        'glass-hover': '0 12px 40px 0 rgba(58, 143, 218, 0.14)',
        'glass-dark': '0 8px 32px 0 rgba(0, 0, 0, 0.35)',
      },
      backdropBlur: {
        'glass': '18px',
      }
    },
  },
  plugins: [],
};
