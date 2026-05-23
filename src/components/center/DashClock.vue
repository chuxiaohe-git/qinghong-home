<template>
  <div class="clock-card" @contextmenu.prevent="openCtx">
    <!-- 时钟模式 -->
    <template v-if="mode === 'clock'">
      <div class="clock-main">
        <div class="clock-frame">
          <span class="clock-time">{{ timeStr }}</span>
          <span class="clock-sec" v-if="showSec">:{{ secStr }}</span>
        </div>
        <div class="clock-date">{{ dateStr }}</div>
      </div>
      <div class="clock-footer">
        <div class="weather-info">
          <span class="weather-icon">{{ weatherIcon }}</span>
          <span class="weather-temp">{{ weatherText }}</span>
          <span v-if="!editingCity" class="weather-city" @click.stop="startEditCity" title="点击切换城市">{{ city }}</span>
          <input v-else ref="cityInput" v-model="cityInputVal" class="city-input" @blur="confirmCity" @keydown.enter="confirmCity" @keydown.escape="cancelEdit" />
        </div>
        <div class="lunar-info">
          <span class="lunar-item good">宜<span class="lunar-val">{{ currentYiJi.yi }}</span></span>
          <span class="lunar-divider">·</span>
          <span class="lunar-item bad">忌<span class="lunar-val">{{ currentYiJi.ji }}</span></span>
        </div>
      </div>
    </template>

    <!-- 倒计时模式 -->
    <template v-else>
      <div class="countdown-main">
        <div class="countdown-frame">
          <span class="countdown-time">{{ countdownStr }}</span>
        </div>
        <div class="countdown-progress">
          <div class="progress-bar" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <div class="countdown-label" v-if="countdownLabel">{{ countdownLabel }}</div>
      </div>
      <div class="countdown-footer">
        <template v-if="!countdownRunning">
          <button class="cd-btn" @click="startCountdown(5)">5′</button>
          <button class="cd-btn" @click="startCountdown(10)">10′</button>
          <button class="cd-btn" @click="startCountdown(25)">25′</button>
          <button class="cd-btn" @click="startCountdown(60)">1h</button>
        </template>
        <template v-else>
          <button class="cd-btn cd-main" @click="pauseCountdown">
            {{ countdownPaused ? '▶' : '⏸' }}
          </button>
          <button class="cd-btn" @click="stopCountdown">⏹</button>
        </template>
      </div>
    </template>

    <!-- 右键菜单 -->
    <Teleport to="body">
      <div v-if="ctxShow" class="ctx-menu" :style="ctxStyle">
        <button class="ctx-item" :class="{ active: mode === 'clock' }" @click="switchMode('clock')">🕐 时钟</button>
        <button class="ctx-item" :class="{ active: mode === 'countdown' }" @click="switchMode('countdown')">⏱ 倒计时</button>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useUserStore } from '@/stores/user'
import { getSettings, updateSettings } from '@/api/settings'
const userStore = useUserStore()

const emit = defineEmits(['ctxopen'])
const userCityKey = 'dashclock_city_' + (userStore.user?.username || 'default')

const mode = ref('clock')
const savedCity = localStorage.getItem(userCityKey) || '北京'
const city = ref(savedCity)
// 从后端加载城市（覆盖 localStorage）
getSettings().then(res => {
  try {
    const cfg = JSON.parse(res?.layout_config || '{}')
    if (cfg.weather_city && cfg.weather_city !== city.value) {
      city.value = cfg.weather_city
      localStorage.setItem(userCityKey, cfg.weather_city)
      fetchWeather()
    }
  } catch {}
}).catch(() => {})
const weatherIcon = ref('')
const weatherText = ref('')
const timeStr = ref('')
const dateStr = ref('')
const secStr = ref('')
const showSec = ref(true)
const editingCity = ref(false)
const cityInputVal = ref('')
const cityInput = ref(null)
const ctxShow = ref(false)
const ctxStyle = ref({})
let timer = null

const countdownSeconds = ref(0)
const countdownTotal = ref(0)
const countdownRunning = ref(false)
const countdownPaused = ref(false)
const countdownLabel = ref('')

