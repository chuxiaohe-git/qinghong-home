<template>
  <div class="web-search" v-show="visible">
    <!-- 搜索框主体 -->
    <div class="ws-box">
      <!-- 左侧引擎图标 -->
      <button ref="engineBtnRef" class="ws-engine-btn" @click.stop="togglePicker" :title="'当前: ' + activeEngine.name">
        <img v-if="activeEngine.icon" :src="activeEngine.icon" class="ws-engine-icon" @error="onIconError" />
        <span v-else class="ws-engine-name">{{ activeEngine.name }}</span>
        <svg class="ws-arrow" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
      </button>

      <!-- 搜索输入 -->
      <input
        ref="inputRef"
        v-model="query"
        type="text"
        class="ws-input"
        :placeholder="placeholderText"
        @keydown.enter="doSearch"
        @focus="focused = true"
        @blur="onBlur"
      />

      <!-- 清除按钮 -->
      <button v-if="query" class="ws-clear" @click="query = ''; inputRef?.focus()" title="清除">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>

      <!-- 搜索按钮 -->
      <button class="ws-go" @click="doSearch" title="搜索">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
      </button>
    </div>

    <!-- 引擎选择器弹出面板 -->
    <transition name="ws-fade">
      <div v-if="showPicker" class="ws-picker" :style="pickerStyle" @click.stop>
        <!-- 已添加的引擎列表 -->
        <div class="ws-picker-list">
          <button
            v-for="eng in engines"
            :key="eng.name"
            class="ws-picker-item"
            :class="{ active: eng === activeEngine }"
            @click="selectEngine(eng)"
          >
            <img v-if="eng.icon" :src="eng.icon" class="ws-pick-icon" @error="$event.target.style.display='none'" />
            <span class="ws-pick-name">{{ eng.name }}</span>
            <!-- 删除按钮（至少保留1个时不显示） -->
            <button
              v-if="engines.length > 1"
              class="ws-pick-del"
              title="删除此引擎"
              @click.stop="removeEngine(eng)"
            >×</button>
          </button>
        </div>

        <div class="ws-picker-divider"></div>

        <!-- 添加新引擎 -->
        <button class="ws-picker-add" @click="showAddForm = true; showPicker = false; nextTick(updatePickerPosition)">
          <span>＋</span> 添加搜索引擎
        </button>
      </div>
    </transition>

    <!-- 添加引擎表单 -->
    <transition name="ws-fade">
      <div v-if="showAddForm" class="ws-add-form" :style="addFormStyle" @click.stop>
        <h4 class="ws-form-title">添加搜索引擎</h4>
        <label class="ws-field">
          <span>名称</span>
          <input v-model="form.name" placeholder="例：搜狗" maxlength="20" />
        </label>
        <label class="ws-field">
          <span>图标 URL</span>
          <input v-model="form.icon" placeholder="https://.../favicon.ico（留空用首字）" />
        </label>
        <label class="ws-field">
          <span>搜索地址</span>
          <input v-model="form.url" placeholder="https://example.com/search?q={q}" />
        </label>
        <p class="ws-hint">{q} 会被替换为你的搜索关键词</p>
        <div class="ws-form-actions">
          <button class="ws-btn ws-btn-cancel" @click="showAddForm = false">取消</button>
          <button class="ws-btn ws-btn-ok" @click="addEngine" :disabled="!formValid">添加</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: true },
  initialEngines: { type: Array, default: () => [] }
})

const emit = defineEmits(['engines-change', 'visibility-change'])

// ---- 内置默认引擎 ----
const DEFAULT_ENGINES = [
  { name: '百度', icon: 'https://favicon.im/www.baidu.com', url: 'https://www.baidu.com/s?wd={q}' },
  { name: 'Bing', icon: 'https://favicon.im/cn.bing.com', url: 'https://cn.bing.com/search?q={q}' },
  { name: 'Google', icon: 'https://favicon.im/www.google.com', url: 'https://www.google.com/search?q={q}' },
  { name: 'DuckDuckGo', icon: 'https://favicon.im/duckduckgo.com', url: 'https://duckduckgo.com/?q={q}' },
  { name: '必应国际', icon: 'https://favicon.im/www.bing.com', url: 'https://www.bing.com/search?q={q}' },
]

