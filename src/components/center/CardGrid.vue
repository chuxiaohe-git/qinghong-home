<template>
  <div class="card-grid" @click="closeContextMenu">
    <!-- 遍历全部分组 -->
    <template v-for="section in sections" :key="section.group.id">
      <div class="category-title" :id="'group-' + section.group.id">
        <div class="category-title-icon" :style="{ background: getGroupColor(section.group) }">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5">
            <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
            <rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
          </svg>
        </div>
        <h2>{{ section.group.name }}</h2>
        <button v-if="!guestSections" class="add-card-btn" @click.stop="openAdd(section.group)" title="添加收藏">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        </button>
        <button v-if="!guestSections" class="display-mode-btn" @click.stop="toggleDisplayMode(section.group)" :title="section.group.display_mode === 'large' ? '切换为小卡片' : '切换为大卡片'">
          <svg v-if="section.group.display_mode === 'large'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
            <rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
          </svg>
          <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="4" y="4" width="16" height="16" rx="2"/>
            <path d="M9 8h6M9 12h6M9 16h4"/>
          </svg>
        </button>
        <!-- 访客可见切换（仅管理员） -->
        <button v-if="isAdmin && !guestSections" class="eye-btn" :class="{ 'eye-on': section.group.guest_visible }" @click.stop="toggleGuestVisible(section.group)" :title="section.group.guest_visible ? '访客可见' : '访客不可见'">
          <svg v-if="section.group.guest_visible" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
          </svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
            <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
            <line x1="1" y1="1" x2="23" y2="23"/>
          </svg>
        </button>
      </div>

      <div :class="['wrap', section.group.display_mode === 'small' ? 'wrap-small' : '']" :data-group-id="section.group.id">
        <div
          v-for="(bm, idx) in section.bookmarks"
          :key="bm.id"
          :class="[
            section.group.display_mode === 'small' ? 'card-small' : 'card',
          ]"
          :data-bm-id="bm.id"
          :data-group-id="section.group.id"
          :style="{ '--card-color': bm.bg_color || getRandomColor() }"
          @click="openUrl(bm)"
          @contextmenu.prevent="showContextMenu($event, bm)"
        >
          <a :href="bm.url" :target="bm.open_method || '_blank'" @click.prevent>
            <template v-if="section.group.display_mode === 'large'">
              <div class="card-head">
                <div class="icon" :style="{ background: bm.bg_color || getRandomColor() }">
                  <img v-if="bm.icon" :src="getIconUrl(bm.icon)" :alt="bm.title" />
                  <span v-else>{{ bm.title.charAt(0) }}</span>
                </div>
                <span class="title">{{ bm.title }}</span>
              </div>
              <p v-if="bm.description" class="desc" :title="bm.description">{{ bm.description }}</p>
            </template>
            <template v-else>
              <div class="card-small-body">
                <div class="icon-sm" :style="{ background: bm.bg_color || getRandomColor() }">
                  <img v-if="bm.icon" :src="getIconUrl(bm.icon)" :alt="bm.title" />
                  <span v-else>{{ bm.title.charAt(0) }}</span>
                </div>
                <span class="title-sm">{{ bm.title }}</span>
              </div>
            </template>
          </a>
        </div>
      </div>
    </template>

    <!-- 空状态 -->
    <div v-if="sections.length === 0 && !props.search" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text3)" stroke-width="1.5">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
      </svg>
      <p>暂无收藏，请在设置中创建分组再添加</p>
    </div>
    <!-- 搜索无结果 -->
    <div v-else-if="sections.length === 0 && props.search" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text3)" stroke-width="1.5">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
      <p>没有找到匹配「{{ props.search }}」的收藏</p>
    </div>

    <!-- 右键菜单 -->
    <transition name="fade">
      <div
        v-if="ctxMenu.visible"
        class="context-menu"
        :style="{ left: ctxMenu.x + 'px', top: ctxMenu.y + 'px' }"
        @click.stop
      >
        <button class="ctx-item" @click="editBookmark(ctxMenu.bookmark)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          <span>编辑</span>
        </button>
        <button class="ctx-item ctx-danger" @click="deleteBookmark(ctxMenu.bookmark)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            <line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/>
          </svg>
          <span>删除</span>
        </button>
      </div>
    </transition>

    <!-- 添加/编辑弹窗 -->
    <div v-if="showModal" class="modal-overlay">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ isEditing ? '编辑收藏' : '添加收藏' }} — {{ editGroup?.name }}</h3>
          <button class="modal-close" @click="closeModal">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="field"><label>标题</label><input v-model="form.title" class="input" placeholder="收藏名称" /></div>
          <div class="field"><label>链接</label><input v-model="form.url" class="input" placeholder="https://" /></div>
          <div class="field"><label>描述</label><textarea v-model="form.description" class="input textarea" placeholder="选填" rows="3"></textarea></div>
          <div class="field"><label>图标</label>
            <div class="icon-field-container">
              <div class="icon-preview-box" :class="{ 'has-icon': form.icon }" @click="form.icon = ''" title="点击清除图标">
                <img v-if="form.icon" :src="form.icon" alt="" />
                <span v-else class="icon-placeholder">📷</span>
              </div>
              <div class="icon-right-col">
                <input v-model="form.icon" class="input icon-url-input" placeholder="选填，图标链接" />
                <div class="icon-btn-row">
                  <button class="btn-sm" @click="fetchFavicon" :disabled="!form.url" title="从网址获取网站图标">🌐 获取</button>
                  <button class="btn-sm" @click="showIconPicker = true" title="从图标库选择">🎨 图标库</button>
                  <button class="btn-sm" @click="openGalleryPicker" title="从本地图库选择">📂 本地图库</button>
                </div>
              </div>
            </div>
            <!-- 图标库选择浮层（来源选择 + 搜索面板） -->
            <div v-if="showIconPicker || iconSearchActive" class="icon-picker-overlay" @click.self="closeIconPicker">
              <div class="icon-picker-card">
                <!-- 阶段1：选择来源（纯色/彩色） -->
                <template v-if="!iconSearchActive">
                  <div class="icon-picker-option" @click="pickIconSource('vector')">
                    <div class="picker-icon">◇</div>
                    <div class="picker-info">
                      <span class="picker-name">纯色图标</span>
                      <span class="picker-desc">来自 Iconify · 线性矢量图标</span>
                    </div>
                  </div>
                  <div class="icon-picker-option" @click="pickIconSource('color')">
                    <div class="picker-icon picker-icon-color">◆</div>
                    <div class="picker-info">
                      <span class="picker-name">彩色图标</span>
                      <span class="picker-desc">来自 IconArchive · 多彩精美图标</span>
                    </div>
                  </div>
                </template>

                <!-- 阶段2：搜索 + 结果面板 -->
                <template v-else>
                  <div class="icon-panel-header">
                    <span>{{ iconSource === 'vector' ? '纯色图标' : '彩色图标' }} — {{ iconSource === 'vector' ? 'Iconify' : 'IconArchive' }}</span>
                    <button class="btn-sm btn-xs" @click="closeIconPicker" title="返回选择">✕ 关闭</button>
                  </div>
                  <div class="icon-search-bar" @keydown.enter.prevent="doIconSearch">
                    <span class="icon-search-icon">🔍</span>
                    <input
                      v-model="iconSearchText"
                      class="icon-search-input"
                      :placeholder="'输入中文或英文关键词，回车搜索…'"
                    />
                    <button v-if="iconSearchText.trim()" class="btn-sm btn-xs icon-search-clear" @click="clearIconSearch" title="清除搜索">✕</button>
                  </div>
                  <div v-if="iconActualKeyword" class="icon-search-hint">搜索：{{ iconActualKeyword }}</div>
                  <div class="icon-suggestions-header">
                    <span class="icon-match-hint">{{ iconSuggestions.length ? iconSuggestions.length + ' 个' + (iconSource === 'color' ? '彩色' : '纯色') + '图标' : '' }}</span>
                    <button v-if="!iconSearchText.trim()" class="btn-sm btn-xs" @click="refreshIcons" :disabled="matchingIcon" title="换一批">🔄 换一批</button>
                    <button v-else class="btn-sm btn-xs" @click="doIconSearch" :disabled="matchingIcon || !iconSearchText.trim()" title="重新搜索">🔍 搜索</button>
                  </div>
                  <div v-if="matchingIcon && !iconSuggestions.length" class="icon-loading-hint">{{ iconMatchMsg || '搜索中…' }}</div>
                  <div v-else-if="!iconSuggestions.length && iconSearched" class="icon-empty-hint">没有找到相关图标，换个关键词试试</div>
                  <div class="icon-suggestions-grid">
                    <button
                      v-for="(ico, idx) in iconSuggestions"
                      :key="ico.id || idx"
                      class="icon-option"
                      :class="{ active: form.icon === ico.url }"
                      @click="form.icon = ico.url; closeIconPicker()"
                      :title="ico.name"
                    >
                      <img :src="ico.thumbnail || ico.url" :alt="ico.name" width="20" height="20" loading="lazy" />
                    </button>
                  </div>
                </template>
              </div>
            </div>
            <!-- 本地图库选择浮层 -->
            <div v-if="showGalleryPicker" class="gallery-picker-overlay" @click.self="showGalleryPicker = false">
              <div class="gallery-picker-card"
                @dragover.prevent
                @dragenter.prevent="galleryDragOver = true"
                @dragleave.prevent="galleryDragOver = false"
                @drop.prevent="onGalleryDrop($event)"
              >
                <div class="gallery-picker-header">
                  <span>本地图库 · 选择图标</span>
                  <div style="display:flex;gap:8px;align-items:center;">
                    <button class="btn-sm btn-primary" @click="$refs.galleryUploadInput?.click()" :disabled="galleryUploading">
                      {{ galleryUploading ? '上传中...' : '➕ 上传图标' }}
                    </button>
                    <input ref="galleryUploadInput" type="file" accept="image/*" multiple hidden @change="handleGalleryUpload" />
                    <button class="btn-sm" @click="showGalleryPicker = false">✕ 关闭</button>
                  </div>
                </div>
                <!-- 上传区域（空状态或拖拽提示） -->
                <div v-if="galleryDragOver" class="gallery-upload-zone drag-active" @drop.prevent>
                  释放以上传
                </div>
                <div v-if="galleryLoading" class="gallery-loading">加载中...</div>
                <div v-else-if="!galleryImages.length && !galleryUploading" class="gallery-empty">
                  图库暂无图标<br><small style="opacity:0.6;">点击「上传图标」添加，或从设置 → 图库管理</small>
                </div>
                <div v-else class="gallery-grid">
                  <button
                    v-for="(img, idx) in galleryImages"
                    :key="img.id"
                    class="gallery-thumb"
                    :class="{ active: form.icon === getUrl(img) }"
                    :title="img.original_name || img.filename"
                    @click="pickGalleryIcon(img)"
                  >
                    <img :src="getUrl(img)" alt="" loading="lazy" />
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="field">
            <label>背景色</label>
            <div class="color-row">
              <input v-model="form.bg_color" class="input color-input" placeholder="#6C5CE7" />
              <input v-model="form.bg_color" type="color" class="color-picker" />
            </div>
          </div>
          <div class="field">
            <label>打开方式</label>
            <select v-model="form.open_method" class="input">
              <option value="_blank">新窗口</option>
              <option value="_self">当前窗口</option>
            </select>
          </div>
          <p v-if="modalError" class="err-msg">{{ modalError }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeModal">取消</button>
          <button class="btn-primary" :disabled="saving" @click="saveBookmark">
            {{ saving ? '保存中...' : (isEditing ? '保存' : '添加') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useGroupStore } from '@/stores/groups'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'
import { getBookmarks, createBookmark, updateBookmark, deleteBookmark as apiDelete, reorderBookmarks } from '@/api/bookmarks'
import { updateGroup } from '@/api/groups'
import { pinyin } from 'pinyin-pro'
import { getGallery, uploadImage } from '@/api/gallery'
import Sortable from 'sortablejs'

const props = defineProps({
  search: { type: String, default: '' },
  guestSections: { type: Array, default: null },
})

// 获取文本的拼音全拼和首拼（用于模糊搜索）
function getPinyinKeys(text) {
  if (!text) return { full: '', first: '' }
  return {
    full: pinyin(text, { toneType: 'none', type: 'string', separator: '' }).toLowerCase(),
    first: pinyin(text, { pattern: 'first', toneType: 'none', type: 'string', separator: '' }).toLowerCase(),
  }
}

// 转换图标 URL，兼容 Iconify 格式
// iconify:prefix:name -> https://api.iconify.design/prefix/name.svg
function getIconUrl(icon) {
  if (!icon) return ''
  if (icon.startsWith('iconify:')) {
    const parts = icon.replace('iconify:', '').split(':')
    if (parts.length >= 2) {
      return `https://api.iconify.design/${parts[0]}/${parts.slice(1).join(':')}.svg`
    }
  }
  return icon
}

const groupStore = useGroupStore()
const userStore = useUserStore()
const isAdmin = computed(() => userStore.isAdmin)
const allBookmarks = ref([])

// 右键菜单
const ctxMenu = ref({ visible: false, x: 0, y: 0, bookmark: null })

// 弹窗
const showModal = ref(false)
const isEditing = ref(false)
const saving = ref(false)
const modalError = ref('')
const editGroup = ref(null)
const editingId = ref(null)
const form = ref({ title: '', url: '', description: '', icon: '', bg_color: '#6C5CE7', open_method: '_blank' })
const iconSuggestions = ref([])
const matchingIcon = ref(false)
const iconMatchMsg = ref('')
const showIconPicker = ref(false)
const iconSource = ref('vector') // 'vector' | 'color'

// 图标搜索
const iconSearchText = ref('')
const iconSearchActive = ref(false)
const iconActualKeyword = ref('')
const iconSearched = ref(false)

// 本地图库选择
const showGalleryPicker = ref(false)
const galleryImages = ref([])
const galleryLoading = ref(false)
const galleryUploading = ref(false)
const galleryDragOver = ref(false)

// ====== 图标搜索 & 翻译 ======

/** 检测文本是否包含中文字符 */
function containsChinese(text) {
  return /[\u4e00-\u9fa5]/.test(text)
}

/**
 * 翻译中文为英文（MyMemory 免费 API）
 * 英文原样返回，中文自动翻译
 */
async function translateText(text) {
  const t = text.trim().toLowerCase()
  if (!t) return ''
  // 纯英文/数字 → 直接返回
  if (!containsChinese(t)) return t
  try {
    const res = await fetch(`https://api.mymemory.translated.net/get?q=${encodeURIComponent(t)}&langpair=zh|en`)
    const data = await res.json()
    const translated = data?.responseData?.translatedText
    // 如果翻译结果和原文一样（没翻译成功），降级为原文
    if (translated && translated !== t) {
      console.log(`[图标搜索] "${t}" → "${translated}"`)
      return translated.toLowerCase()
    }
    return t
  } catch (e) {
    console.warn('[图标搜索] 翻译失败，使用原文:', e)
    return t
  }
}

/** 执行图标搜索：翻译 + 调用对应接口 */
async function doIconSearch() {
  const text = iconSearchText.value.trim()
  iconSearched.value = true
  if (!text) {
    // 清空搜索时恢复随机模式
    clearIconSearch()
    return
  }
  iconActualKeyword.value = ''
  const keyword = await translateText(text)
  iconActualKeyword.value = keyword
  iconSearchActive.value = true

  if (iconSource.value === 'vector') {
    await fetchVectorIcons(keyword)
  } else {
    await fetchColorIcons(keyword)
  }
}

/** 清除搜索关键词，恢复随机模式 */
function clearIconSearch() {
  iconSearchText.value = ''
  iconActualKeyword.value = ''
  iconSearched.value = false
  // 回到随机模式
  refreshIcons()
}

// 从 URL 提取域名并获取网站图标
async function fetchFavicon() {
  if (!form.value.url) return
  try {
    let urlStr = form.value.url.trim()
    if (!/^https?:\/\//i.test(urlStr)) urlStr = 'https://' + urlStr
    const data = await request.get('/scrape/favicon', { params: { url: urlStr } })
    if (data?.data?.favicon) {
      form.value.icon = data.data.favicon
    }
    iconSuggestions.value = []
    iconMatchMsg.value = ''
  } catch { /* 不做处理 */ }
}

// 随机拉取 Iconify 矢量图标
const iconKeywords = [
  'star', 'heart', 'home', 'user', 'book', 'mail', 'clock', 'cloud',
  'search', 'link', 'image', 'folder', 'map', 'flag', 'bell', 'cog',
  'chart', 'tool', 'globe', 'message', 'photo', 'music', 'video', 'tag',
  'lock', 'key', 'calendar', 'download', 'upload', 'shield', 'fire',
  'light', 'moon', 'sun', 'eye', 'cart', 'gift', 'pen', 'phone',
]

async function fetchVectorIcons(keyword) {
  matchingIcon.value = true
  iconSuggestions.value = []
  iconMatchMsg.value = '加载中...'

  if (keyword && keyword.trim()) {
    // ===== 精准搜索模式 =====
    const q = keyword.trim().toLowerCase()
    try {
      const res = await fetch(`https://api.iconify.design/search?query=${encodeURIComponent(q)}&limit=30`)
      const data = await res.json()
      if (data.icons?.length) {
        const icons = data.icons.map(id => {
          const [prefix, ...nameParts] = id.split(':')
          const name = nameParts.join(':')
          return { id, name: id, url: `https://api.iconify.design/${prefix}/${name}.svg` }
        })
        iconSuggestions.value = icons.slice(0, 30)
        iconMatchMsg.value = ''
      } else {
        iconMatchMsg.value = `未找到「${q}」相关图标`
      }
    } catch {
      iconMatchMsg.value = '搜索失败，请重试'
    }
  } else {
    // ===== 随机模式（原有逻辑） =====
    const shuffled = [...iconKeywords].sort(() => Math.random() - 0.5)
    const words = shuffled.slice(0, 3 + Math.floor(Math.random() * 2))

    const results = await Promise.allSettled(
      words.map(w => fetch(`https://api.iconify.design/search?query=${w}&limit=12`).then(r => r.json()))
    )

    let allIcons = []
    for (const r of results) {
      if (r.status === 'fulfilled' && r.value.icons) {
        allIcons.push(...r.value.icons)
      }
    }

    if (allIcons.length) {
      const unique = [...new Set(allIcons)].sort(() => Math.random() - 0.5).slice(0, 30)
      iconSuggestions.value = unique.map(id => {
        const [prefix, ...nameParts] = id.split(':')
        const name = nameParts.join(':')
        return { id, name: id, url: `https://api.iconify.design/${prefix}/${name}.svg` }
      })
      iconMatchMsg.value = ''
    } else {
      iconMatchMsg.value = '未获取到图标，请重试'
    }
  }
  matchingIcon.value = false
}

// 从后端代理抓取 IconArchive 彩色图标
async function fetchColorIcons(keyword) {
  matchingIcon.value = true
  iconSuggestions.value = []
  iconMatchMsg.value = '加载中...'

  try {
    const params = new URLSearchParams({ source: 'archive' })
    if (keyword && keyword.trim()) {
      params.set('keyword', keyword.trim().toLowerCase())
    }
    const res = await fetch(`/api/scrape/icons?${params.toString()}`)
    const data = await res.json()
    if (data.data?.icons?.length) {
      iconSuggestions.value = data.data.icons
      iconMatchMsg.value = ''
    } else {
      iconMatchMsg.value = keyword ? `未找到「${keyword.trim()}」相关图标` : '未获取到图标，请重试'
    }
  } catch {
    iconMatchMsg.value = '搜索失败，请重试'
  }
  matchingIcon.value = false
}

// 弹出选择浮层 → 选来源后切换到搜索面板
function pickIconSource(source) {
  iconSource.value = source
  // 切换到搜索面板（不关闭弹窗）
  iconSearchActive.value = true
  iconSearchText.value = ''
  iconActualKeyword.value = ''
  iconSearched.value = false
  // 默认加载随机图标
  if (source === 'vector') fetchVectorIcons()
  else fetchColorIcons()
}

/** 关闭图标库面板，重置所有状态 */
function closeIconPicker() {
  showIconPicker.value = false
  iconSearchActive.value = false
  iconSearchText.value = ''
  iconActualKeyword.value = ''
  iconSearched.value = false
  iconSuggestions.value = []
  iconMatchMsg.value = ''
}

// 换一批（清除搜索词，回到随机模式）
function refreshIcons() {
  iconSearchText.value = ''
  iconActualKeyword.value = ''
  iconSearched.value = false
  if (iconSource.value === 'vector') fetchVectorIcons()
  else fetchColorIcons()
}

// 本地图库
function getUrl(img) {
  return img.url || `/uploads/${img.filename}`
}
async function openGalleryPicker() {
  showGalleryPicker.value = true
  galleryLoading.value = true
  galleryImages.value = []
  try {
    const res = await getGallery('icon')
    galleryImages.value = (res.data || []).filter(i => i.image_type === 'icon')
  } catch {}
  galleryLoading.value = false
}
function pickGalleryIcon(img) {
  form.value.icon = getUrl(img)
  showGalleryPicker.value = false
}

const ICON_SIZE = 150

/** 图标上传：大图裁剪为正方形，小图保持原样 */
function maybeResizeIcon(file) {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => {
      const { naturalWidth: w, naturalHeight: h } = img
      if (w <= ICON_SIZE && h <= ICON_SIZE) { resolve(file); return }
      const size = Math.min(w, h)
      const sx = (w - size) / 2
      const sy = (h - size) / 2
      const canvas = document.createElement('canvas')
      canvas.width = ICON_SIZE
      canvas.height = ICON_SIZE
      const ctx = canvas.getContext('2d')
      ctx.drawImage(img, sx, sy, size, size, 0, 0, ICON_SIZE, ICON_SIZE)
      canvas.toBlob((blob) => {
        resolve(blob ? new File([blob], file.name, { type: 'image/png' }) : file)
      }, 'image/png')
    }
    img.onerror = () => resolve(file)
    img.src = URL.createObjectURL(file)
  })
}

async function handleGalleryUpload(e) {
  await doGalleryUpload(e.target.files)
}
async function onGalleryDrop(e) {
  galleryDragOver.value = false
  await doGalleryUpload(e.dataTransfer?.files)
}
async function doGalleryUpload(fileList) {
  if (!fileList?.length) return
  galleryUploading.value = true
  try {
    for (const file of fileList) {
      const resized = await maybeResizeIcon(file)
      const res = await uploadImage(resized, 'icon')
      // 插到列表最前面并自动选中
      galleryImages.value.unshift(res.data)
      form.value.icon = getUrl(res.data)
    }
  } catch (e) {
    alert('上传失败：' + e.message)
  } finally {
    galleryUploading.value = false
  }
}

// 计算每个分组的卡片（支持搜索过滤，含拼音/首拼匹配）
const sections = computed(() => {
  // 访客模式：直接返回传入的数据
  if (props.guestSections) {
    if (!props.search) return props.guestSections
    const q = props.search.trim().toLowerCase()
    return props.guestSections
      .map(s => ({
        ...s,
        bookmarks: s.bookmarks.filter(b => {
          if (b.title.toLowerCase().includes(q)) return true
          if (b.description && b.description.toLowerCase().includes(q)) return true
          if (s.group.name.toLowerCase().includes(q)) return true
          const titlePy = getPinyinKeys(b.title)
          if (titlePy.full.includes(q) || titlePy.first.includes(q)) return true
          return false
        }),
      }))
      .filter(s => s.bookmarks.length > 0 || !q)
  }

  const q = props.search.trim().toLowerCase()
  let filtered = allBookmarks.value
  if (q) {
    filtered = allBookmarks.value.filter(b => {
      // 直接匹配
      if (b.title.toLowerCase().includes(q)) return true
      if (b.description && b.description.toLowerCase().includes(q)) return true
      const group = groupStore.groups.find(g => g.id === b.group_id)
      if (group && group.name.toLowerCase().includes(q)) return true

      // 拼音匹配：全拼 + 首拼
      const titlePy = getPinyinKeys(b.title)
      if (titlePy.full.includes(q) || titlePy.first.includes(q)) return true
      if (b.description) {
        const descPy = getPinyinKeys(b.description)
        if (descPy.full.includes(q) || descPy.first.includes(q)) return true
      }
      if (group) {
        const groupPy = getPinyinKeys(group.name)
        if (groupPy.full.includes(q) || groupPy.first.includes(q)) return true
      }

      return false
    })
  }
  return groupStore.groups
    .map(g => ({
      group: g,
      bookmarks: filtered.filter(b => b.group_id === g.id),
    }))
    .filter(s => !q || s.bookmarks.length > 0)
})

async function loadAll() {
  try {
    const res = await getBookmarks()
    allBookmarks.value = res.data || []
  } catch {
    allBookmarks.value = []
  }
}

// ====== 右键菜单 ======
function showContextMenu(e, bm) {
  const maxX = window.innerWidth - 160
  const maxY = window.innerHeight - 100
  ctxMenu.value = {
    visible: true,
    x: Math.min(e.clientX, maxX),
    y: Math.min(e.clientY, maxY),
    bookmark: bm,
  }
}
function closeContextMenu() {
  ctxMenu.value.visible = false
}

// ====== 编辑 ======
function editBookmark(bm) {
  closeContextMenu()
  isEditing.value = true
  editingId.value = bm.id
  editGroup.value = groupStore.groups.find(g => g.id === bm.group_id) || null
  form.value = {
    title: bm.title,
    url: bm.url,
    description: bm.description || '',
    icon: bm.icon || '',
    bg_color: bm.bg_color || '#6C5CE7',
    open_method: bm.open_method || '_blank',
  }
  modalError.value = ''
  showModal.value = true
}

// ====== 添加 ======
function openAdd(group) {
  closeContextMenu()
  isEditing.value = false
  editingId.value = null
  editGroup.value = group
  form.value = { title: '', url: '', description: '', icon: '', bg_color: getRandomColor(), open_method: '_blank' }
  modalError.value = ''
  showModal.value = true
}

async function toggleDisplayMode(group) {
  const newMode = group.display_mode === 'large' ? 'small' : 'large'
  try {
    const res = await updateGroup(group.id, { display_mode: newMode })
    if (res.code === 0) {
      group.display_mode = newMode
    }
  } catch (e) {
    console.error(e)
  }
}

async function toggleGuestVisible(group) {
  const newVal = !group.guest_visible
  try {
    const res = await updateGroup(group.id, { guest_visible: newVal })
    if (res.code === 0) {
      group.guest_visible = newVal
    }
  } catch (e) {
    console.error(e)
  }
}

// ====== 保存（添加或编辑） ======
async function saveBookmark() {
  modalError.value = ''
  if (!form.value.title.trim()) { modalError.value = '请输入标题'; return }
  if (!form.value.url.trim()) { modalError.value = '请输入链接'; return }
  if (!editGroup.value) { modalError.value = '请选择分组'; return }

  // 自动补全 https://
  let url = form.value.url.trim()
  if (!/^https?:\/\//i.test(url)) url = 'https://' + url
  form.value.url = url

  saving.value = true
  try {
    const data = { ...form.value, group_id: editGroup.value.id }

    if (isEditing.value && editingId.value) {
      const res = await updateBookmark(editingId.value, data)
      const idx = allBookmarks.value.findIndex(b => b.id === editingId.value)
      if (idx >= 0) allBookmarks.value[idx] = res.data
    } else {
      const res = await createBookmark(data)
      allBookmarks.value.push(res.data)
    }

    showModal.value = false
  } catch (e) {
    modalError.value = e.message
  } finally {
    saving.value = false
  }
}

function closeModal() {
  showModal.value = false
}

// ====== 删除 ======
async function deleteBookmark(bm) {
  closeContextMenu()
  if (!confirm(`确定删除「${bm.title}」？`)) return
  try {
    await apiDelete(bm.id)
    allBookmarks.value = allBookmarks.value.filter(b => b.id !== bm.id)
  } catch (e) {
    alert('删除失败：' + e.message)
  }
}

// ====== 打开链接 ======
function openUrl(bm) {
  window.open(bm.url, bm.open_method || '_blank')
}

// ====== 颜色工具 ======

function getRandomColor() {
  const r = Math.floor(Math.random() * 256)
  const g = Math.floor(Math.random() * 256)
  const b = Math.floor(Math.random() * 256)
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
}

const groupColors = ['#4285F4', '#1DA1F2', '#0079BF', '#E4405F', '#5CB85C', '#F48024', '#EC5252', '#2932E1']
function getGroupColor(group) {
  let hash = 0
  for (let i = 0; i < group.name.length; i++) {
    hash = group.name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return groupColors[Math.abs(hash) % groupColors.length]
}

let sortableInstances = []

function initSortable() {
  // 销毁旧实例
  sortableInstances.forEach(s => s.destroy())
  sortableInstances = []

  document.querySelectorAll('.wrap').forEach(wrapEl => {
    // .wrap 的父级 .category-title 才有 data-group-id
    const groupId = wrapEl.closest('.category-title')?.dataset?.groupId
      || wrapEl.closest('[data-group-id]')?.dataset?.groupId
    if (!groupId) return
    const s = new Sortable(wrapEl, {
      group: 'shared-bookmarks',
      animation: 200,
      easing: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
      ghostClass: 'card-ghost',
      chosenClass: 'card-chosen',
      dragClass: 'card-drag',
      placeholderClass: 'card-placeholder',
      onEnd: async (evt) => {
        const toGroupId = evt.to.closest('.category-title')?.dataset?.groupId
          || evt.to.closest('[data-group-id]')?.dataset?.groupId
        if (!toGroupId) return
        const all = [...allBookmarks.value]
        const dragId = parseInt(evt.item.dataset.bmId)
        const dragIdx = all.findIndex(b => b.id === dragId)
        if (dragIdx === -1) return
        const [dragBm] = all.splice(dragIdx, 1)
        dragBm.group_id = parseInt(toGroupId)
        // 根据 evt.to 中的 DOM 顺序计算插入位置
        const siblingEls = [...evt.to.querySelectorAll('[data-bm-id]')]
        const siblingIds = siblingEls.map(el => parseInt(el.dataset.bmId))
        const myNewIdx = siblingIds.indexOf(dragId)
        const newAll = allBookmarks.value.filter(b => b.id !== dragId)
        const insertBeforeId = siblingEls[myNewIdx + 1]?.dataset?.bmId
          ? parseInt(siblingEls[myNewIdx + 1].dataset.bmId)
          : null
        const insertIdx = insertBeforeId != null
          ? newAll.findIndex(b => b.id === insertBeforeId)
          : newAll.length
        newAll.splice(insertIdx, 0, dragBm)
        allBookmarks.value = newAll
        const ids = newAll.filter(b => b.group_id === parseInt(toGroupId)).map(b => b.id)
        reorderBookmarks(parseInt(toGroupId), ids).catch(e => console.error('reorder failed', e))
      },
    })
    sortableInstances.push(s)
  })
}

onMounted(async () => {
  if (!props.guestSections) {
    await groupStore.fetchGroups()
    await loadAll()
  }
  nextTick(() => { initSortable() })
  document.addEventListener('click', closeContextMenu)
})
onUnmounted(() => {
  sortableInstances.forEach(s => s.destroy())
  sortableInstances = []
  document.removeEventListener('click', closeContextMenu)
})

</script>

<style scoped>
.card-grid { flex: 1; }

/* ====== 分类标题 ====== */
.category-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px 0 8px;
  padding: 6px 12px;
  background: color-mix(in srgb, var(--bg-glass) 50%, transparent);
  border-radius: 8px;
  border: 1px solid color-mix(in srgb, var(--border) 50%, transparent);
  position: relative;
  overflow: hidden;
  overflow: hidden;
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
}
.category-title::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(240, 147, 251, 0.3), transparent);
  transition: 0.6s;
  pointer-events: none;
}
:root.light-theme .category-title::after {
  background: linear-gradient(90deg, transparent, rgba(66, 133, 244, 0.2), transparent);
}
.category-title:hover::after {
  left: 100%;
}
.category-title:first-of-type { margin-top: 0; }
.category-title h2 {
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
  background: linear-gradient(45deg, #fff, #b8b8ff, #f093fb, #fad0c4, #a1c4fd);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 10px rgba(240, 147, 251, 0.3);
}
:root.light-theme .category-title h2 {
  background: linear-gradient(45deg, #1a3a7a, #3a6aaa, #5a8ad0, #4a90b0, #5a7aaa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: none;
}
.category-title-icon {
  width: 22px;
  height: 22px;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.add-card-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-glass);
  border: 1px solid var(--border-light);
  border-radius: 6px;
  color: var(--text3);
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
  opacity: 0;
}
.category-title:hover .add-card-btn {
  opacity: 1;
}
.add-card-btn:hover {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}
.add-card-btn svg {
  width: 14px;
  height: 14px;
}

/* ====== 卡片大小切换按钮 ====== */
.display-mode-btn {
  margin-left: 6px; flex-shrink: 0;
  width: 28px; height: 28px;
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--bg-glass); border: 1px solid var(--border);
  border-radius: 6px; cursor: pointer; color: var(--text3); opacity: 0;
  transition: all 0.15s;
}
.category-title:hover .display-mode-btn { opacity: 1; }
.display-mode-btn:hover { background: var(--border); color: var(--text); }
.display-mode-btn svg { width: 14px; height: 14px; }