// 黄历预制文案
const yiJiList = [
  { yi: '摸鱼', ji: '上班' },
  { yi: '发呆', ji: '焦虑' },
  { yi: '摸鱼', ji: '内卷' },
  { yi: '躺平', ji: 'kpi' },
  { yi: '喝水', ji: '开会' },
  { yi: '散步', ji: '加班' },
  { yi: '午睡', ji: '早起' },
  { yi: '摸鱼', ji: '汇报' },
  { yi: '追剧', ji: '写文档' },
  { yi: '刷手机', ji: '回邮件' },
  { yi: '聊天', ji: '干活' },
  { yi: '喝咖啡', ji: '写代码' },
  { yi: '划水', ji: '背锅' },
  { yi: '摸鱼', ji: '卷王' },
  { yi: '吃瓜', ji: '种瓜' },
  { yi: '摸鱼', ji: '卷' },
  { yi: '摸鱼', ji: '卷PPT' },
  { yi: '看剧', ji: '做表格' },
  { yi: '摸鱼', ji: '写周报' },
  { yi: '摸鱼', ji: '填需求' },
  { yi: '网购', ji: '比价' },
  { yi: '摸鱼', ji: '接需求' },
  { yi: '听歌', ji: '开会' },
  { yi: '摸鱼', ji: 'debug' },
  { yi: '刷短视频', ji: '刷长视频' },
  { yi: '摸鱼', ji: '对线' },
  { yi: '做梦', ji: '干活' },
  { yi: '摸鱼', ji: '卷deadline' },
  { yi: '看天', ji: '看文档' },
  { yi: '摸鱼', ji: '赶进度' },
  { yi: '摸鱼', ji: '赶需求' },
  { yi: '逛B站', ji: '写代码' },
  { yi: '摸鱼', ji: 'review' },
  { yi: '发呆', ji: 'commit' },
  { yi: '摸鱼', ji: 'deploy' },
  { yi: '喝奶茶', ji: '喝白水' },
  { yi: '摸鱼', ji: '发版' },
  { yi: '摸鱼', ji: '上线' },
  { yi: '看夕阳', ji: '看报错' },
  { yi: '摸鱼', ji: '联调' },
  { yi: '发呆', ji: '需求评审' },
  { yi: '摸鱼', ji: '迭代' },
  { yi: '摸鱼', ji: '冲刺' },
  { yi: '摆烂', ji: '挣扎' },
  { yi: '摸鱼', ji: '排期' },
  { yi: '摸鱼', ji: '计划' },
  { yi: '发呆', ji: '思考人生' },
  { yi: '摸鱼', ji: '改bug' },
  { yi: '摸鱼', ji: '做任务' },
]

const getRandomYiJi = () => {
  // 以日期+用户名为种子，每天每人不同
  const seed = new Date().toISOString().slice(0, 10) + '_' + (userStore.user?.username || '')
  let hash = 0
  for (let i = 0; i < seed.length; i++) hash = ((hash << 5) - hash) + seed.charCodeAt(i)
  const idx = Math.abs(hash) % yiJiList.length
  return yiJiList[idx]
}
const currentYiJi = ref(getRandomYiJi())
let countdownTimer = null

