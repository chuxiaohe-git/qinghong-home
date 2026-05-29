<template>
  <div class="music-card" @click.stop>
    <audio ref="audioRef" @ended="nextSong" @error="onError" @timeupdate="onTime" @loadedmetadata="onMeta" @canplay="onCanplay"></audio>

    <div class="music-top">
      <div class="music-info">
        <span class="music-note" :class="{ 'is-playing': playing }">♫</span>
        <span class="music-title" v-if="currentSong">{{ currentSong.title }}</span>
        <span class="music-title artist" v-if="currentSong"> — {{ currentSong.author }}</span>
        <span class="music-placeholder" v-else>搜索歌曲开始播放</span>
      </div>
    </div>

    <div class="eq-wrap" ref="eqWrapRef" @click="seekFromEq">
      <canvas ref="eqCanvas" class="eq-canvas" width="240" height="60"></canvas>
      <div class="eq-time">
        <span class="time-label">{{ fmtTime(currentTime) }}</span>
        <div class="eq-seek-track" ref="eqSeekRef">
          <div class="eq-seek-fill" :style="{ width: progressPct + '%' }"></div>
        </div>
        <span class="time-label">{{ fmtTime(duration) }}</span>
      </div>
    </div>

    <div class="music-controls">
      <button class="mc-btn" @click.stop="prevSong" title="上一首">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h2v12H6zm3.5 6 8.5 6V6z"/></svg>
      </button>
      <button class="mc-btn mc-play" @click.stop="togglePlay" title="播放/暂停">
        <svg v-if="!playing" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        <svg v-else viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
      </button>
      <button class="mc-btn" @click.stop="nextSong" title="下一首">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>
      </button>
      <button class="mc-btn mc-list-btn" @click.stop="toggleList" title="播放列表">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
        <span class="list-count" v-if="playlist.length">{{ playlist.length }}</span>
      </button>
      <button class="mc-btn mc-mode-btn" @click.stop="cycleMode" :title="modeLabels[playMode]">
        <!-- 列表循环 -->
        <svg v-if="playMode === 'list'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
        <!-- 随机播放 -->
        <svg v-else-if="playMode === 'random'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/><line x1="4" y1="4" x2="9" y2="9"/></svg>
        <!-- 单曲循环 -->
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
        <span class="mode-indicator">{{ modeIndicators[playMode] }}</span>
      </button>
      <button class="mc-btn mc-search-btn" @click.stop="toggleSearch" title="搜索歌曲">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      </button>
      <div class="volume-wrap" @mousedown.stop @touchstart.stop>
        <button class="mc-btn mc-vol-icon" @click.stop="toggleMute">
          <svg v-if="volume.value === 0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
        </button>
        <input type="range" class="volume-slider" min="0" max="1" step="0.01" v-model.number="volumeLocal" @input="syncVolume" @mousedown.stop @touchstart.stop />
      </div>
    </div>

    <Teleport to="body">
      <div v-if="showList" class="list-modal" @click.self="showList = false">
        <div class="list-dialog">
          <div class="list-head">
            <span class="list-head-title">播放列表</span>
            <div class="list-head-right">
              <button class="list-clear" @click="clearList" v-if="playlist.length">清空</button>
              <button class="list-close" @click="showList = false">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
          </div>
          <div class="list-body">
            <div v-if="!playlist.length" class="list-empty">列表为空</div>
            <div v-else class="queue-list">
              <div v-for="(s, idx) in playlist" :key="idx" class="queue-item" :class="{ playing: idx === currentIndex }" @click="playByIdx(idx)">
                <span class="queue-num">{{ idx + 1 }}</span>
                <span class="queue-num" v-if="idx === currentIndex && playing">♪</span>
                <div class="queue-info">
                  <span class="queue-title">{{ s.title }}</span>
                  <span class="queue-author">{{ s.author }}</span>
                </div>
                <button class="queue-remove" @click.stop="removeSong(idx)" title="移除">✕</button>
              </div>
            </div>
          </div>
          <div v-if="showGequhaiSearch" class="gequhai-search">
            <div class="gequhai-input-row">
              <input v-model="gequhaiKeyword" class="gequhai-input" placeholder="搜索歌曲..." @keydown.enter="doGequhaiSearch" />
              <button class="gequhai-go" @click="doGequhaiSearch" :disabled="ghLoading">{{ ghLoading ? '...' : '搜' }}</button>
            </div>
            <div v-if="ghResults.length" class="gequhai-results">
              <div v-for="s in ghResults" :key="s.songid" class="gequhai-item" @click="playGequhaiSong(s)">
                <span class="gequhai-title">{{ s.title }}</span>
                <span class="gequhai-author">{{ s.author }}</span>
              </div>
            </div>
            <div v-else-if="ghSearched" class="list-empty">未找到结果</div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useUserStore } from '@/stores/user'
