<template>
  <div class="tab-content">
    <h3 class="section-title">背景颜色</h3>
    <p class="hint">设置底色后页面背景会以此为基准生成渐变效果</p>
    <div class="theme-badge" :class="currentTheme">{{ currentTheme === 'dark' ? '🌙 夜间模式' : '☀️ 白天模式' }}</div>
    <div class="color-row">
      <input :value="currentBgColor" @input="onColorChange($event.target.value)" type="color" class="big-picker" />
      <input :value="currentBgColor" @input="onColorChange($event.target.value)" class="input color-input" placeholder="#1a1a2e" />
      <button class="btn-sm" @click="onColorChange('#1a1a2e')">重置暗色</button>
      <button class="btn-sm" @click="onColorChange('#eef2ff')">重置浅色</button>
    </div>

    <div class="section-divider"></div>

    <h3 class="section-title">卡片透明度</h3>
    <p class="hint">调整卡片玻璃层的透明度，数值越大越透明</p>
    <div class="opacity-row">
      <input
        type="range"
        v-model.number="cardTransparency"
        min="0"
        max="0.9"
        step="0.05"
        class="opacity-slider"
      />
      <span class="opacity-value">{{ Math.round(cardTransparency * 100) }}%</span>
    </div>

    <div class="section-divider"></div>

    <h3 class="section-title">壁纸轮播</h3>
    <p class="hint">从图库中选择壁纸，多选后将自动轮播切换</p>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else>
      <!-- 上传区域 -->
      <div class="upload-area" @click="$refs.uploadInput.click()" @dragover.prevent @drop.prevent="onDrop">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        <p>点击或拖拽图片上传壁纸</p>
        <input ref="uploadInput" type="file" accept="image/*" multiple hidden @change="onUpload" />
      </div>

      <p v-if="uploading" class="uploading">上传中...</p>

      <div class="wallpaper-toolbar">
        <span class="wallpaper-count">{{ selectedIds.length }} / {{ wallpapers.length }} 选中</span>
        <div class="wallpaper-actions">
          <button class="btn-xs" @click="selectAll" :disabled="wallpapers.length === 0">全选</button>
          <button class="btn-xs" @click="deselectAll" :disabled="selectedIds.length === 0">取消全选</button>
        </div>
      </div>

      <div class="wallpaper-grid">
        <div
          v-for="img in wallpapers"
          :key="img.id"
          class="wallpaper-item"
          :class="{ selected: selectedIds.includes(img.id) }"
          @click="toggleSelect(img.id)"
        >
          <img :src="getImgUrl(img)" :alt="img.original_name" />
          <div class="check-mark" v-if="selectedIds.includes(img.id)">✓</div>
        </div>
        <div v-if="wallpapers.length === 0" class="no-data">
          暂无壁纸，点击上方区域上传
        </div>
      </div>

      <div v-if="selectedIds.length >= 2" class="carousel-options">
        <label class="toggle-row">
          <span>启用轮播</span>
          <label class="toggle">
            <input type="checkbox" v-model="carouselEnabled" />
            <span class="toggle-slider"></span>
          </label>
        </label>
        <div class="info-row">
          <label>切换间隔（分钟）</label>
          <input v-model.number="interval" type="number" class="input" min="0.5" max="120" step="0.5" style="width:80px" />
        </div>
      </div>
    </template>

    <div class="section-divider"></div>

    <h3 class="section-title">功能卡片</h3>
    <p class="hint">控制首页顶部各功能卡片的显示与隐藏</p>

    <div class="card-toggle-grid">
      <label v-for="card in CARD_OPTIONS" :key="card.key"
        class="card-toggle-chip" :class="{ off: hiddenCards.includes(card.key) }">
        <input type="checkbox" :checked="!hiddenCards.includes(card.key)"
          @change="toggleCard(card.key)" />
        <span class="chip-icon">{{ card.icon }}</span>
        <span>{{ card.label }}</span>
      </label>
    </div>

    <div class="section-divider"></div>

    <h3 class="section-title">导航栏显示</h3>
    <p class="hint">控制左侧导航栏各项目的显示与隐藏（网页收藏默认显示）</p>

    <div class="card-toggle-grid">
      <label v-for="nav in NAV_OPTIONS" :key="nav.key"
        class="card-toggle-chip" :class="{ off: hiddenNav.includes(nav.key) }">
        <input type="checkbox" :checked="!hiddenNav.includes(nav.key)"
          @change="toggleNav(nav.key)" />
        <span class="chip-icon">{{ nav.icon }}</span>
        <span>{{ nav.label }}</span>
      </label>
    </div>

    <div class="section-divider"></div>
    <button class="btn-primary" :disabled="saving" @click="save">
      {{ saving ? '保存中...' : '保存设置' }}
    </button>
    <p v-if="msg" class="msg">{{ msg }}</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { getSettings, updateSettings } from '@/api/settings'