/* ====== 访客可见按钮（悬停显示，和添加/切换按钮一致）===== */
.eye-btn {
  margin-left: 4px; flex-shrink: 0;
  width: 28px; height: 28px;
  display: inline-flex; align-items: center; justify-content: center;
  background: transparent; border: none;
  border-radius: 6px; cursor: pointer; opacity: 0;
  transition: all 0.15s;
  color: var(--text3);
}
.category-title:hover .eye-btn { opacity: 1; }
.eye-btn:hover { background: var(--bg-glass); }
.eye-on { color: var(--primary) !important; }

/* ====== 卡片网格 ====== */
.wrap {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}
.wrap-small {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(76px, 1fr));
  gap: 6px;
}

/* ====== 卡片 ====== */
.card {
  /* 卡片背景透明度：--card-bg-opacity 0=完全不透明，1=完全透明
     透明度越高，越能看到背景图片/壁纸
     --card-r/g/b: 基础 RGB 颜色
     --card-bg-opacity: 透明度（0=完全不透明，1=完全透明） */
  background: rgba(var(--card-r), var(--card-g), var(--card-b), calc(1 - var(--card-bg-opacity, 0)));
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 10px 14px;
  transition: all 0.2s ease, opacity 0.15s;
  position: relative;
  overflow: hidden;
  cursor: pointer;
}
.card.dragging { opacity: 0.4; transition: none; }
/* SortableJS 占位框：提前显示目标插入位置的空框 */
.card-placeholder {
  background: color-mix(in srgb, var(--primary, #409eff) 8%, transparent) !important;
  border: 2px dashed var(--primary, #409eff) !important;
  border-radius: 12px;
  transition: background 0.15s;
}
.card-small.card-placeholder {
  border-radius: 10px;
  border-width: 1.5px;
}
/* 拖拽镜像（跟随鼠标的卡片）*/
.card-ghost {
  opacity: 0.85;
  transform: rotate(3deg) scale(1.03);
  box-shadow: 0 8px 25px rgba(0,0,0,0.25);
  transition: transform 0.18s, box-shadow 0.18s;
}
/* 选中状态（开始拖拽时源卡片的样式）*/
.card-chosen {
  opacity: 0.9;
  box-shadow: 0 4px 15px rgba(0,0,0,0.18);
}
/* 拖拽进行中 */
.card-drag {
  opacity: 0.5;
}
/* 左上角斜光效，线性渐变从左上到右下淡出 */
.card::after {
  content: '';
  position: absolute;
  top: -60%;
  left: -60%;
  width: 220%;
  height: 220%;
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--card-color) 38%, rgba(255,255,255,0.28)) 0%,
    color-mix(in srgb, var(--card-color) 18%, rgba(255,255,255,0.12)) 40%,
    transparent 70%
  );
  transform: rotate(30deg);
  transition: all 0.4s;
  z-index: 0;
  pointer-events: none;
}
:is(:root.light-theme, .light-theme) .card::after {
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--card-color) 28%, rgba(255,255,255,0.55)) 0%,
    color-mix(in srgb, var(--card-color) 12%, rgba(255,255,255,0.28)) 40%,
    transparent 70%
  );
}
.card:hover::after {
  transform: rotate(30deg) translate(18%, 18%);
}