const countdownStr = computed(() => {
  const m = Math.floor(countdownSeconds.value / 60)
  const s = countdownSeconds.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

const progressPercent = computed(() => {
  if (!countdownTotal.value) return 0
  return Math.round((countdownSeconds.value / countdownTotal.value) * 100)
})

function updateTime() {
  const now = new Date()
  timeStr.value = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
  secStr.value = String(now.getSeconds()).padStart(2, '0')
  const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  const month = now.getMonth() + 1
  const day = now.getDate()
  dateStr.value = `${month}月${day}日，${weekdays[now.getDay()]}`
}

async function fetchWeather() {
  try {
    const res = await fetch(`https://wttr.in/${encodeURIComponent(city.value)}?format=j1`)
    const data = await res.json()
    const current = data.current_condition?.[0]
    if (current) {
      const cond = (current.weatherDesc?.[0]?.value || '').toLowerCase()
      const emojiMap = {
        sunny: '☀️', clear: '🌙', cloudy: '☁️', overcast: '☁️',
        rain: '🌧️', drizzle: '🌦️', thunder: '⛈️', snow: '❄️',
        mist: '🌫️', fog: '🌫️', haze: '🌫️', windy: '💨',
        'light rain': '🌦️', 'heavy rain': '🌧️', 'patchy rain': '🌦️',
        'light snow': '🌨️', 'heavy snow': '❄️',
      }
      let emoji = '🌤️'
      for (const [k, v] of Object.entries(emojiMap)) {
        if (cond.includes(k)) { emoji = v; break }
      }
      weatherIcon.value = emoji
      weatherText.value = `${current.temp_C}°`
    }
  } catch {
    weatherIcon.value = '🌤️'
    weatherText.value = '--°'
  }
}

// 同步城市到后端数据库
let citySyncTimer = null
function syncCity() {
  clearTimeout(citySyncTimer)
  citySyncTimer = setTimeout(() => {
    getSettings().then(res => {
      const cfg = JSON.parse(res?.layout_config || '{}')
      cfg.weather_city = city.value
      updateSettings({ layout_config: JSON.stringify(cfg) }).catch(() => {})
    }).catch(() => {})
  }, 500)
}

function startEditCity() {
  cityInputVal.value = city.value
  editingCity.value = true
  setTimeout(() => cityInput.value?.focus(), 50)
}
function confirmCity() {
  const val = cityInputVal.value.trim()
  if (val && val !== city.value) { city.value = val; localStorage.setItem(userCityKey, val); syncCity(); fetchWeather() }
  editingCity.value = false
}
function cancelEdit() { editingCity.value = false }

function autoLocate() {
  if (!navigator.geolocation) return
  navigator.geolocation.getCurrentPosition(async (pos) => {
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${pos.coords.latitude}&lon=${pos.coords.longitude}&accept-language=zh`,
        { headers: { 'User-Agent': 'DashClock/1.0' } }
      )
      const data = await res.json()
      const addr = data.address
      const c = addr?.city || addr?.town || addr?.county || addr?.state
      if (c && c !== city.value) { city.value = c; localStorage.setItem(userCityKey, c); syncCity(); fetchWeather() }
    } catch {}
  }, () => {}, { timeout: 5000 })
}

// 右键菜单
function openCtx(e) {
  e.preventDefault()
  e.stopPropagation()
  ctxShow.value = false
  emit('ctxopen')
  nextTick(() => {
    ctxStyle.value = { left: `${Math.min(e.clientX, window.innerWidth - 120)}px`, top: `${Math.min(e.clientY, window.innerHeight - 80)}px` }
    ctxShow.value = true
  })
}
function closeCtx() { ctxShow.value = false }
function switchMode(m) {
  if (m === mode.value) { closeCtx(); return }
  if (m === 'countdown') {
    mode.value = 'countdown'
    countdownLabel.value = ''
    countdownSeconds.value = 0
    countdownTotal.value = 0
    countdownRunning.value = false
    countdownPaused.value = false
  } else {
    mode.value = 'clock'
    stopCountdown()
  }
  closeCtx()
}

function startCountdown(minutes) {
  countdownTotal.value = minutes * 60
  countdownSeconds.value = countdownTotal.value
  countdownRunning.value = true
  countdownPaused.value = false
  countdownLabel.value = minutes >= 60 ? '1小时' : `${minutes}分钟`
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    if (!countdownPaused.value) {
      countdownSeconds.value--
      if (countdownSeconds.value <= 0) {
        clearInterval(countdownTimer); countdownTimer = null
        countdownRunning.value = false
        countdownLabel.value = '时间到!'
      }
    }
  }, 1000)
}
function pauseCountdown() { countdownPaused.value = !countdownPaused.value }
function stopCountdown() {
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = null; countdownRunning.value = false
  countdownPaused.value = false; countdownSeconds.value = 0
  countdownTotal.value = 0; countdownLabel.value = ''
}

onMounted(() => {
  updateTime(); fetchWeather(); autoLocate()
  timer = setInterval(updateTime, 1000)
  document.addEventListener('click', closeCtx)
  window.addEventListener('close-clock-ctx', closeCtx)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (countdownTimer) clearInterval(countdownTimer)
  document.removeEventListener('click', closeCtx)
  window.removeEventListener('close-clock-ctx', closeCtx)
})
</script>

<style scoped>
.clock-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 12px 14px 10px;
  cursor: default;
  position: relative;
  background:
    radial-gradient(ellipse at 80% 20%, color-mix(in srgb, #00CEC9 10%, transparent) 0%, transparent 50%),
    radial-gradient(ellipse at 10% 80%, color-mix(in srgb, #6C5CE7 8%, transparent) 0%, transparent 50%),
    color-mix(in srgb, var(--bg-card) 70%, transparent);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  overflow: hidden;
}

/* ====== 时钟模式 ====== */
.clock-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  justify-content: center;
}

.clock-frame {
  display: flex;
  align-items: baseline;
  line-height: 1;
}

.clock-time {
  font-family: 'Orbitron', 'Roboto Mono', monospace;
  font-size: 36px;
  font-weight: 700;
  background: linear-gradient(135deg, #6C5CE7, #00CEC9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 2px;
}

.clock-sec {
  font-family: 'Orbitron', 'Roboto Mono', monospace;
  font-size: 18px;
  font-weight: 500;
  color: var(--text3);
  margin-left: 1px;
}

.clock-date {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
  font-size: 14px;
  color: var(--text2);
  margin-top: 4px;
  letter-spacing: 0.5px;
}

.clock-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 6px;
  border-top: 1px solid var(--border);
}

.weather-info {
  display: flex;
  align-items: center;
  gap: 4px;
}

.weather-icon {
  font-size: 14px;
}

.weather-temp {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.weather-city {
  font-size: 10px;
  color: var(--text3);
  cursor: pointer;
  padding: 1px 5px;
  border-radius: 4px;
  border: 1px solid var(--border);
  transition: all 0.12s;
}

.weather-city:hover {
  border-color: var(--primary);
  color: var(--text);
}

.city-input {
  width: 60px;
  font-size: 10px;
  padding: 1px 5px;
  border: 1px solid var(--primary);
  border-radius: 4px;
  background: var(--bg-input);
  color: var(--text);
  outline: none;
}

.lunar-info {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}
.lunar-item {
  display: flex;
  align-items: center;
  gap: 2px;
}
.lunar-item.good {
  color: #00CEC9;
}
.lunar-item.bad {
  color: #FF6B6B;
}
.lunar-val {
  font-weight: 600;
}
.lunar-divider {
  color: var(--text3);
}

/* ====== 倒计时模式 ====== */
.countdown-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  justify-content: center;
  gap: 8px;
}

.countdown-frame {
  display: flex;
  align-items: baseline;
}

.countdown-time {
  font-family: 'Orbitron', 'Roboto Mono', monospace;
  font-size: 36px;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: 3px;
}

.countdown-progress {
  width: 100%;
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--primary));
  border-radius: 2px;
  transition: width 0.3s ease;
}

.countdown-label {
  font-size: 11px;
  color: var(--text3);
  letter-spacing: 1px;
}

.countdown-footer {
  display: flex;
  gap: 6px;
  justify-content: center;
  padding-top: 6px;
  border-top: 1px solid var(--border);
}

.cd-btn {
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 500;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-glass);
  color: var(--text2);
  cursor: pointer;
  transition: all 0.12s;
}

.cd-btn:hover {
  border-color: var(--accent);
  color: var(--text);
}

.cd-main {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

.cd-main:hover {
  opacity: 0.85;
}
</style>

<style>
/* Teleport 右键菜单 */
.ctx-menu {
  position: fixed;
  z-index: 99999;
  min-width: 110px;
  background: var(--bg-menu);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 4px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.ctx-item {
  display: block;
  width: 100%;
  padding: 6px 10px;
  background: none;
  border: none;
  border-radius: 5px;
  color: var(--text2);
  font-size: 12px;
  text-align: left;
  cursor: pointer;
  transition: all 0.1s;
}
.ctx-item:hover { background: var(--bg-glass); color: var(--text); }
.ctx-item.active { color: var(--accent); font-weight: 600; }
</style>