import { getGallery, uploadImage } from '@/api/gallery'

const currentTheme = computed(() =>
  document.documentElement.classList.contains('light-theme') ? 'light' : 'dark'
)

const CARD_OPTIONS = [
  { key: 'quote', icon: '💬', label: '一言' },
  { key: 'clock', icon: '🕐', label: '时钟' },
  { key: 'game', icon: '🎮', label: '游戏' },
  { key: 'music', icon: '🎵', label: '音乐' },
  { key: 'food', icon: '🃏', label: '抽卡' },
  { key: 'websearch', icon: '🔍', label: '网络搜索' },
]
const NAV_OPTIONS = [
  { key: 'calendar', icon: '📅', label: '摸鱼日历' },
  { key: 'notes', icon: '📝', label: '摸鱼笔记' },
  { key: 'wiki', icon: '📖', label: '摸鱼WIKI' },
  { key: 'ai', icon: '🤖', label: 'AI对话' },
]
const bgColorDark = ref('#1a1a2e')
const bgColorLight = ref('#eef2ff')
const currentBgColor = computed(() => currentTheme.value === 'dark' ? bgColorDark.value : bgColorLight.value)
const cardTransparency = ref(0) // 透明度，0 = 不透明，0.9 = 最透明
const wallpapers = ref([])
const selectedIds = ref([])
const carouselEnabled = ref(false)
const interval = ref(1)
const loading = ref(true)
const uploading = ref(false)
const saving = ref(false)
const msg = ref('')
const uploadInput = ref(null)
const hiddenCards = ref([])
const hiddenNav = ref([])

function getImgUrl(img) {
  return img.url || `/uploads/${img.filename}`
}

function onColorChange(val) {
  if (currentTheme.value === 'dark') bgColorDark.value = val
  else bgColorLight.value = val
}

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) {
    selectedIds.value.splice(idx, 1)
  } else {
    selectedIds.value.push(id)
  }
}

async function onUpload(e) {
  const files = e.target.files
  if (!files.length) return
  await uploadFiles(files)
  e.target.value = ''
}

async function onDrop(e) {
  const files = e.dataTransfer.files
  if (!files.length) return
  await uploadFiles(files)
}

async function uploadFiles(files) {
  uploading.value = true
  try {
    for (const file of files) {
      if (!file.type.startsWith('image/')) continue
      const res = await uploadImage(file, 'wallpaper')
      wallpapers.value.unshift(res.data)
      // 上传新图片后自动取消其他选中，只选新图片
      selectedIds.value = [res.data.id]
    }
  } catch (e) {
    alert('上传失败：' + e.message)
  } finally {
    uploading.value = false
  }
}

function selectAll() {
  selectedIds.value = wallpapers.value.map(i => i.id)
}

function deselectAll() {
  selectedIds.value = []
}

function toggleCard(key) {
  const idx = hiddenCards.value.indexOf(key)
  if (idx >= 0) {
    hiddenCards.value.splice(idx, 1)
  } else {
    hiddenCards.value.push(key)
  }
}

function toggleNav(key) {
  const idx = hiddenNav.value.indexOf(key)
  if (idx >= 0) {
    hiddenNav.value.splice(idx, 1)
  } else {
    hiddenNav.value.push(key)
  }
}

