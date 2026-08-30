/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Inter"', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        luna: {
          orange: '#9146ff', // Twitch Signature Purple
          orangeDark: '#772ce8',
          orangeLight: '#bf94ff',
          topbar: '#18181b', // Twitch Dark Topbar
          sidebar: '#1f1f23', // Twitch Dark Sidebar
          canvas: '#0e0e10', // Twitch Canvas
          card: '#18181b', // Twitch Card Surface
          cardBorder: '#2f2f35', // Twitch Border
          cardBorderHover: '#464649',
          tableHover: '#26262c',
          textMuted: '#adadb8',
          textSubtle: '#848494',
          textLight: '#efeff1',
        },
        twitch: {
          purple: '#9146ff',
          purpleDark: '#772ce8',
          purpleLight: '#bf94ff',
          red: '#eb0400',
          darkCanvas: '#0e0e10',
          darkCard: '#18181b',
          darkSidebar: '#1f1f23',
          darkBorder: '#2f2f35',
        },
        verdict: {
          passed: '#00f59b',
          flagged: '#eb0400',
          escalated: '#9146ff',
        }
      },
      borderRadius: {
        DEFAULT: '4px',
        sm: '2px',
        md: '6px',
        lg: '8px',
      }
    },
  },
  plugins: [],
}