/* 顶部彩虹条（悬浮时展开） */
.card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(45deg, var(--card-color, #667eea), color-mix(in srgb, var(--card-color, #667eea) 70%, #fff), var(--card-color, #667eea));
  background-size: 300% 300%;
  transform: scaleX(0);
  transition: transform 0.12s;
  z-index: 2;
}
.card:hover::before {
  transform: scaleX(1);
  animation: gradientShift 1.5s ease infinite;
}

/* 悬浮状态 */
.card:hover {
  transform: translateY(-6px);
  border-color: color-mix(in srgb, var(--card-color, #667eea) 35%, var(--border));
  box-shadow:
    0 8px 20px color-mix(in srgb, var(--card-color, #667eea) 15%, transparent),
    0 2px 8px rgba(0,0,0,0.1);
  background: var(--bg-card-hover);
}
:is(:root.light-theme, .light-theme) .card:hover {
  border-color: color-mix(in srgb, var(--card-color, #667eea) 20%, var(--border));
  box-shadow:
    0 8px 20px color-mix(in srgb, var(--card-color, #667eea) 10%, transparent),
    0 2px 8px rgba(0,0,0,0.04);
  background: var(--bg-card-hover);
}
.card a {
  display: flex;
  flex-direction: column;
  text-decoration: none;
  color: inherit;
  position: relative;
  z-index: 1;
}

.card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-shrink: 0;
}
.icon {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #fff;
  font-weight: 700;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
  background: var(--card-color, #667eea);
  box-shadow: 0 0 5px color-mix(in srgb, var(--card-color, #667eea) 40%, transparent);
  transition: all 0.12s;
}
.icon img { width: 100%; height: 100%; object-fit: contain; }
.card:hover .icon {
  box-shadow: 0 0 12px color-mix(in srgb, var(--card-color, #667eea) 60%, transparent);
}
.title {
  font-size: 15px;
  font-weight: 600;
  /* 夜间模式：淡白 + 极淡卡片色阴影，柔和不刺眼 */
  color: rgba(245, 245, 255, 0.88);
  text-shadow: 0 1px 8px color-mix(in srgb, var(--card-color, #667eea) 30%, transparent);
  transition: all 0.12s;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
:is(:root.light-theme, .light-theme) .title {
  /* 白天模式：深色标题，保证在任何背景色上可读 */
  color: #1e2a3a;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
}
.card:hover .title {
  background: linear-gradient(45deg, #fff, color-mix(in srgb, var(--card-color, #f093fb) 60%, #fff), var(--card-color, #f093fb));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
:is(:root.light-theme, .light-theme) .card:hover .title {
  background: linear-gradient(45deg, #1a3a7a, color-mix(in srgb, var(--card-color, #3a6aaa) 70%, #1a3a7a), var(--card-color, #3a6aaa));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.desc {
  font-size: 12px;
  color: var(--text-desc);
  line-height: 1.5;
  min-height: 1.5em; /* 至少1行 */
  max-height: 3em;   /* 最多2行 */
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  text-overflow: ellipsis;
  word-break: break-word;
}

/* ====== 小卡片模式 ====== */
.card-small {
  padding: 6px 4px;
  border-radius: 10px;
  cursor: pointer;
  border: 1px solid transparent;
  background: transparent;
  transition: border-color 0.2s ease;
  position: relative;
  overflow: hidden;
}
.card-small:hover {
  border-color: rgba(var(--card-r), var(--card-g), var(--card-b), 0.2);
}
.card-small.dragging { opacity: 0.4; }
/* SortableJS 小卡片占位框 */
.card-small.card-placeholder {
  border-radius: 10px;
  border-width: 1.5px;
}
.card-small-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-decoration: none;
}
.icon-sm {
  width: 50px; height: 50px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  font-size: 16px; font-weight: 700; color: white;
  position: relative;
  overflow: hidden;
  background: var(--card-color, #667eea);
  box-shadow: 0 0 5px color-mix(in srgb, var(--card-color, #667eea) 40%, transparent);
  transition: all 0.12s;
}
.icon-sm img { width: 100%; height: 100%; object-fit: contain; position: relative; z-index: 1; }
/* 图标左上角斜光效（与大卡片 card-head 一致） */
.icon-sm::after {
  content: '';
  position: absolute;
  top: -60%; left: -60%;
  width: 80%; height: 80%;
  background: linear-gradient(135deg,
    color-mix(in srgb, var(--card-color, #667eea) 38%, rgba(255,255,255,0.28)) 0%,
    color-mix(in srgb, var(--card-color, #667eea) 18%, rgba(255,255,255,0.12)) 40%,
    transparent 80%
  );
  transform: rotate(30deg);
  transition: transform 0.3s ease;
  pointer-events: none;
  z-index: 2;
}
.card-small:hover .icon-sm::after {
  transform: rotate(30deg) translate(18%, 18%);
}
.card-small:hover .icon-sm {
  box-shadow: 0 0 12px color-mix(in srgb, var(--card-color, #667eea) 60%, transparent);
  transform: scale(1.05);
}
.title-sm {
  font-size: 11px;
  color: var(--text);
  text-align: center;
  line-height: 1.3;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  word-break: break-word;
}

/* ====== 右键菜单 ====== */
.context-menu {
  position: fixed;
  z-index: 999;
  width: 140px;
  background: var(--bg-menu);
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: var(--shadow);
  overflow: hidden;
  padding: 6px;
}
.ctx-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  background: none;
  border: none;
  border-radius: 6px;
  color: var(--text2);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.ctx-item:hover {
  background: rgba(255,255,255,0.08);
  color: var(--text);
}
.ctx-danger:hover {
  background: rgba(255, 107, 107, 0.15);
  color: var(--danger);
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

/* ====== 空状态 ====== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  height: 300px;
  color: var(--text3);
  font-size: 14px;
}

/* ====== 弹窗 ====== */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-card {
  width: 420px;
  max-width: 90vw;
  background: var(--bg-modal);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 0;
}
.modal-header h3 { font-size: 16px; font-weight: 700; }
.modal-close {
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  background: var(--bg-glass); border: none; border-radius: 8px; color: var(--text2); cursor: pointer;
}
.modal-close:hover { background: rgba(128,128,128,0.1); }
.modal-body { padding: 20px 24px; display: flex; flex-direction: column; gap: 14px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 13px; color: var(--text2); }
.input {
  width: 100%; padding: 9px 12px; background: var(--bg-input);
  border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-size: 13px;
}
.input:focus { border-color: var(--primary); }
textarea.input {
  resize: vertical;
  min-height: 72px;
  line-height: 1.6;
}
select.input { cursor: pointer; }
.color-row { display: flex; gap: 8px; }
.color-input { flex: 1; }
.color-picker { width: 36px; height: 36px; padding: 2px; border: 1px solid var(--border); border-radius: 8px; background: transparent; cursor: pointer; }
.err-msg { color: var(--danger); font-size: 13px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 0 24px 20px; }
.btn-primary {
  padding: 8px 20px; background: var(--primary); border: none; border-radius: 8px;
  color: white; font-size: 14px; font-weight: 600; cursor: pointer;
}
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-primary:hover:not(:disabled) { opacity: 0.85; }
.btn-cancel {
  padding: 8px 20px; background: transparent; border: 1px solid var(--border);
  border-radius: 8px; color: var(--text2); font-size: 14px; cursor: pointer;
}
.btn-cancel:hover { background: var(--bg-glass); }

/* ====== 图标工具 ====== */
.icon-field-container {
  display: flex;
  gap: 12px;
  align-items: stretch;
}
.icon-preview-box {
  width: 64px; height: 64px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border: 1px dashed var(--border); border-radius: 10px;
  background: var(--bg-input); cursor: pointer;
  overflow: hidden; transition: all 0.15s;
}
.icon-preview-box:hover { border-color: var(--primary); }
.icon-preview-box img { width: 100%; height: 100%; object-fit: contain; padding: 4px; box-sizing: border-box; }
.icon-placeholder { font-size: 22px; opacity: 0.35; }
.icon-right-col {
  flex: 1; display: flex; flex-direction: column; gap: 8px;
}
.icon-url-input { flex: 1; }
.icon-btn-row { display: flex; gap: 8px; }
.btn-sm {
  padding: 0 12px;
  height: 36px;
  white-space: nowrap;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text2);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}
.btn-sm:hover:not(:disabled) {
  background: color-mix(in srgb, var(--primary) 20%, transparent);
  border-color: var(--primary);
  color: var(--text);
}
.btn-sm:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.btn-xs {
  height: 28px;
  padding: 0 10px;
  font-size: 11px;
}
/* ====== 图标库面板头部 ====== */
.icon-panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding-bottom: 8px; margin-bottom: 8px;
  border-bottom: 1px solid var(--border);
  font-size: 13px; font-weight: 600; color: var(--text);
}

.icon-suggestions {
  margin-top: 8px;
  padding: 8px;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 8px;
}
.icon-suggestions-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.icon-suggestions-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-height: 120px;
  overflow-y: auto;
}
.icon-option {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.12s;
  padding: 0;
}
.icon-option:hover {
  border-color: var(--primary);
  background: color-mix(in srgb, var(--primary) 15%, transparent);
}
.icon-option.active {
  border-color: var(--primary);
  background: color-mix(in srgb, var(--primary) 25%, transparent);
  box-shadow: 0 0 0 1px var(--primary);
}
.icon-option img {
  display: block;
}
.icon-match-msg {
  font-size: 12px;
  color: var(--text3);
  margin: 4px 0 0;
}
.icon-match-hint {
  font-size: 11px;
  color: var(--text3);
  width: 100%;
  margin-bottom: 2px;
}

/* ====== 图标搜索框 ====== */
.icon-search-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 8px;
  transition: border-color 0.15s;
}
.icon-search-bar:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary) 20%, transparent);
}
.icon-search-icon {
  font-size: 14px;
  flex-shrink: 0;
  opacity: 0.5;
}
.icon-search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text);
  font-size: 13px;
  padding: 4px 0;
  min-width: 0;
}
.icon-search-input::placeholder {
  color: var(--text3);
  opacity: 0.7;
}
.icon-search-clear {
  width: 22px !important;
  height: 22px !important;
  padding: 0 !important;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: var(--text3);
  font-size: 12px;
  transition: all 0.12s;
  flex-shrink: 0;
}
.icon-search-clear:hover {
  background: rgba(255,255,255,0.1);
  color: var(--text);
}
.icon-search-hint {
  font-size: 11px;
  color: var(--primary);
  margin: 4px 0 2px;
  opacity: 0.8;
}
.icon-loading-hint {
  text-align: center;
  padding: 16px 8px;
  color: var(--text3);
  font-size: 12px;
}
.icon-empty-hint {
  text-align: center;
  padding: 16px 8px;
  color: var(--text3);
  font-size: 12px;
}

/* ====== 图标来源选择浮层 ====== */
.icon-picker-overlay {
  position: fixed;
  inset: 0;
  z-index: 1001;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
}
.icon-picker-card {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: var(--bg-modal);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 12px;
  box-shadow: var(--shadow);
}
.icon-picker-option {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
}
.icon-picker-option:hover {
  border-color: var(--primary);
  background: color-mix(in srgb, var(--primary) 10%, var(--bg-glass));
}
.picker-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: white;
  background: linear-gradient(135deg, #6C5CE7, #00CEC9);
  flex-shrink: 0;
}
.picker-icon-color {
  background: linear-gradient(135deg, #FF6B6B, #FDCB6E, #4facfe);
}
.picker-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.picker-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}
.picker-desc {
  font-size: 12px;
  color: var(--text3);
}

/* ====== 本地图库选择浮层 ====== */
.gallery-picker-overlay {
  position: fixed; inset: 0; z-index: 1001;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
}
.gallery-picker-card {
  width: 580px; max-height: 78vh;
  display: flex; flex-direction: column; gap: 14px;
  background: var(--bg-modal); border: 1px solid var(--border);
  border-radius: 16px; padding: 20px;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.35), 0 0 1px rgba(255,255,255,0.08) inset;
  overflow-y: auto;
}
.gallery-picker-header {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 15px; font-weight: 600; color: var(--text);
}
.gallery-loading, .gallery-empty {
  text-align: center; padding: 36px 0; color: var(--text3); font-size: 13px;
}
.gallery-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
  gap: 10px;
}
.gallery-thumb {
  aspect-ratio: 1;
  display: flex; align-items: center; justify-content: center;
  border: 2px solid transparent; border-radius: 10px;
  background: var(--bg-glass); cursor: pointer; overflow: hidden;
  padding: 6px; box-sizing: border-box; transition: all 0.15s ease;
  position: relative;
}
.gallery-thumb::after {
  content: ''; position: absolute; inset: 0;
  border-radius: 8px;
  transition: all 0.15s ease;
}
.gallery-thumb:hover { border-color: rgba(255,255,255,0.2); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
.gallery-thumb:hover::after { background: rgba(255,255,255,0.05); }
.gallery-thumb.active {
  border-color: var(--primary);
  box-shadow: 0 0 16px color-mix(in srgb, var(--primary) 35%, transparent), 0 4px 12px rgba(0,0,0,0.15);
}
.gallery-thumb img { width: 100%; height: 100%; object-fit: contain; }

/* 图库上传区域 */
.gallery-upload-zone {
  border: 2px dashed var(--border);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  color: var(--text3);
  font-size: 14px;
  background: rgba(128, 128, 128, 0.05);
  transition: all 0.2s ease;
}
.gallery-upload-zone.drag-active {
  border-color: var(--primary);
  background: color-mix(in srgb, var(--primary) 10%, transparent);
  color: var(--primary);
  font-weight: 600;
}
.btn-primary {
  background: var(--primary) !important;
  color: #fff !important;
  border-color: var(--primary) !important;
}
.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}
.btn-primary:disabled {
  opacity: 0.5; cursor: not-allowed;
}

@media (max-width: 768px) {
  .card-grid { padding:8px 0; }
  .wrap { grid-template-columns:repeat(2,1fr); gap:8px; }
  .card { padding:8px; border-radius:8px; }
  .card-icon-wrap { width:32px; height:32px; border-radius:6px; }
  .card-icon { font-size:16px; }
  .card-title { font-size:11px; }
  .card-desc { font-size:10px; }
  .action-btn { padding:3px 8px; font-size:10px; }
}

@media (max-width: 480px) {
  .wrap { grid-template-columns:1fr; gap:6px; }
}
</style>