// ---- 状态 ----
const query = ref('')
const inputRef = ref(null)
const engineBtnRef = ref(null)
const focused = ref(false)
const showPicker = ref(false)
const showAddForm = ref(false)

// 引擎列表
const engines = ref(props.initialEngines && props.initialEngines.length
  ? props.initialEngines
  : [...DEFAULT_ENGINES])

// 当前活跃引擎
const activeEngineName = ref(engines.value[0]?.name || '百度')
const activeEngine = computed(() =>
  engines.value.find(e => e.name === activeEngineName.value) || engines.value[0]
)

const placeholderText = computed(() => `${activeEngine.value.name}一下，你就知道`)

// 选择器动态定位（紧贴引擎按钮下方）
const pickerStyle = ref({})
const addFormStyle = ref({})

// ---- 添加表单 ----
const form = ref({ name: '', icon: '', url: '' })
const formValid = computed(() => {
  return form.value.name.trim() && form.value.url.trim().includes('{q}')
})

// ---- 方法 ----
function togglePicker() {
  showPicker.value = !showPicker.value
  showAddForm.value = false
  if (showPicker.value) updatePickerPosition()
}
function updatePickerPosition() {
  const btn = engineBtnRef.value
  if (!btn) return
  const rect = btn.getBoundingClientRect()
  const parent = btn.closest('.web-search')
  if (!parent) return
  const parentRect = parent.getBoundingClientRect()
  pickerStyle.value = {
    top: (rect.bottom - parentRect.top + 4) + 'px',
    left: rect.left - parentRect.left + 'px',
    transform: 'none'
  }
  addFormStyle.value = { ...pickerStyle.value }
}

function selectEngine(eng) {
  activeEngineName.value = eng.name
  showPicker.value = false
  saveEngines()
}

function removeEngine(eng) {
  const idx = engines.value.indexOf(eng)
  if (idx >= 0) {
    engines.value.splice(idx, 1)
    // 如果删的是当前激活的，切到第一个
    if (activeEngineName.value === eng.name && engines.value.length > 0) {
      activeEngineName.value = engines.value[0].name
    }
    saveEngines()
  }
}

function addEngine() {
  if (!formValid.value) return
  engines.value.push({ ...form.value })
  emit('engines-change', [...engines.value])
  form.value = { name: '', icon: '', url: '' }
  showAddForm.value = false
}

function doSearch() {
  const q = query.value.trim()
  if (!q) return
  const url = activeEngine.value.url.replace('{q}', encodeURIComponent(q))
  window.open(url, '_blank')
  // 不清空查询词，方便用户修改后再次搜索
}

function onBlur() {
  focused.value = false
  // 延迟关闭选择器，让点击事件先触发
  setTimeout(() => {
    if (!showPicker.value && !showAddForm.value) return
    showPicker.value = false
    showAddForm.value = false
  }, 200)
}

function onIconError(e) {
  e.target.style.display = 'none'
}

function saveEngines() {
  emit('engines-change', JSON.parse(JSON.stringify(engines.value)))
}

// ---- 点击外部关闭 ----
function onClickOutside(e) {
  const el = e.target.closest('.web-search')
  if (!el) {
    showPicker.value = false
    showAddForm.value = false
  }
}

onMounted(() => document.addEventListener('mousedown', onClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', onClickOutside))
</script>

<style scoped>
.web-search {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 28px 0 12px;
  position: relative;
}

/* ====== 搜索框 ====== */
.ws-box {
  display: flex;
  align-items: center;
  gap: 0;
  width: 100%;
  max-width: 560px;
  height: 46px;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 3px 3px 3px 4px;
  transition: border-color 0.25s, box-shadow 0.25s;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
.ws-box:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-light), 0 4px 20px rgba(108,92,231,0.15);
}

/* 引擎按钮 */
.ws-engine-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 10px 0 14px;
  height: 100%;
  background: none;
  border: none;
  border-right: 1px solid var(--border-light);
  color: var(--text2);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
  border-radius: 11px 0 0 11px;
  transition: color 0.15s, background 0.15s;
}
.ws-engine-btn:hover { color: var(--text); background: rgba(128,128,128,0.08); }