import { gequhaiSearch, gequhaiUrl, gequhaiLyric, getPlaylist, addToPlaylist, removeFromPlaylist, refreshPlaylistUrl } from '@/api/music'
import { getSettings, updateSettings } from '@/api/settings'
import {
  audioEl, playlist, currentIndex, playing, progressPct,
  currentTime, duration, currentSong, volume, setLyrics
} from '@/composables/useMusicPlayer'

const userStore = useUserStore()
const musicKey = (k) => k + '_' + (userStore.user?.username || 'default')

const audioRef = ref(null)
const showList = ref(false)
const showGequhaiSearch = ref(false)
const gequhaiKeyword = ref('')
const ghResults = ref([])
const ghSearched = ref(false)
const ghLoading = ref(false)
const volumeLocal = ref(volume.value)

// ── 播放模式 ──
const PLAY_MODES = ['list', 'random', 'one']
const modeLabels = { list: '列表循环', random: '随机播放', one: '单曲循环' }
const modeIndicators = { list: '', random: '', one: '1' }
const playMode = ref(localStorage.getItem(musicKey('music_mode')) || 'list')

function cycleMode() {
  const idx = PLAY_MODES.indexOf(playMode.value)
  playMode.value = PLAY_MODES[(idx + 1) % PLAY_MODES.length]
  localStorage.setItem(musicKey('music_mode'), playMode.value)
  syncMusicSetting('music_mode', playMode.value)
}

let musicSyncTimer = null
function syncMusicSetting(key, val) {
  clearTimeout(musicSyncTimer)
  musicSyncTimer = setTimeout(() => {
    getSettings().then(res => {
      try {
        const cfg = JSON.parse(res?.layout_config || '{}')
        cfg[key] = val
        updateSettings({ layout_config: JSON.stringify(cfg) })
      } catch {}
    }).catch(() => {})
  }, 500)
}

let playingLock = false

function toggleList() { showList.value = !showList.value }

function toggleSearch() {
  showList.value = true
  showGequhaiSearch.value = true
  nextTick(() => {
    const el = document.querySelector('.gequhai-input')
    if (el) el.focus()
  })
}

// ── 歌曲海搜索 ──
async function doGequhaiSearch() {
  const kw = gequhaiKeyword.value.trim()
  if (!kw) return
  ghLoading.value = true; ghSearched.value = true
  try {
    const res = await gequhaiSearch(kw)
    ghResults.value = (res.data || res) || []
  } catch { ghResults.value = [] }
  finally { ghLoading.value = false }
}

async function playGequhaiSong(song) {
  try {
    const res = await gequhaiUrl(song.songid)
    // axios 拦截器已解包，res 就是 {code, url} 或 {code, msg}
    if (!res || res.code !== 200 || !res.url) {
      showToast(res?.msg || '无法获取歌曲链接')
      return
    }
    song.url = `/api/music/gequhai/proxy?url=${encodeURIComponent(res.url)}`
    song.fetched_at = new Date().toISOString()
    playlist.value.push(song)
    currentIndex.value = playlist.value.length - 1
    localStorage.setItem(musicKey('music_idx'), String(currentIndex.value))
    // 同步到后端，记下返回的 id 以便失败时删除
    try {
      const saveRes = await addToPlaylist({
        songid: song.songid,
        title: song.title,
        author: song.author || '',
        url: song.url,
        lrc: song.lrc || '',
      })
      if (saveRes?.data?.id) song.id = saveRes.data.id
    } catch {}
    showGequhaiSearch.value = false
    showList.value = false
    // 异步获取歌词
    gequhaiLyric(song.songid).then(lrcRes => {
      const lrcData = lrcRes.data || lrcRes
      if (lrcData.lyric) {
        playlist.value[playlist.value.length - 1].lrc = lrcData.lyric
        setLyrics(lrcData.lyric.split('\n'))
      }
    }).catch(() => {})
    playCurrent()
  } catch {}
}