async function load() {
  try {
    const [res, galleryRes] = await Promise.all([
      getSettings(),
      getGallery('wallpaper'),
    ])
    const cfg = res.data?.layout_config
    if (cfg) {
      try {
        const parsed = typeof cfg === 'string' ? JSON.parse(cfg) : cfg
        bgColorDark.value = parsed.bgColorDark || '#1a1a2e'
        bgColorLight.value = parsed.bgColorLight || '#eef2ff'
        cardTransparency.value = parsed.cardTransparency ?? 0
        selectedIds.value = parsed.wallpaperIds || []
      carouselEnabled.value = parsed.carouselEnabled || false
      interval.value = parsed.interval || 1
      // 恢复隐藏导航状态
      if (parsed.hidden_nav && Array.isArray(parsed.hidden_nav)) {
        hiddenNav.value = parsed.hidden_nav
      }
      if (parsed.hidden_cards && Array.isArray(parsed.hidden_cards)) {
        hiddenCards.value = parsed.hidden_cards
      }
        // 应用卡片透明度
        applyCardTransparency(cardTransparency.value)
      } catch {}
    }
    wallpapers.value = galleryRes.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  msg.value = ''
  try {
    await updateSettings({
      layout_config: JSON.stringify({
        bgColorDark: bgColorDark.value,
        bgColorLight: bgColorLight.value,
        cardTransparency: cardTransparency.value,
        wallpaperIds: selectedIds.value,
        carouselEnabled: carouselEnabled.value,
        interval: interval.value,
        hidden_cards: [...hiddenCards.value],
        hidden_nav: [...hiddenNav.value],
      }),
    })
    msg.value = '保存成功'
    // 应用卡片透明度
    applyCardTransparency(cardTransparency.value)
    // 通知主页同步隐藏状态
    window.dispatchEvent(new CustomEvent('dashboard-cards-changed', {
      detail: { hiddenCards: [...hiddenCards.value] }
    }))
    // 通知侧边栏同步导航显隐
    window.dispatchEvent(new CustomEvent('nav-visibility-changed', {
      detail: { hiddenNav: [...hiddenNav.value] }
    }))
    // 触发全局背景更新，传当前模式
    const theme = currentTheme.value
    window.dispatchEvent(new CustomEvent('bg-update', {
      detail: {
        bgColor: theme === 'dark' ? bgColorDark.value : bgColorLight.value,
        bgColorDark: bgColorDark.value,
        bgColorLight: bgColorLight.value,
        cardTransparency: cardTransparency.value,
        theme: theme,
        wallpaperIds: selectedIds.value,
        carouselEnabled: carouselEnabled.value,
        interval: interval.value,
      }
    }))
  } catch (e) {
    msg.value = '保存失败：' + e.message
  } finally {
    saving.value = false
  }
}

// 应用卡片透明度到 CSS 变量
// cardTransparency: 0 = 完全不透明，0.9 = 最透明
// 直接映射到 rgba 中的 opacity 值
function applyCardTransparency(transparency) {
  document.documentElement.style.setProperty('--card-bg-opacity', transparency.toString())
}

onMounted(load)

// 监听主页卡片关闭事件（用户在首页点了×）— 用命名函数确保能正确移除
function onDashboardCardsChanged(e) {
  if (e.detail && Array.isArray(e.detail.hiddenCards)) {
    hiddenCards.value = e.detail.hiddenCards
  }
}
window.addEventListener('dashboard-cards-changed', onDashboardCardsChanged)

onBeforeUnmount(() => {
  window.removeEventListener('dashboard-cards-changed', onDashboardCardsChanged)
})
</script>

<style scoped>
.tab-content { max-width: 600px; }
.section-title { font-size: 15px; font-weight: 700; margin-bottom: 8px; }
.hint { color: var(--text3); font-size: 13px; margin-bottom: 14px; }
.theme-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;
  margin-bottom: 12px;
}
.theme-badge.dark { background: rgba(15, 15, 26, 0.2); color: #b8b8ff; border: 1px solid rgba(255,255,255,0.1); }
.theme-badge.light { background: rgba(66, 133, 244, 0.1); color: #1a5cc8; border: 1px solid rgba(66,133,244,0.15); }
.color-row { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.big-picker { width: 48px; height: 48px; padding: 2px; border: 1px solid var(--border); border-radius: 10px; background: transparent; cursor: pointer; }
.color-input { width: 140px !important; }
.input {
  padding: 8px 12px; background: var(--bg-input); border: 1px solid var(--border);
  border-radius: 8px; color: var(--text); font-size: 13px;
}
.input:focus { border-color: var(--primary); }
.btn-sm { padding: 6px 12px; background: var(--bg-glass); border: 1px solid var(--border); border-radius: 6px; color: var(--text2); font-size: 12px; cursor: pointer; }
.btn-sm:hover { background: rgba(128,128,128,0.1); }
.opacity-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.opacity-slider {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: linear-gradient(to right, var(--primary), var(--accent));
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}
.opacity-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: white;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}
.opacity-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: white;
  border-radius: 50%;
  cursor: pointer;
  border: none;
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}
.opacity-value {
  min-width: 48px;
  text-align: right;
  font-size: 14px;
  font-weight: 600;
  color: var(--primary);
}
.section-divider { border: none; border-top: 1px solid var(--border); margin: 20px 0; }
.upload-area {
  border: 2px dashed var(--border); border-radius: 12px; padding: 24px;
  text-align: center; cursor: pointer; transition: all 0.2s; margin-bottom: 16px;
  color: var(--text3); font-size: 13px;
}
.upload-area:hover { border-color: var(--primary); color: var(--text2); background: var(--bg-glass); }
.upload-area svg { margin-bottom: 8px; }
.uploading { color: var(--text3); font-size: 13px; margin-bottom: 12px; }
.wallpaper-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 10px;
}
.wallpaper-count { font-size: 12px; color: var(--text3); }
.wallpaper-actions { display: flex; gap: 6px; }
.btn-xs {
  padding: 4px 10px; background: var(--bg-glass); border: 1px solid var(--border);
  border-radius: 5px; color: var(--text2); font-size: 11px; cursor: pointer;
}
.btn-xs:hover:not(:disabled) { border-color: var(--primary); color: var(--text); }
.btn-xs:disabled { opacity: 0.4; cursor: not-allowed; }
.loading { color: var(--text3); padding: 20px 0; }
.wallpaper-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 10px; margin-bottom: 16px; }
.wallpaper-item {
  position: relative; aspect-ratio: 16/10; border-radius: 8px; overflow: hidden;
  border: 2px solid transparent; cursor: pointer; transition: border-color 0.15s;
}
.wallpaper-item img { width: 100%; height: 100%; object-fit: cover; }
.wallpaper-item.selected { border-color: var(--primary); }
.check-mark {
  position: absolute; top: 4px; right: 4px; width: 20px; height: 20px;
  background: var(--primary); border-radius: 50%; color: white; font-size: 12px;
  display: flex; align-items: center; justify-content: center;
}
.no-data { grid-column: 1 / -1; color: var(--text3); font-size: 13px; padding: 20px 0; text-align: center; }
.carousel-options { margin-bottom: 16px; }
.toggle-row { display: flex; align-items: center; gap: 12px; font-size: 14px; margin-bottom: 12px; }
.toggle { display: flex; align-items: center; cursor: pointer; }
.toggle input { display: none; }
.toggle-slider {
  width: 40px; height: 22px; background: rgba(128,128,128,0.2); border-radius: 11px;
  position: relative; transition: background 0.2s;
}
.toggle-slider::after {
  content: ''; position: absolute; top: 2px; left: 2px;
  width: 18px; height: 18px; background: white; border-radius: 50%; transition: transform 0.2s;
}
.toggle input:checked + .toggle-slider { background: var(--primary); }
.toggle input:checked + .toggle-slider::after { transform: translateX(18px); }
.info-row { display: flex; align-items: center; gap: 12px; font-size: 13px; color: var(--text2); }
.btn-primary { padding: 8px 20px; background: var(--primary); border: none; border-radius: 8px; color: white; font-size: 14px; font-weight: 600; cursor: pointer; }
.btn-primary:disabled { opacity: 0.6; }
.msg { margin-top: 12px; font-size: 13px; color: var(--accent); }
/* 功能卡片 — 紧凑并排 */
.card-toggle-grid {
  display: flex; flex-wrap: wrap; gap: 8px;
}
.card-toggle-chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 10px; border-radius: 20px;
  background: var(--bg-glass); border: 1px solid var(--border);
  cursor: pointer; transition: opacity 0.15s, border-color 0.15s, background 0.15s;
  font-size: 13px; color: var(--text2); user-select: none;
}
.card-toggle-chip:hover { border-color: rgba(128,128,128,0.35); }
.card-toggle-chip.off { opacity: 0.45; text-decoration: line-through; }
.card-toggle-chip input[type="checkbox"] {
  appearance: none; -webkit-appearance: none;
  width: 16px; height: 16px; border-radius: 4px;
  border: 1.5px solid var(--border); background: transparent;
  cursor: pointer; position: relative; flex-shrink: 0;
  transition: all 0.15s;
}
.card-toggle-chip input[type="checkbox"]:checked {
  background: var(--primary); border-color: var(--primary);
}
.card-toggle-chip input[type="checkbox"]:checked::after {
  content: ''; position: absolute; top: 1.5px; left: 4.5px;
  width: 4px; height: 8px; border: solid white; border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}
.chip-icon { font-size: 14px; line-height: 1; }
</style>