.ws-engine-icon {
  width: 18px;
  height: 18px;
  object-fit: contain;
}
.ws-engine-name {
  font-size: 13px;
  font-weight: 600;
}
.ws-arrow {
  color: var(--text3);
  flex-shrink: 0;
  margin-left: -2px;
  transition: transform 0.2s;
}
.ws-engine-btn:hover .ws-arrow { transform: translateY(1px); color: var(--text3); }

/* 输入框 */
.ws-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  background: none;
  border: none;
  outline: none;
  color: var(--text);
  font-size: 15px;
  padding: 0 12px;
  letter-spacing: 0.3px;
}
.ws-input::placeholder {
  color: var(--text3);
}

/* 清除按钮 */
.ws-clear {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px; height: 22px;
  background: rgba(128,128,128,0.15);
  border: none;
  border-radius: 50%;
  color: var(--text3);
  cursor: pointer;
  flex-shrink: 0;
  margin-right: 4px;
  transition: all 0.15s;
}
.ws-clear:hover { background: rgba(255,80,80,0.2); color: #ff6b6b; }

/* 搜索按钮 */
.ws-go {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  height: 100%;
  background: var(--primary);
  border: none;
  border-radius: 0 11px 11px 0;
  border-left: 1px solid rgba(255,255,255,0.15);
  margin-left: 4px;
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
  transition: transform 0.15s, box-shadow 0.2s;
}
.ws-go:hover {
  transform: scale(1.06);
  box-shadow: 0 2px 12px rgba(108,92,231,0.4);
}
.ws-go:active { transform: scale(0.95); }

/* ====== 引擎选择器面板 ====== */
.ws-picker {
  position: absolute;
  min-width: 260px;
  max-width: 340px;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 12px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.25);
  z-index: 100;
}
.ws-picker-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.ws-picker-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 10px;
  background: transparent;
  border: none;
  color: var(--text2);
  font-size: 13px;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
  width: 100%;
}
.ws-picker-item:hover { background: rgba(128,128,128,0.1); color: var(--text); }
.ws-picker-item.active {
  background: var(--primary-light);
  color: var(--primary);
  font-weight: 600;
}
.ws-pick-icon {
  width: 18px; height: 18px;
  object-fit: contain;
  flex-shrink: 0;
}
.ws-pick-name {
  flex: 1;
}
.ws-pick-del {
  opacity: 0;
  width: 20px; height: 20px;
  background: rgba(255,80,80,0.1);
  border: none;
  border-radius: 50%;
  color: #ff6b6b;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: opacity 0.15s, background 0.15s;
}
.ws-picker-item:hover .ws-pick-del { opacity: 1; }
.ws-pick-del:hover { background: rgba(255,80,80,0.25); }

.ws-picker-divider {
  height: 1px;
  background: var(--border-light);
  margin: 8px 4px;
}

.ws-picker-add {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 8px;
  border: 1px dashed var(--border);
  border-radius: 10px;
  background: transparent;
  color: var(--text3);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.ws-picker-add:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-light);
}

/* ====== 添加引擎表单 ====== */
.ws-add-form {
  position: absolute;
  width: 320px;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.25);
  z-index: 101;
}
.ws-form-title {
  margin: 0 0 14px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}
.ws-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}
.ws-field span {
  font-size: 12px;
  color: var(--text3);
  font-weight: 500;
}
.ws-field input {
  padding: 9px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text);
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s;
}
.ws-field input:focus {
  border-color: var(--primary);
}
.ws-field input::placeholder { color: var(--text3); }
.ws-hint {
  margin: 0 0 14px;
  font-size: 11px;
  color: var(--text3);
}
.ws-form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.ws-btn {
  padding: 7px 18px;
  border-radius: 8px;
  border: none;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.ws-btn-cancel {
  background: transparent;
  color: var(--text3);
  border: 1px solid var(--border);
}
.ws-btn-cancel:hover { background: rgba(128,128,128,0.1); color: var(--text2); }
.ws-btn-ok {
  background: var(--primary);
  color: #fff;
}
.ws-btn-ok:hover:not(:disabled) { opacity: 0.9; }
.ws-btn-ok:disabled { opacity: 0.35; cursor: not-allowed; }

/* ====== 动画 ====== */
.ws-fade-enter-active,
.ws-fade-leave-active {
  transition: opacity 0.18s, transform 0.18s;
}
.ws-fade-enter-from,
.ws-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