// ── 播放控制 ──
async function playCurrent() {
  if (playingLock) return
  playingLock = true
  const s = playlist.value[currentIndex.value]
  if (!s) { playingLock = false; return }
  currentSong.value = s
  const a = audioEl.value
  if (!a) { playingLock = false; return }

  // 直接播放，链接失效时 onError 会自动刷新

  a.src = s.url.replace(/^http:/, 'https:')
  a.volume = volume.value
  a.play().then(() => {
    playing.value = true; playingLock = false
    initEQ()
    if (s.lrc) setLyrics(s.lrc.split('\n'))
    else setLyrics([])
  }).catch(() => { playingLock = false; onError() })
}

function playByIdx(idx) { currentIndex.value = idx; playCurrent() }

function togglePlay() {
  const a = audioEl.value
  if (!a || !playlist.value.length) return
  if (playing.value) { a.pause(); playing.value = false }
  else {
    if (currentIndex.value < 0) currentIndex.value = 0
    if (a.src) a.play().then(() => { playing.value = true }).catch(() => {})
    else playCurrent()
  }
}

function nextSong() {
  if (!playlist.value.length) return
  playingLock = false // 确保不被锁住，让 @ended 能正确切到下一首
  if (playMode.value === 'one') {
    // 单曲循环：重播当前
    const a = audioEl.value
    if (a) { a.currentTime = 0; a.play().catch(() => {}) }
    return
  }
  if (playMode.value === 'random') {
    let idx
    do { idx = Math.floor(Math.random() * playlist.value.length) }
    while (idx === currentIndex.value && playlist.value.length > 1)
    currentIndex.value = idx
  } else {
    currentIndex.value = (currentIndex.value + 1) % playlist.value.length
  }
  playCurrent()
}

function prevSong() {
  if (!playlist.value.length) return
  currentIndex.value = (currentIndex.value - 1 + playlist.value.length) % playlist.value.length
  playCurrent()
}

function removeSong(idx) {
  const s = playlist.value[idx]
  playlist.value.splice(idx, 1)
  if (currentIndex.value === idx) {
    if (playlist.value.length) currentIndex.value = Math.min(idx, playlist.value.length - 1)
    else { currentIndex.value = -1; currentSong.value = null; playing.value = false }
  } else if (idx < currentIndex.value) currentIndex.value--
  // 从后端删除
  if (s?.id) removeFromPlaylist(s.id).catch(() => {})
}

async function clearList() {
  // 逐个删除后端记录
  for (const s of playlist.value) {
    if (s.id) {
      try { await removeFromPlaylist(s.id) } catch {}
    }
  }
  playlist.value.length = 0; currentIndex.value = -1
  currentSong.value = null; playing.value = false
  progressPct.value = 0; currentTime.value = 0; duration.value = 0
  const a = audioEl.value; if (a) { a.pause(); a.src = '' }
}

function onTime() {
  const a = audioEl.value
  if (a && a.duration) {
    progressPct.value = (a.currentTime / a.duration) * 100
    currentTime.value = a.currentTime
  }
}
function onMeta() { if (audioEl.value) duration.value = audioEl.value.duration }
function onCanplay() {}
// ── 播放错误重试计数（防止无限循环）──
const errorRetries = {}

function onError() {
  playing.value = false
  const s = playlist.value[currentIndex.value]
  if (!s) return
  const songId = s.songid
  if (errorRetries[songId] >= 2) {
    // 已重试过，直接移除
    fallbackRemove(s)
    return
  }
  errorRetries[songId] = (errorRetries[songId] || 0) + 1
  // 尝试用搜索接口重新采集播放地址
  gequhaiUrl(songId).then(refreshRes => {
    const newUrl = refreshRes?.url || refreshRes?.data?.url
    // 只接受 http/https 开头的有效 URL
    if (newUrl && /^https?:\/\//.test(newUrl)) {
      s.url = `/api/music/gequhai/proxy?url=${encodeURIComponent(newUrl)}`
      s.fetched_at = new Date().toISOString()
      setTimeout(playCurrent, 300)
      return
    }
    fallbackRemove(s)
  }).catch(() => fallbackRemove(s))
}

