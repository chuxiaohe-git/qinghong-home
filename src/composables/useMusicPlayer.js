// 音乐播放器共享状态，供 DashMusic 和 DashLyric 共用
import { ref } from 'vue'

export const audioEl = ref(null)
export const playlist = ref([])
export const currentIndex = ref(-1)
export const playing = ref(false)
export const progressPct = ref(0)
export const currentTime = ref(0)
export const duration = ref(0)
export const currentSong = ref(null)
export const lyrics = ref([])      // [{time: 0, text: '歌词'}]
export const volume = ref(parseFloat(localStorage.getItem('music_volume') || '0.7'))

export function setLyrics(lines) {
  lyrics.value = lines.map(l => {
    const m = l.match(/\[(\d+):(\d+\.?\d*)\](.*)/)
    if (m) return { time: parseInt(m[1]) * 60 + parseFloat(m[2]), text: m[3].trim() }
    return { time: 0, text: '' }
  }).filter(l => l.text)
}
