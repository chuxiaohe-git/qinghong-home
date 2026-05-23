// ── 便签卡片颜色（10 色，TodoPanel / ScratchNote / CalendarView 共享） ──

export const NOTE_COLORS = [
  '#FF6B6B','#FDCB6E','#A29BFE','#2ECC71','#4ECDC4',
  '#FF9FF3','#74B9FF','#FAB1A0','#DDA0DD','#FFEAA7',
]

// 带文字色的样式配置（浅色文字色 vs 深色文字色）
function isLightColor(hex) {
  const c = parseInt(hex.slice(1), 16)
  const r = (c >> 16) & 0xFF
  const g = (c >> 8) & 0xFF
  const b = c & 0xFF
  return (r * 299 + g * 587 + b * 114) / 1000 > 180
}

export const NOTE_STYLES = NOTE_COLORS.map(bg => ({
  bg,
  text: isLightColor(bg) ? '#2d3436' : '#fff',
}))

// 深色模式配色（降低亮度+饱和度）
export const NOTE_STYLES_DARK = [
  { bg: '#8B3A3A', text: '#fff' },
  { bg: '#8B7D3A', text: '#2d3436' },
  { bg: '#6B66A8', text: '#fff' },
  { bg: '#2A8B4A', text: '#fff' },
  { bg: '#368B85', text: '#fff' },
  { bg: '#A86BA0', text: '#2d3436' },
  { bg: '#4E7BA8', text: '#fff' },
  { bg: '#A87368', text: '#2d3436' },
  { bg: '#8B6B8B', text: '#fff' },
  { bg: '#A89B6B', text: '#2d3436' },
]

// 浅色→深色映射表
export const LIGHT_TO_DARK = new Map()
NOTE_STYLES.forEach((s, i) => LIGHT_TO_DARK.set(s.bg, NOTE_STYLES_DARK[i]))

// 随机取色
export function randomColor() {
  return NOTE_COLORS[Math.floor(Math.random() * NOTE_COLORS.length)]
}