function fallbackRemove(s) {
  const invalidId = s.songid
  playlist.value = playlist.value.filter(x => x.songid !== invalidId)
  if (currentIndex.value >= playlist.value.length) currentIndex.value = playlist.value.length - 1
  if (!playlist.value.length) { currentIndex.value = -1; currentSong.value = null }
  // 也从后端删除，防止刷新又出现
  if (s.id) removeFromPlaylist(s.id).catch(() => {})
  showToast('歌曲链接已失效')
  if (playlist.value.length) setTimeout(nextSong, 500)
}

let prevVol = volume.value
function toggleMute() {
  const a = audioEl.value
  if (!a) return
  if (volume.value > 0) { prevVol = volume.value; volume.value = 0; a.volume = 0 }
  else { volume.value = prevVol; a.volume = prevVol }
  volumeLocal.value = volume.value
  localStorage.setItem(musicKey('music_volume'), String(volume.value))
  syncMusicSetting('music_volume', String(volume.value))
}
function syncVolume() {
  const a = audioEl.value
  volume.value = volumeLocal.value
  if (a) a.volume = volume.value
  localStorage.setItem(musicKey('music_volume'), String(volume.value))
  syncMusicSetting('music_volume', String(volume.value))
}

// EQ 可视化
let analyser = null
let animId = null
const eqCanvas = ref(null)
const eqWrapRef = ref(null)
const eqSeekRef = ref(null)
let audioCtx = null

function drawEQ() {
  const canvas = eqCanvas.value
  if (!canvas || !analyser) return
  const ctx = canvas.getContext('2d')
  const w = canvas.width, h = canvas.height
  const arr = new Uint8Array(analyser.frequencyBinCount)
  analyser.getByteFrequencyData(arr)
  ctx.clearRect(0, 0, w, h)
  const barCount = 48, gap = 2
  const bw = (w - gap * (barCount - 1)) / barCount
  for (let i = 0; i < barCount; i++) {
    const val = arr[Math.floor(i * arr.length * 0.72 / barCount)] / 255
    // 低频权重小，高频权重大，避免低频顶满
    const weight = 0.7 + (i / barCount) * 0.7
    const bh = Math.max(1, Math.min(h, val * h * weight))
    const x = i * (bw + gap), y = h - bh
    // 彩虹渐变：红 → 橙 → 黄 → 绿 → 青 → 蓝 → 紫
    const hue = 360 - i * 7.5
    ctx.fillStyle = `hsla(${hue}, 85%, 55%, ${0.3 + val * 0.7})`
    ctx.beginPath()
    ctx.roundRect(x, y, bw, bh, [2, 2, 0, 0])
    ctx.fill()
  }
  animId = requestAnimationFrame(drawEQ)
}

function initEQ() {
  const a = audioEl.value
  if (!a || audioCtx) return
  try {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    if (audioCtx.state === 'suspended') audioCtx.resume()
    const src = audioCtx.createMediaElementSource(a)
    analyser = audioCtx.createAnalyser()
    analyser.fftSize = 256
    src.connect(analyser)
    analyser.connect(audioCtx.destination)
    drawEQ()
  } catch {}
}

function seekFromEq(e) {
  const el = eqSeekRef.value
  if (!el || !audioEl.value) return
  const rect = el.getBoundingClientRect()
  if (rect.width <= 0) return
  const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  const a = audioEl.value
  if (a.duration && isFinite(a.duration)) {
    a.currentTime = pct * a.duration
  }
}

function fmtTime(s) {
  if (!s || isNaN(s)) return '0:00'
  return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`
}

function showToast(msg) {
  const el = document.createElement('div')
  el.textContent = msg
  el.style.cssText = 'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.8);color:#fff;padding:10px 20px;border-radius:8px;font-size:13px;z-index:999999;animation:toast-fade 3s forwards;backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.1)'
  document.body.appendChild(el)
  setTimeout(() => { if (el.parentNode) el.parentNode.removeChild(el) }, 3000)
}

onMounted(async () => {
  try {
    // 先从后端拉歌单（跨设备同步）
    const res = await getPlaylist()
    const items = res.data || []
    if (items.length) {
      playlist.value = items
      const savedIdx = localStorage.getItem(musicKey('music_idx'))
      if (savedIdx !== null) currentIndex.value = parseInt(savedIdx)
      if (currentIndex.value >= 0 && currentIndex.value < playlist.value.length)
        currentSong.value = playlist.value[currentIndex.value]
      else { currentIndex.value = -1; currentSong.value = null }
    }
  } catch {}
  // 后端无数据时兜底从 localStorage 恢复
  if (!playlist.value.length) {
    try {
      const saved = localStorage.getItem(musicKey('music_playlist'))
      if (saved) {
        const parsed = JSON.parse(saved)
        playlist.value = parsed
        if (playlist.value.length) {
          const savedIdx = localStorage.getItem(musicKey('music_idx'))
          if (savedIdx !== null) currentIndex.value = parseInt(savedIdx)
          if (currentIndex.value >= 0 && currentIndex.value < playlist.value.length)
            currentSong.value = playlist.value[currentIndex.value]
          else { currentIndex.value = -1; currentSong.value = null }
        }
      }
    } catch {}
  }
  if (audioRef.value) audioEl.value = audioRef.value
})

onUnmounted(() => {
  cancelAnimationFrame(animId)
  if (audioCtx) {
    try { audioCtx.close() } catch {}
    audioCtx = null
  }
})
</script>

<style scoped>
.music-card { height:100%; display:flex; flex-direction:column; padding:6px 10px 4px; cursor:default; position:relative;
  background: radial-gradient(ellipse at 20% 30%, color-mix(in srgb, #FF6B6B 8%, transparent) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 70%, color-mix(in srgb, #FDCB6E 6%, transparent) 0%, transparent 50%),
    color-mix(in srgb, var(--bg-card) 70%, transparent);
  backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px); }
.music-top { flex-shrink:0; }
.music-info { display:flex; align-items:center; gap:4px; white-space:nowrap; overflow:hidden; }
.music-note { flex-shrink:0; font-size:14px; color:#FF6B6B; animation:pulse 1s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
.music-note.is-playing { animation:pulse 1s infinite; }
.music-title { font-size:11px; color:var(--text); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.music-placeholder { font-size:10px; color:var(--text3); }

.eq-wrap { position:relative; margin:1px 0; margin-top:auto; }
.eq-canvas { width:100%; height:50px; display:block; border-radius:4px; }
.eq-time { display:flex; align-items:center; gap:4px; margin-top:1px; }
.time-label { font-size:9px; color:var(--text3); font-variant-numeric:tabular-nums; min-width:28px; }
.time-label:last-child { text-align:right; }
.eq-seek-track { flex:1; height:3px; background:color-mix(in srgb, #FF6B6B 20%, transparent); border-radius:2px; position:relative; cursor:pointer; }
.eq-seek-fill { height:100%; background:linear-gradient(90deg, #FF6B6B, #FDCB6E); border-radius:2px; transition:width 0.2s; }

.music-controls { display:flex; align-items:center; gap:1px; margin-top:2px; margin-bottom:4px; }
.mc-btn { width:20px; height:18px; display:flex; align-items:center; justify-content:center; background:none; border:none; color:var(--text3); cursor:pointer; padding:0; transition:color 0.12s; border-radius:3px; }
.mc-btn:hover { color:#FF6B6B; background:color-mix(in srgb, #FF6B6B 10%, transparent); }
.mc-btn svg { width:12px; height:12px; }
.mc-play { width:22px; height:20px; background:color-mix(in srgb, #FF6B6B 15%, transparent); border-radius:4px; color:#FF6B6B; }
.mc-play:hover { background:#FF6B6B; color:white; }
.mc-play svg { width:13px; height:13px; }
.mc-list-btn { position:relative; }
.mc-search-btn { margin-left:1px; }
.mc-search-btn svg { width:13px; height:13px; stroke-width:2.5; }
.mc-mode-btn { position:relative; width:22px; height:18px; }
.mc-mode-btn svg { width:13px; height:13px; }
.mode-indicator { position:absolute; bottom:-1px; right:-1px; font-size:7px; font-weight:700; color:#FF6B6B; line-height:1; }
.list-count { position:absolute; top:-3px; right:-3px; min-width:11px; height:11px; background:#FF6B6B; color:white; font-size:7px; border-radius:6px; display:flex; align-items:center; justify-content:center; padding:0 2px; }
.volume-wrap { display:flex; align-items:center; gap:1px; margin-left:auto; }
.volume-slider { width:36px; height:2px; accent-color:#FF6B6B; cursor:pointer; }
.mc-vol-icon { width:16px; height:16px; }
.mc-vol-icon svg { width:10px; height:10px; }
</style>

<style>
.list-modal { position:fixed; inset:0; z-index:99999; background:rgba(0,0,0,0.5); backdrop-filter:blur(4px); display:flex; align-items:center; justify-content:center; }
.list-dialog { width:380px; max-width:90vw; max-height:65vh; background:var(--bg-modal); border:1px solid var(--border); border-radius:16px; padding:16px; box-shadow:0 16px 50px rgba(0,0,0,0.5); display:flex; flex-direction:column; gap:10px; }
.list-head { display:flex; align-items:center; justify-content:space-between; }
.list-head-title { font-size:15px; font-weight:700; }
.list-head-right { display:flex; align-items:center; gap:6px; }
.list-clear { padding:3px 10px; font-size:11px; background:var(--bg-glass); border:1px solid var(--border); border-radius:6px; color:var(--text2); cursor:pointer; }
.list-local-btn { padding:3px 10px; font-size:11px; background:var(--bg-glass); border:1px solid var(--border); border-radius:6px; color:var(--text2); cursor:pointer; }
.list-close { width:28px; height:28px; display:flex; align-items:center; justify-content:center; background:var(--bg-glass); border:none; border-radius:8px; color:var(--text2); cursor:pointer; }
.list-body { flex:1; overflow-y:auto; }
.list-empty { padding:24px; text-align:center; color:var(--text3); font-size:12px; }
.queue-list { display:flex; flex-direction:column; gap:1px; }
.queue-item { display:flex; align-items:center; gap:8px; padding:6px 8px; border-radius:8px; cursor:pointer; }
.queue-item:hover { background:var(--bg-glass); }
.queue-item.playing { background:color-mix(in srgb, #FF6B6B 8%, transparent); }
.queue-num { width:16px; text-align:center; font-size:10px; color:var(--text3); flex-shrink:0; }
.queue-info { flex:1; overflow:hidden; }
.queue-title { font-size:12px; color:var(--text); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.queue-author { font-size:10px; color:var(--text3); }
.queue-remove { width:20px; height:20px; flex-shrink:0; display:flex; align-items:center; justify-content:center; background:none; border:none; color:var(--text3); cursor:pointer; font-size:10px; border-radius:4px; opacity:0; }
.queue-item:hover .queue-remove { opacity:1; }
.queue-remove:hover { color:var(--danger); }
.gequhai-search { border-top:1px solid var(--border); padding:10px 0 0; display:flex; flex-direction:column; gap:6px; }
.gequhai-input-row { display:flex; gap:4px; }
.gequhai-input { flex:1; padding:6px 10px; font-size:12px; border:1px solid var(--border); border-radius:6px; background:var(--bg-input); color:var(--text); outline:none; }
.gequhai-go { padding:6px 12px; font-size:11px; background:#FF6B6B; color:white; border:none; border-radius:6px; cursor:pointer; font-weight:600; }
.gequhai-go:disabled { opacity:0.5; }
.gequhai-results { display:flex; flex-direction:column; gap:2px; max-height:180px; overflow-y:auto; }
.gequhai-item { display:flex; align-items:center; gap:8px; padding:5px 8px; border-radius:6px; cursor:pointer; }
.gequhai-item:hover { background:var(--bg-glass); }
.gequhai-title { font-size:12px; color:var(--text); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }
.gequhai-author { font-size:10px; color:var(--text3); flex-shrink:0; }
@keyframes toast-fade { 0%{opacity:0;transform:translateX(-50%) translateY(10px)} 10%{opacity:1;transform:translateX(-50%) translateY(0)} 80%{opacity:1} 100%{opacity:0} }
</style>
