<template>
  <div class="home" :style="{ transform: `scale(${zoomLevel})`, transformOrigin: 'top left', width: `calc(100vw / ${zoomLevel})`, height: `calc(100vh / ${zoomLevel})` }">
    <div class="animated-bg">
      <div class="bg-wallpaper" :style="bgStyle"></div>
    </div>

    <div class="layout">
      <!-- Left: Sidebar (全高) -->
      <aside class="sidebar">
        <GroupSidebar
          :totalBookmarks="totalBookmarks"
          :bookmarkCounts="bookmarkCounts"
          :activeView="activeView"
          :wikiDocs="wikiDocs"
          :currentWikiDocId="currentWikiDoc?.id"
          @navigate="handleNavigate"
          @select-wiki-doc="selectWikiDoc"
          @create-wiki-doc="createWikiDoc"
          @delete-wiki-doc="deleteWikiDoc"
        />
      </aside>

      <!-- 右侧区域（顶栏 + 内容 + 待办） -->
      <div class="right-area">
        <!-- 顶栏，盖住整个右侧 -->
        <div class="top-bar">
          <div class="top-bar-left">
            <SearchBar @search="handleSearch" />
            <div v-if="!store.isGuest" class="header-lyric">
              <button class="header-lyric-btn" :class="{ playing: playing }" @click="toggleHeaderPlay" :title="playing ? '暂停' : '播放'">
                <svg v-if="!playing" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
              </button>
              <div class="header-lyric-content" v-if="currentLyric || nextLyric">
                <span class="header-lyric-line current">{{ currentLyric || '♪' }}</span>
                <span class="header-lyric-line next" v-if="nextLyric">{{ nextLyric }}</span>
              </div>
              <span class="header-lyric-line current" v-else-if="currentSong">{{ currentSong.title }}</span>
              <span class="header-lyric-placeholder" v-else>♪ 电台随机播放</span>
            </div>
          </div>
          <div class="top-bar-right">
            <div v-if="!store.isGuest" class="greeting-text">{{ greeting }}，<span class="greeting-name">{{ store.nickname }}</span> 👋</div>
            <div v-if="store.isGuest" class="guest-login-btn" @click="goLogin">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
              <span>登录</span>
            </div>
            <div v-if="!store.isGuest" class="top-actions">
            <!-- 切换账号按钮 -->
            <div class="switch-btn-wrap" ref="switchWrapRef">
              <button class="switch-btn" @click="toggleSwitchPopover" title="切换账号">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <circle cx="9" cy="7" r="4"/><path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/><path d="M21 21v-2a4 4 0 0 0-3-3.85"/>
                </svg>
              </button>

              <!-- 切换账号弹窗 -->
              <transition name="fade">
                <div v-if="showSwitchPopover" class="switch-popover">
                  <div class="popover-header">
                    <h3>切换账号</h3>
                    <span class="popover-count">{{ store.recentUsers.length }}</span>
                  </div>
                  <div class="popover-body">
                    <div
                      v-for="u in store.recentUsers"
                      :key="u.username"
                      class="switch-row"
                      :class="{ active: u.username === store.user?.username }"
                      @click="handleSwitchClick(u)"
                    >
                      <div class="sr-avatar">
                        <img v-if="u.avatar" :src="'/uploads/' + u.avatar" />
                        <span v-else>{{ u.nickname.charAt(0) }}</span>
                      </div>
                      <div class="sr-info">
                        <div class="sr-name">{{ u.nickname }}<span v-if="u.username === store.user?.username" class="sr-badge">当前</span></div>
                        <div class="sr-acct">@{{ u.username }}</div>
                      </div>
                      <button class="sr-del" @click.stop="handleDelClick(u)" title="删除记录">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                      </button>
                    </div>
                    <div v-if="store.recentUsers.length === 0" class="popover-empty">暂无其他登录记录</div>
                  </div>
                </div>
              </transition>
            </div>

            <div class="user-dropdown" @click.stop>
              <button class="avatar-btn" @click="showUserMenu = !showUserMenu" :title="store.nickname">
                <img v-if="store.user?.avatar" :src="'/uploads/' + store.user.avatar" class="avatar-img" />
                <span v-else class="avatar-small">{{ store.nickname.charAt(0) }}</span>
              </button>
              <transition name="fade">
                <div v-if="showUserMenu" class="dropdown-menu">
                  <div class="dropdown-header">
                    <span class="dropdown-username">{{ store.nickname }}</span>
                    <span class="dropdown-account">{{ store.user?.username }}</span>
                  </div>
                  <div class="dropdown-body">
                    <button class="dropdown-item" @click="openSettings">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="3"/>
                        <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
                      </svg>
                      <span>设置</span>
                    </button>
                    <div class="dropdown-divider"></div>
                    <button class="dropdown-item" @click="toggleTheme">
                      <svg v-if="isLight" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                      </svg>
                      <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                      </svg>
                      <span>{{ isLight ? '夜间模式' : '白天模式' }}</span>
                    </button>
                    <div class="dropdown-divider"></div>
                    <div class="zoom-controls">
                      <span class="zoom-label">缩放</span>
                      <button class="zoom-btn" @click="zoomOut" title="缩小">−</button>
                      <span class="zoom-value">{{ Math.round(zoomLevel * 100) }}%</span>
                      <button class="zoom-btn" @click="zoomIn" title="放大">+</button>
                      <button class="zoom-btn zoom-reset" @click="zoomReset" title="重置">⟲</button>
                    </div>
                    <div class="dropdown-divider"></div>
                    <button class="dropdown-item" @click="logout">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                        <polyline points="16 17 21 12 16 7"/>
                        <line x1="21" y1="12" x2="9" y2="12"/>
                      </svg>
                      <span>退出登录</span>
                    </button>
                  </div>
                </div>
              </transition>
            </div>
          </div>
          </div>
        </div>
        <!-- 下面内容 + 待办 -->
        <div class="right-body">
          <!-- 右侧：所有内容一起滚动 -->
          <main class="main">
            <!-- 网络搜索（仅 bookmarks 视图显示） -->
            <WebSearch
              v-if="activeView === 'bookmarks'"
              :visible="!isCardHidden('websearch')"
              :initialEngines="searchEngines"
              @engines-change="onSearchEnginesChange"
            />

            <!-- 仪表板（可拖拽排序） -->
            <div v-if="!store.isGuest" class="dashboard" :style="activeView !== 'bookmarks' ? 'display:none' : ''"
              @dragover.prevent="onDragOver" @drop="onDrop">
            <div v-if="!isCardHidden('quote')" class="dash-card dash-quote" data-card="quote" :style="{ order: cardIdx('quote') }"
              @contextmenu.prevent="openQuoteMenu">
              <div class="drag-grip" draggable="true"
                @dragstart="onDragStart($event, 'quote')" @dragend="onDragEnd">⠿</div>
              <button class="dash-close-btn" title="隐藏此卡片" @click.stop="hideCard('quote')">×</button>
              <div class="quote-text">{{ quoteText }}</div>
                <div class="quote-from" v-if="quoteFrom">—— {{ quoteFrom }}</div>
              </div>
            <!-- 一言右键菜单 -->
            <div v-if="quoteMenu.show" class="ctx-menu-fixed" :style="quoteMenu.style">
              <button class="ctx-item-fixed" @click="doRefreshQuote">🔄 换一句</button>
              <button class="ctx-item-fixed" @click="doToggleAuto">{{ quoteAuto ? '⏹ 停止自动' : '▶️ 自动播放' }}</button>
            </div>
              <div v-if="!isCardHidden('clock')" class="dash-card" data-card="clock" :style="{ order: cardIdx('clock') }"
                >
                <div class="drag-grip" draggable="true"
                  @dragstart="onDragStart($event, 'clock')" @dragend="onDragEnd">⠿</div>
                <button class="dash-close-btn" title="隐藏此卡片" @click.stop="hideCard('clock')">×</button>
                <DashClock @ctxopen="closeQuoteMenu" />
              </div>
              <div v-if="!isCardHidden('game')" class="dash-card" data-card="game" :style="{ order: cardIdx('game') }"
                >
                <div class="drag-grip" draggable="true"
                  @dragstart="onDragStart($event, 'game')" @dragend="onDragEnd">⠿</div>
                <button class="dash-close-btn" title="隐藏此卡片"
                  @mousedown.stop.prevent @touchstart.stop.prevent @click.stop="hideCard('game')">×</button>
                <DashGame />
              </div>
              <div v-if="!isCardHidden('music')" class="dash-card" data-card="music" :style="{ order: cardIdx('music') }"
                >
                <div class="drag-grip" draggable="true"
                  @dragstart="onDragStart($event, 'music')" @dragend="onDragEnd">⠿</div>
                <button class="dash-close-btn" title="隐藏此卡片" @click.stop="hideCard('music')">×</button>
                <DashMusic />
              </div>
              <div v-if="!isCardHidden('food')" class="dash-card" data-card="food" :style="{ order: cardIdx('food') }"
                >
                <div class="drag-grip" draggable="true"
                  @dragstart="onDragStart($event, 'food')" @dragend="onDragEnd">⠿</div>
                <button class="dash-close-btn" title="隐藏此卡片" @click.stop="hideCard('food')">×</button>
                <DashFood />
              </div>
            </div>
            <!-- 收藏内容 -->
            <div v-if="activeView === 'bookmarks' || store.isGuest" class="content-area">
              <CardGrid :search="searchQuery" :guestSections="store.isGuest ? guestSections : null" />
            </div>

            <!-- 摸鱼日历 -->
            <div v-if="!store.isGuest && activeView === 'todo-calendar'" class="cal-wrapper">
              <CalendarView v-if="!isMobile" :refreshKey="calendarRefreshKey" @todo-changed="onCalendarTodoChanged" />
              <MobileCalendarView v-else />
            </div>

            <!-- 摸鱼笔记 -->
            <div v-if="!store.isGuest && activeView === 'scratch-note'" class="cal-wrapper">
              <ScratchNote @todo-changed="onTodoChanged" />
            </div>

            <!-- AI 对话 -->
            <div v-if="activeView === 'ai-chat'" class="ai-wrapper">
              <AIChat />
            </div>

            <!-- 摸鱼WIKI -->
            <div v-if="!store.isGuest && activeView === 'wiki'" class="cal-wrapper">
              <WikiPanel
                :currentDoc="currentWikiDoc"
                :wikiDocs="wikiDocs"
                @close-doc="closeWikiDoc"
                @doc-updated="onWikiDocUpdated"
                @doc-deleted="onWikiDocDeleted"
                @select-doc="selectWikiDoc"
                @create-wiki-doc="createWikiDoc"
              />
            </div>

            <!-- 其他页面（便签/统计）显示黑板 -->
            <NotesView v-if="!store.isGuest && activeView !== 'bookmarks' && activeView !== 'todo-calendar' && activeView !== 'scratch-note' && activeView !== 'ai-chat' && activeView !== 'wiki'" />
          </main>
          <aside v-if="!store.isGuest && showTodo" class="todo-sidebar">
            <TodoPanel :refreshKey="todoRefreshKey" @todo-changed="onTodoChanged" @jump-to-note="onJumpToNote" @close="showTodo = false" />
          </aside>
          <button v-if="!store.isGuest && !showTodo" class="todo-reopen" @click="showTodo = true" title="展开待办">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 移动端底部导航 -->
    <nav class="mobile-bottom-nav">
      <button class="mb-item" :class="{active: activeMobileTab==='bookmarks'}" @click="switchMobileTab('bookmarks')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
        <span>收藏</span>
      </button>
      <button class="mb-item" :class="{active: activeMobileTab==='calendar'}" @click="switchMobileTab('calendar')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        <span>日历</span>
      </button>
      <button class="mb-item" :class="{active: activeMobileTab==='note'}" @click="switchMobileTab('note')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        <span>笔记</span>
      </button>
      <button class="mb-item" :class="{active: activeMobileTab==='game'}" @click="switchMobileTab('game')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 12h4M8 10v4"/><rect x="2" y="6" width="20" height="12" rx="3"/><circle cx="16" cy="10" r="1"/><circle cx="18" cy="12" r="1"/></svg>
        <span>暴打BOSS</span>
      </button>
    </nav>

    <MobileGameView v-if="showGame" @close="showGame = false" />

    <SettingsModal v-if="showSettings" @close="showSettings = false" />

    <!-- 全屏闹铃 -->
    <AlarmOverlay
      :show="alarmShow"
      :todo="alarmTodo"
      @dismiss="alarmDismiss"
      @snooze="alarmSnooze"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useGroupStore } from '@/stores/groups'
import { getSettings, updateSettings } from '@/api/settings'
import { getBookmarks } from '@/api/bookmarks'
import { getGuestGroups } from '@/api/guest'
import { getTodos } from '@/api/todo'
import GroupSidebar from '@/components/sidebar/GroupSidebar.vue'
import SearchBar from '@/components/center/SearchBar.vue'
import CardGrid from '@/components/center/CardGrid.vue'
import WebSearch from '@/components/center/WebSearch.vue'
import NotesView from '@/components/center/NotesView.vue'
import CalendarView from '@/components/calendar/CalendarView.vue'
import MobileCalendarView from '@/components/calendar/MobileCalendarView.vue'
import MobileGameView from '@/components/game/MobileGameView.vue'
import DashClock from '@/components/center/DashClock.vue'
import DashMusic from '@/components/center/DashMusic.vue'
import DashFood from '@/components/center/DashFood.vue'
import DashGame from '@/components/center/DashGame.vue'
import ScratchNote from '@/components/center/ScratchNote.vue'
import WikiPanel from '@/components/center/WikiPanel.vue'
import TodoPanel from '@/components/todo/TodoPanel.vue'
import { playing, currentSong, lyrics, currentTime, audioEl } from '@/composables/useMusicPlayer'
import SettingsModal from '@/components/settings/SettingsModal.vue'
import AlarmOverlay from '@/components/calendar/AlarmOverlay.vue'
import { useReminder } from '@/composables/useReminder'
import { useScratchNoteStore } from '@/stores/scratch-note'
import AIChat from '@/components/center/AIChat.vue'

const router = useRouter()
const store = useUserStore()
const groupStore = useGroupStore()
const scratchNoteStore = useScratchNoteStore()

const showSettings = ref(false)
const showGame = ref(false)
const showSwitchPopover = ref(false)
const switchWrapRef = ref(null)
const showTodo = ref(true)
const showUserMenu = ref(false)
const todoRefreshKey = ref(0)
const calendarRefreshKey = ref(0)

// ── 移动端判断 ──
const isMobile = ref(window.innerWidth <= 768)
function checkMobile() { isMobile.value = window.innerWidth <= 768 }
onMounted(() => window.addEventListener('resize', checkMobile))
onUnmounted(() => window.removeEventListener('resize', checkMobile))

// ── 移动端适配 ──
const activeMobileTab = ref('bookmarks')
function switchMobileTab(tab) {
  activeMobileTab.value = tab
  if (tab === 'bookmarks') { activeView.value = 'bookmarks'; showTodo.value = false }
  else if (tab === 'calendar') { activeView.value = 'todo-calendar'; showTodo.value = false }
  else if (tab === 'note') { activeView.value = 'scratch-note'; showTodo.value = false }
  else if (tab === 'game') { showGame.value = true }
}

function onCalendarTodoChanged() {
  todoRefreshKey.value++
}

function onTodoChanged() {
  calendarRefreshKey.value++
  todoRefreshKey.value++
  window.dispatchEvent(new CustomEvent('scratch-note-refresh-highlights'))
}

function onAiActionDone() {
  todoRefreshKey.value++
  calendarRefreshKey.value++
}

function onJumpToNote({ noteId, notebookId, isNotebook }) {
  // 切换到 scratch-note 视图
  activeView.value = 'scratch-note'
  // 异步切换笔记本并打开笔记/目录
  ;(async () => {
    if (notebookId && notebookId !== scratchNoteStore.currentNotebookId) {
      await scratchNoteStore.switchNotebook(notebookId)
    }
    if (noteId) {
      // 通过 store 传递跳转目标，避免事件时序问题
      scratchNoteStore.pendingOpenNoteId = noteId
    } else if (isNotebook && notebookId) {
      // 跳转到笔记本目录页
      scratchNoteStore.pendingOpenNoteId = 'directory'
    }
  })()
}

// ── 提醒系统 ──
const { showAlarm: alarmShow, currentAlarm: alarmTodo, dismissAlarm: alarmDismiss, snoozeAlarm: alarmSnooze } = useReminder()
const activeView = ref('bookmarks')

// ── WIKI 状态管理 ──
const wikiDocs = ref([])
const currentWikiDoc = ref(null)

async function loadWikiDocs() {
  const { getWikiDocs } = await import('@/api/wiki')
  const res = await getWikiDocs()
  if (res.code === 0) wikiDocs.value = res.data || []
}
async function selectWikiDoc(id) {
  activeView.value = 'wiki'
  const { getWikiDoc } = await import('@/api/wiki')
  const res = await getWikiDoc(id)
  if (res.code === 0) currentWikiDoc.value = res.data
}
async function createWikiDoc() {
  const { createWikiDoc } = await import('@/api/wiki')
  const title = prompt('请输入文档标题：')
  if (!title?.trim()) return
  const res = await createWikiDoc(title.trim(), '# 欢迎\n\n开始编写你的文档...')
  if (res.code === 0) {
    wikiDocs.value.unshift(res.data)
    activeView.value = 'wiki'
    currentWikiDoc.value = res.data
  }
}
async function deleteWikiDoc(id) {
  if (!confirm('确定删除此文档？')) return
  const { deleteWikiDoc } = await import('@/api/wiki')
  await deleteWikiDoc(id)
  wikiDocs.value = wikiDocs.value.filter(d => d.id !== id)
  if (currentWikiDoc.value?.id === id) currentWikiDoc.value = null
}
function closeWikiDoc() { currentWikiDoc.value = null }
function onWikiDocUpdated(updated) {
  const idx = wikiDocs.value.findIndex(d => d.id === updated.id)
  if (idx !== -1) wikiDocs.value[idx] = { ...wikiDocs.value[idx], ...updated }
  if (currentWikiDoc.value?.id === updated.id) currentWikiDoc.value = { ...currentWikiDoc.value, ...updated }
}
function onWikiDocDeleted(id) {
  wikiDocs.value = wikiDocs.value.filter(d => d.id !== id)
  currentWikiDoc.value = null
}

// 仪表板卡片拖拽排序
const DEFAULT_CARD_ORDER = ['quote', 'clock', 'game', 'music', 'food']
const cardOrder = ref([...DEFAULT_CARD_ORDER])
// 卡片隐藏状态（存的是被隐藏的卡片名数组，空=全显示）
const hiddenCards = ref(JSON.parse(localStorage.getItem('dash_hidden_cards') || '[]'))
// 网络搜索引擎列表
const searchEngines = ref([])
let dragCard = null

function cardIdx(name) { return cardOrder.value.indexOf(name) }
function isCardHidden(name) { return hiddenCards.value.includes(name) }
function hideCard(name) {
  if (!hiddenCards.value.includes(name)) {
    hiddenCards.value.push(name)
    saveHiddenCards()
  }
}
function showCard(name) {
  const idx = hiddenCards.value.indexOf(name)
  if (idx >= 0) {
    hiddenCards.value.splice(idx, 1)
    saveHiddenCards()
  }
}
function saveHiddenCards() {
  localStorage.setItem('dash_hidden_cards', JSON.stringify(hiddenCards.value))
  updateSettings({
    layout_config: JSON.stringify({ ...bgConfig.value, card_order: cardOrder.value, hidden_cards: [...hiddenCards.value], search_engines: [...searchEngines.value] })
  }).catch(() => {})
  // 通知设置面板同步
  window.dispatchEvent(new CustomEvent('dashboard-cards-changed', { detail: { hiddenCards: [...hiddenCards.value] } }))
}
// 搜索引擎变更（用户添加/删除了引擎）
function onSearchEnginesChange(engines) {
  searchEngines.value = engines
  // 立即持久化
  updateSettings({
    layout_config: JSON.stringify({ ...bgConfig.value, card_order: cardOrder.value, hidden_cards: [...hiddenCards.value], search_engines: engines })
  }).catch(() => {})
}
function saveCardOrder() {
  // 保存到后端
  updateSettings({ layout_config: JSON.stringify({ ...bgConfig.value, card_order: cardOrder.value, hidden_cards: [...hiddenCards.value], search_engines: [...searchEngines.value] }) }).catch(() => {})
}
function onDragStart(e, name) {
  dragCard = name; e.target.closest('.dash-card')?.classList.add('dragging')
}
function onDragOver(e) {
  const t = e.target.closest('.dash-card'); if (!t || !dragCard) return
  const n = t.dataset.card; if (!n || n === dragCard) return
  let a = cardOrder.value.indexOf(dragCard), b = cardOrder.value.indexOf(n)
  if (a === -1 || b === -1) return
  cardOrder.value.splice(a, 1); cardOrder.value.splice(b, 0, dragCard); saveCardOrder()
}
function onDragEnd(e) { e.target.closest('.dash-card')?.classList.remove('dragging'); dragCard = null }
function onDrop(e) { e.preventDefault(); dragCard = null }

const isLight = ref(document.documentElement.classList.contains('light-theme'))
const bgConfig = ref({ bgColor: '', wallpaperIds: [], carouselEnabled: false, interval: 1 })
const bgStyle = ref({})
const wallpaperIndex = ref(0)
const totalBookmarks = ref(0)
const incompleteTodos = ref(0)
const bookmarkCounts = ref({})
const searchQuery = ref('')
const quoteText = ref('')
const quoteFrom = ref('')
const quoteAuto = ref(false)
const quoteMenu = ref({ show: false, style: {} })
let carouselTimer = null
let quoteTimer = null

function openQuoteMenu(e) {
  // 通知时钟关闭右键菜单
  window.dispatchEvent(new CustomEvent('close-clock-ctx'))
  quoteMenu.value = {
    show: true,
    style: {
      left: Math.min(e.clientX, window.innerWidth - 140) + 'px',
      top: Math.min(e.clientY, window.innerHeight - 80) + 'px',
    }
  }
}
function closeQuoteMenu() { quoteMenu.value.show = false }
function doRefreshQuote() { fetchQuote(); closeQuoteMenu() }
function doToggleAuto() {
  quoteAuto.value = !quoteAuto.value
  if (quoteAuto.value) {
    doRefreshQuote()
    quoteTimer = setInterval(fetchQuote, 300000)  // 5 分钟
  } else {
    clearInterval(quoteTimer)
    quoteTimer = null
  }
  closeQuoteMenu()
}

async function fetchQuote() {
  // 随机选：正经一言 vs 毒鸡汤
  if (Math.random() > 0.5) {
    try {
      const res = await fetch('https://v2.xxapi.cn/api/dujitang')
      const data = await res.json()
      if (data.code === 200 && data.data) {
        quoteText.value = data.data
        quoteFrom.value = '💊 毒鸡汤'
        return
      }
    } catch {}
  }
  try {
    const res = await fetch('https://v1.hitokoto.cn/')
    const data = await res.json()
    quoteText.value = data.hitokoto
    quoteFrom.value = data.from_who || data.from || ''
  } catch {
    quoteText.value = '一言难尽，稍后再试'
    quoteFrom.value = ''
  }
}

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return '早上好'
  if (h < 18) return '下午好'
  return '晚上好'
})

// 顶栏播放/暂停控制
function toggleHeaderPlay() {
  const a = audioEl.value
  if (!a) return
  if (currentSong.value && playing.value) {
    a.pause()
    playing.value = false
  } else if (currentSong.value) {
    a.play().then(() => { playing.value = true }).catch(() => {})
  }
  // 无歌时按钮不响应（UI上保持不可用状态即可）
}

// 当前歌词行 + 下一行
const currentLyric = computed(() => {
  if (!lyrics.value.length) return ''
  let line = ''
  for (const l of lyrics.value) {
    if (l.time <= currentTime.value) line = l.text
  }
  return line
})
const currentLyricIdx = computed(() => {
  let idx = -1
  for (let i = 0; i < lyrics.value.length; i++) {
    if (lyrics.value[i].time <= currentTime.value) idx = i
  }
  return idx
})
const nextLyric = computed(() => {
  const idx = currentLyricIdx.value
  if (idx < 0 || idx >= lyrics.value.length - 1) return ''
  return lyrics.value[idx + 1].text
})

// 加载背景配置
async function loadBgConfig() {
  try {
    const res = await getSettings()
    const cfg = res.data?.layout_config
    if (cfg) {
      const parsed = typeof cfg === 'string' ? JSON.parse(cfg) : cfg
      bgConfig.value = parsed
      applyBg(parsed)
      startCarousel(parsed)
      // 从数据库恢复卡片排序
      if (parsed.card_order && Array.isArray(parsed.card_order) && parsed.card_order.length === DEFAULT_CARD_ORDER.length) {
        cardOrder.value = parsed.card_order
      }
      // 从数据库恢复隐藏卡片状态
      if (parsed.hidden_cards && Array.isArray(parsed.hidden_cards)) {
        hiddenCards.value = parsed.hidden_cards
        localStorage.setItem('dash_hidden_cards', JSON.stringify(parsed.hidden_cards))
      }
      // 从数据库恢复导航显隐状态
      if (parsed.hidden_nav && Array.isArray(parsed.hidden_nav)) {
        localStorage.setItem('hidden_nav', JSON.stringify(parsed.hidden_nav))
      }
      // 从数据库恢复搜索引擎列表
      if (parsed.search_engines && Array.isArray(parsed.search_engines) && parsed.search_engines.length > 0) {
        searchEngines.value = parsed.search_engines
      }
      return
    }
  } catch {}
}

function applyBg(cfg) {
  const bg = document.querySelector('.animated-bg')
  if (!bg) return
  // 确定当前主题并取对应颜色
  const isLight = document.documentElement.classList.contains('light-theme')
  const color = isLight ? (cfg.bgColorLight || '#eef2ff') : (cfg.bgColorDark || '#1a1a2e')

  if (color) {
    if (color.length !== 7) return
    // 如果是默认色，清除自定义样式让 CSS 兜底
    if ((isLight && color === '#eef2ff') || (!isLight && color === '#1a1a2e')) {
      bg.style.background = ''
      bg.style.backgroundSize = ''
      bg.style.backgroundPosition = ''
      bg.style.backgroundRepeat = ''
      document.documentElement.style.removeProperty('--bg')
      document.documentElement.style.removeProperty('--bg-dark')
      return
    }
    const r = parseInt(color.slice(1,3), 16)
    const g = parseInt(color.slice(3,5), 16)
    const b = parseInt(color.slice(5,7), 16)
    if (isLight) {
      // 浅色模式：不动光晕，改 body 的 --bg
      bg.style.background = ''
      bg.style.backgroundSize = ''
      bg.style.backgroundPosition = ''
      bg.style.backgroundRepeat = ''
      const c1 = `rgb(${Math.round(r*0.7)},${Math.round(g*0.7)},${Math.round(b*0.7)})`
      const c2 = color
      const c3 = `rgb(${Math.min(255,r+30)},${Math.min(255,g+30)},${Math.min(255,b+30)})`
      document.documentElement.style.setProperty('--bg', `linear-gradient(135deg, ${c1}, ${c2}, ${c3})`)
    } else {
      // 暗色模式：一样不动光晕，改 --bg-dark
      bg.style.background = ''
      bg.style.backgroundSize = ''
      bg.style.backgroundPosition = ''
      bg.style.backgroundRepeat = ''
      const dark = `rgb(${Math.round(r*0.08)},${Math.round(g*0.08)},${Math.round(b*0.08)})`
      const mid = `rgb(${Math.round(r*0.15)},${Math.round(g*0.15)},${Math.round(b*0.15)})`
      document.documentElement.style.setProperty('--bg-dark', `linear-gradient(135deg, ${dark}, ${mid}, ${color})`)
    }
  }
}

function startCarousel(cfg) {
  stopCarousel()
  if (!cfg.wallpaperIds || cfg.wallpaperIds.length === 0) {
    bgStyle.value = {} // 清除壁纸，回到纯色背景
    return
  }
  
  const t = Date.now()
  bgStyle.value = { backgroundImage: `url(/api/gallery/${cfg.wallpaperIds[0]}/file?t=${t})` }

  if (cfg.carouselEnabled && cfg.wallpaperIds.length >= 2) {
    wallpaperIndex.value = 0
    carouselTimer = setInterval(() => {
      wallpaperIndex.value = (wallpaperIndex.value + 1) % cfg.wallpaperIds.length
      const id = cfg.wallpaperIds[wallpaperIndex.value]
      bgStyle.value = { backgroundImage: `url(/api/gallery/${id}/file?t=${Date.now()})` }
    }, (cfg.interval || 1) * 60 * 1000)
  }
}

function stopCarousel() {
  if (carouselTimer) {
    clearInterval(carouselTimer)
    carouselTimer = null
  }
}

function handleBgUpdate(e) {
  const cfg = e.detail
  bgConfig.value = cfg
  applyBg(cfg)
  startCarousel(cfg)
}

async function loadCounts() {
  try {
    const [bmRes, todoRes] = await Promise.all([getBookmarks(), getTodos()])
    const bms = bmRes.data || []
    const todos = todoRes.data || []
    totalBookmarks.value = bms.length
    incompleteTodos.value = todos.filter(t => !t.done).length
    // 计算每个分组的数量
    const counts = {}
    bms.forEach(b => { counts[b.group_id] = (counts[b.group_id] || 0) + 1 })
    bookmarkCounts.value = counts
  } catch {}
}

// 访客模式数据
const guestSections = ref([])
async function loadGuestData() {
  try {
    const res = await getGuestGroups()
    guestSections.value = res.data || []
    // 填充侧边栏所需数据
    const guestGroups = (res.data || []).map(s => s.group)
    groupStore.groups = guestGroups
    const counts = {}
    for (const s of (res.data || [])) {
      counts[s.group.id] = s.bookmarks.length
    }
    bookmarkCounts.value = counts
  } catch {
    guestSections.value = []
  }
}

function handleSearch(q) {
  searchQuery.value = q
}

function handleNavigate(view) {
  activeView.value = view
  if (view === 'wiki') loadWikiDocs()
  if (view !== 'wiki') currentWikiDoc.value = null
}

// 主题切换
function toggleTheme() {
  document.documentElement.classList.toggle('light-theme')
  isLight.value = document.documentElement.classList.contains('light-theme')
  showUserMenu.value = false
  localStorage.setItem('theme', isLight.value ? 'light' : 'dark')
  updateSettings({ theme: isLight.value ? 'light' : 'dark' }).catch(() => {})
  // 主题切换后重新应用背景颜色
  if (bgConfig.value) applyBg(bgConfig.value)
}

// ── 页面缩放 ──
const zoomLevel = ref(parseFloat(localStorage.getItem('page_zoom') || '1'))
function applyZoom() {
  localStorage.setItem('page_zoom', String(zoomLevel.value))
}
const zoomSteps = [0.75, 0.85, 1, 1.15, 1.25]
function zoomIn() {
  const i = zoomSteps.findIndex(s => s > zoomLevel.value + 0.01)
  if (i >= 0) zoomLevel.value = zoomSteps[i]
  else zoomLevel.value = Math.min(zoomLevel.value + 0.1, 1.5)
  applyZoom()
}
function zoomOut() {
  const steps = [...zoomSteps].reverse()
  const i = steps.findIndex(s => s < zoomLevel.value - 0.01)
  if (i >= 0) zoomLevel.value = steps[i]
  else zoomLevel.value = Math.max(zoomLevel.value - 0.1, 0.5)
  applyZoom()
}
function zoomReset() { zoomLevel.value = 1; applyZoom() }

function openSettings() {
  showUserMenu.value = false
  showSettings.value = true
}

function toggleSwitchPopover() {
  if (store.recentUsers.length > 0) {
    showSwitchPopover.value = !showSwitchPopover.value
  } else {
    store.logout()
    router.push('/login')
  }
}

function handleSwitchClick(u) {
  if (u.username === store.user?.username) return
  showSwitchPopover.value = false
  store.switchToUser(u)
}

function goLogin() {
  router.push('/login')
}

function handleDelClick(u) {
  store.removeRecentUser(u.username)
}

function logout() {
  store.logout()
  router.push('/login')
}

function closeMenu(e) {
  if (showUserMenu.value) showUserMenu.value = false
  if (showSwitchPopover.value) {
    // 点击 popover 内部不关闭
    if (switchWrapRef.value && switchWrapRef.value.contains(e.target)) return
    showSwitchPopover.value = false
  }
  if (quoteMenu.value.show) quoteMenu.value.show = false
}

onMounted(async () => {
  // 应用页面缩放
  applyZoom()
  // 恢复主题（默认白天模式）
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme !== 'dark') {
    document.documentElement.classList.add('light-theme')
    isLight.value = true
  }
  if (store.token) {
    await store.fetchUser()
  }
  if (store.isGuest) {
    // 访客模式：只加载可见分组
    await loadGuestData()
  } else {
    await groupStore.fetchGroups()
    await loadBgConfig()
    await loadCounts()
    fetchQuote()
  }
  window.addEventListener('bg-update', handleBgUpdate)
  function onDashCardsChanged(e) {
    if (e.detail && Array.isArray(e.detail.hiddenCards)) {
      hiddenCards.value = e.detail.hiddenCards
    }
  }
  window.addEventListener('dashboard-cards-changed', onDashCardsChanged)
  document.addEventListener('click', closeMenu)
  // AI 操作完成后刷新待办和收藏
  window.addEventListener('ai-action-done', onAiActionDone)
})

onUnmounted(() => {
  stopCarousel()
  if (quoteTimer) clearInterval(quoteTimer)
  window.removeEventListener('bg-update', handleBgUpdate)
  window.removeEventListener('dashboard-cards-changed', onDashCardsChanged)
  document.removeEventListener('click', closeMenu)
  window.removeEventListener('ai-action-done', onAiActionDone)
})
</script>

<style scoped>
.home {
  height: 100vh;
  position: relative;
}
.animated-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  background:
    radial-gradient(ellipse at 20% 50%, color-mix(in srgb, var(--user-bg-color, #6C5CE7) 18%, transparent) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, color-mix(in srgb, var(--user-bg-color, #00CEC9) 12%, transparent) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, color-mix(in srgb, var(--user-bg-color, #FF6B6B) 8%, transparent) 0%, transparent 50%),
    var(--bg-dark);
  background-size: 100% 100%;
  background-position: center;
  background-repeat: no-repeat;
}
:root.light-theme .animated-bg {
  background:
    radial-gradient(ellipse at 20% 30%, color-mix(in srgb, var(--user-bg-color, #4285F4) 12%, transparent) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 70%, color-mix(in srgb, var(--user-bg-color, #0096C8) 10%, transparent) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 10%, color-mix(in srgb, var(--user-bg-color, #82B1FF) 8%, transparent) 0%, transparent 50%),
    transparent;
}
.bg-wallpaper {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  z-index: -1;
}
.layout {
  display: flex;
  height: 100%;
  position: relative;
  z-index: 1;
}
.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: 1px solid var(--border);
  background:
    radial-gradient(ellipse at 20% 20%, color-mix(in srgb, var(--primary) 8%, transparent) 0%, transparent 60%),
    radial-gradient(ellipse at 80% 80%, color-mix(in srgb, var(--accent) 5%, transparent) 0%, transparent 50%),
    color-mix(in srgb, var(--bg-card) 85%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
.right-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}
.top-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 20px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--border);
  background: color-mix(in srgb, var(--bg-card) 85%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  z-index: 20;
}
.top-bar-left {
  flex: 1;
  display: flex;
  align-items: center;
  min-width: 0;
}
.top-bar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}
.dash-card {
  height: 130px;
  border-radius: 12px;
  border: 1px solid var(--border);
  position: relative;
  overflow: hidden;
  /* 修复 WebKit 下 backdrop-filter 干扰 border-radius 裁剪的问题 */
  -webkit-mask-image: -webkit-radial-gradient(white, black);
  mask-image: radial-gradient(white, black);
  transition: transform 0.15s, box-shadow 0.15s;
  cursor: default;
}
.dash-card.dragging { opacity: 0.4; transform: scale(0.95); }
/* 卡片关闭按钮 */
.dash-close-btn {
  position: absolute; top: 4px; right: 4px;
  width: 20px; height: 20px; border: none; border-radius: 50%;
  background: rgba(128,128,128,0.2); color: var(--text3);
  font-size: 14px; line-height: 1; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity 0.15s, background 0.15s;
  z-index: 50;
}
.dash-card:hover .dash-close-btn { opacity: 1; }
.dash-close-btn:hover { background: rgba(255,80,80,0.3); color: #ff6b6b; }
/* 拖拽手柄 */
.drag-grip {
  position: absolute; top: 2px; left: 50%; transform: translateX(-50%);
  font-size: 10px; color: var(--text3); opacity: 0; z-index: 10;
  line-height: 1; letter-spacing: 2px;
  cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 22 22'%3E%3Cdefs%3E%3Cfilter id='s'%3E%3CfeDropShadow dx='0' dy='1' stdDeviation='1' flood-opacity='0.3'/%3E%3C/filter%3E%3C/defs%3E%3Cg filter='url(%23s)'%3E%3Cpath d='M10 2v8l-3-2v2l3 2 2 1 4 2 .5.5V8c0-1-.7-2-2-2h-1V4c0-1-.7-2-2-2h-1.5z' fill='white' stroke='%236C5CE7' stroke-width='1.2' stroke-linejoin='round'/%3E%3Cpath d='M5 10l-2 3c0 3 2 6 6 7 2 .5 5 .5 7 0l2-1 1-2' fill='none' stroke='%236C5CE7' stroke-width='1.2'/%3E%3C/g%3E%3C/svg%3E") 5 5, auto;
  transition: opacity 0.15s;
}
.dash-card:hover .drag-grip { opacity: 0.5; }
.dash-card .drag-grip:active { opacity: 0.8; cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 22 22'%3E%3Cdefs%3E%3Cfilter id='s'%3E%3CfeDropShadow dx='0' dy='1' stdDeviation='1' flood-opacity='0.3'/%3E%3C/filter%3E%3C/defs%3E%3Cg filter='url(%23s)'%3E%3Cpath d='M10 2v8l-3-2v2l3 2 2 1 4 2 .5.5V8c0-1-.7-2-2-2h-1V4c0-1-.7-2-2-2h-1.5z' fill='%236C5CE7' stroke='%236C5CE7' stroke-width='1.2' stroke-linejoin='round'/%3E%3Cpath d='M5 10l-2 3c0 3 2 6 6 7 2 .5 5 .5 7 0l2-1 1-2' fill='none' stroke='%236C5CE7' stroke-width='1.2'/%3E%3C/g%3E%3C/svg%3E") 5 5, auto; }
/* 卡片底部彩色渐变装饰线 */
.dash-card::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, var(--primary), var(--accent), #FF6B6B);
  opacity: 0.4;
}
.dash-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text3);
  font-size: 14px;
  border-style: dashed;
  background: color-mix(in srgb, var(--bg-card) 50%, transparent);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

/* 右键菜单 */
.ctx-menu-fixed {
  position: fixed;
  z-index: 999;
  min-width: 120px;
  background: var(--bg-menu);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 4px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.ctx-item-fixed {
  display: block;
  width: 100%;
  padding: 7px 12px;
  background: none;
  border: none;
  border-radius: 5px;
  color: var(--text2);
  font-size: 12px;
  text-align: left;
  cursor: pointer;
  transition: all 0.1s;
}
.ctx-item-fixed:hover {
  background: var(--bg-glass);
  color: var(--text);
}
/* 一言卡片 */
.dash-quote {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background:
    radial-gradient(ellipse at 20% 30%, color-mix(in srgb, #6C5CE7 15%, transparent) 0%, transparent 50%),
    color-mix(in srgb, var(--bg-card) 70%, transparent);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}
.quote-text {
  font-family: 'Ma Shan Zheng', 'ZCOOL XiaoWei', cursive;
  font-size: 16px;
  line-height: 1.7;
  color: var(--text);
  word-wrap: break-word;
  overflow-wrap: break-word;
}
.quote-from {
  font-family: 'Ma Shan Zheng', 'ZCOOL XiaoWei', cursive;
  font-size: 13px;
  color: var(--text3);
  margin-top: 4px;
  text-align: right;
}

/* 顶栏歌词 */
.header-lyric {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  border-left: 1px solid var(--border);
  margin-left: 4px;
  max-width: 380px;
  overflow: hidden;
  min-height: 36px;
}
.header-lyric-content {
  display: flex;
  flex-direction: column;
  gap: 1px;
  overflow: hidden;
  flex: 1;
  min-width: 0;
}
.header-lyric-btn {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--text3);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s;
  padding: 0;
  opacity: 0.6;
}
.header-lyric-btn:hover {
  opacity: 1;
  color: var(--text);
}
.header-lyric-btn.playing {
  color: #FF6B6B;
  opacity: 1;
  animation: header-pulse 1s infinite;
}
@keyframes header-pulse { 0%,100% { opacity: 0.7; } 50% { opacity: 1; } }
.header-lyric-line {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.header-lyric-line.current {
  font-size: 14px;
  color: var(--text);
  font-weight: 600;
}
.header-lyric-line.next {
  font-size: 11px;
  color: var(--text3);
}
.header-lyric-placeholder {
  font-size: 12px;
  color: var(--text3);
}
.right-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}
/* 仪表板（随内容滚动，不固定） */
.dashboard {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
  padding: 12px 0 8px;
}
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0 20px 12px;
  overflow-y: auto;
  overflow-x: hidden;
  min-width: 0;
  scrollbar-width: none;
  -ms-overflow-style: none;
  background: var(--bg);
}
.main::-webkit-scrollbar {
  display: none;
}
.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding-top: 16px;
}
.cal-wrapper {
  margin: 12px 0 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.ai-wrapper {
  margin: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}
.wiki-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--text3);
  font-size: 16px;
  opacity: 0.6;
}
.greeting-name {
  background: linear-gradient(135deg, #6C5CE7, #00CEC9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}
.greeting-text {
  font-size: 14px;
  color: var(--text3);
  white-space: nowrap;
  flex-shrink: 0;
}

/* 访客模式登录按钮 */
.guest-login-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  background: var(--primary);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all .2s;
  white-space: nowrap;
}
.guest-login-btn:hover {
  opacity: .88;
  box-shadow: 0 2px 10px color-mix(in srgb, var(--primary) 30%, transparent);
  transform: translateY(-1px);
}
.guest-login-btn:active {
  transform: translateY(0);
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* User Dropdown */
.user-dropdown {
  position: relative;
}
.avatar-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
  transition: opacity 0.2s;
}
.avatar-btn:hover {
  opacity: 0.85;
}
.avatar-small {
  font-size: 13px;
  font-weight: 700;
  color: white;
}
.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}
.dropdown-menu {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  width: 220px;
  background: var(--bg-menu);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  z-index: 100;
  overflow: hidden;
}
.dropdown-header {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.dropdown-username {
  font-size: 14px;
  font-weight: 600;
}
.dropdown-account {
  font-size: 12px;
  color: var(--text3);
}
.dropdown-body {
  padding: 6px;
}
.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: none;
  border: none;
  border-radius: 8px;
  color: var(--text2);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.dropdown-item:hover {
  background: var(--bg-glass);
  color: var(--text);
}
.dropdown-divider {
  height: 1px;
  background: var(--border);
  margin: 4px 6px;
}
/* ── 切换账号弹窗 ── */
.switch-btn-wrap {
  position: relative;
}
.switch-btn {
  width: 32px; height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text3);
  cursor: pointer;
  transition: all 0.15s;
}
.switch-btn:hover {
  background: rgba(255,255,255,0.08);
  border-color: var(--primary);
  color: var(--primary);
}
.switch-popover {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 195px;
  background: var(--bg-modal);
  border: 1px solid var(--border-light);
  border-radius: 14px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.4);
  z-index: 9999;
  overflow: hidden;
}
.popover-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px 6px;
  border-bottom: 1px solid var(--border);
}
.popover-header h3 {
  font-size: 12px;
  font-weight: 600;
  color: var(--text2);
}
.popover-count {
  font-size: 10px;
  color: var(--text3);
  background: var(--bg-glass);
  padding: 1px 6px;
  border-radius: 20px;
}
.popover-body {
  max-height: 280px;
  overflow-y: auto;
  padding: 2px 4px;
}
.popover-body::-webkit-scrollbar { width: 3px; }
.popover-body::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
.switch-row {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.1s;
}
.switch-row:hover:not(.active) { background: var(--bg-glass); }
.switch-row.active { opacity: 0.5; cursor: default; }
.sr-avatar {
  width: 22px; height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 700;
  color: white;
  overflow: hidden;
  flex-shrink: 0;
}
.sr-avatar img { width: 100%; height: 100%; object-fit: cover; }
.sr-info {
  flex: 1;
  min-width: 0;
}
.sr-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
  line-height: 1.3;
  display: flex;
  align-items: center;
  gap: 4px;
}
.sr-badge {
  font-size: 9px;
  padding: 0 5px;
  border-radius: 20px;
  background: var(--primary-light);
  color: var(--primary);
  border: 1px solid rgba(108, 92, 231, 0.2);
  font-weight: 500;
}
.sr-acct {
  font-size: 10px;
  color: var(--text3);
}
.sr-del {
  width: 20px; height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  border-radius: 4px;
  color: var(--text3);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.12s;
}
.sr-del:hover {
  background: rgba(255, 107, 107, 0.1);
  color: var(--danger);
}
.popover-empty {
  text-align: center;
  padding: 24px 0;
  color: var(--text3);
  font-size: 12px;
}

/* ── 缩放控制 ── */
.zoom-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
}
.zoom-label {
  font-size: 12px;
  color: var(--text3);
  margin-right: auto;
}
.zoom-btn {
  width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text2);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.12s;
}
.zoom-btn:hover { background: var(--primary); color: white; border-color: var(--primary); }
.zoom-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  min-width: 36px;
  text-align: center;
}
.zoom-reset { font-size: 12px; }

.todo-sidebar {
  width: var(--todo-width);
  flex-shrink: 0;
  overflow-y: auto;
  overflow-x: hidden;
  margin: 12px 0 12px 0;
  border-radius: 12px 0 0 12px;
  border: 1px solid var(--border);
  border-right: none;
  background: color-mix(in srgb, var(--bg-card) 85%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
.todo-reopen {
  position: absolute;
  right: 4px;
  top: 60px;
  width: 28px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, color-mix(in srgb, var(--primary) 20%, transparent), color-mix(in srgb, var(--accent) 15%, transparent));
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-right: none;
  border-radius: 10px 0 0 10px;
  color: var(--text2);
  cursor: pointer;
  transition: all 0.2s;
  z-index: 10;
  box-shadow: 0 0 15px color-mix(in srgb, var(--primary) 15%, transparent);
}
.todo-reopen:hover {
  color: white;
  background: linear-gradient(180deg, color-mix(in srgb, var(--primary) 50%, transparent), color-mix(in srgb, var(--accent) 40%, transparent));
  border-color: color-mix(in srgb, var(--primary) 40%, transparent);
  box-shadow: 0 0 25px color-mix(in srgb, var(--primary) 40%, transparent),
              inset 0 0 20px color-mix(in srgb, var(--primary) 10%, transparent);
}

/* ════════════════════════════════════════
   移动端适配（不影响 PC 端）
   ════════════════════════════════════════ */
/* 底部导航 — 默认隐藏 */
.mobile-bottom-nav { display: none; }

@media (max-width: 768px) {
  .sidebar { display:none; }
  .todo-sidebar { display:none; }
  .todo-reopen { display:none; }
  .right-body { flex-direction:column; }
  .right-area { padding-bottom:calc(56px + env(safe-area-inset-bottom, 0px)); }
  .main { padding:0 12px 12px; }
  .top-bar { padding:4px 12px; gap:8px; flex-wrap:wrap; }
  .top-bar-left { flex:1; min-width:0; }
  .header-lyric { display:none; }
  .greeting-text { display:none; }
  .dashboard { grid-template-columns:1fr; gap:8px; }
  .dash-card:not([data-card="clock"]) { display:none; }
  .dash-card { height:100px; }
  .dash-quote { padding:12px; }
  .dash-card .drag-grip { display:none; }
  /* 手机下拉菜单精简：只保留退出登录 */
  .dropdown-body .dropdown-item:not(:last-child) { display:none; }
  .dropdown-body .dropdown-divider { display:none; }
  .zoom-controls { display:none; }
  .dropdown-menu { min-width:100px; right:0; left:auto; }

  /* 底部导航 */
  .mobile-bottom-nav {
    display:flex; position:fixed; bottom:0; left:0; right:0;
    padding-bottom:env(safe-area-inset-bottom, 0px);
    height:calc(56px + env(safe-area-inset-bottom, 0px));
    background:var(--bg-card);
    border-top:1px solid var(--border);
    z-index:1000;
    backdrop-filter:blur(16px);
    -webkit-backdrop-filter:blur(16px);
  }
  .mb-item {
    flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center;
    gap:2px; background:none; border:none;
    color:var(--text3); font-size:9px; font-weight:500;
    cursor:pointer; transition:color .12s;
    padding:0;
  }
  .mb-item.active { color:var(--primary); }
  .mb-item svg { width:20px; height:20px; }
  .mb-item span { line-height:1; }
}

@media (max-width: 480px) {
  .top-bar-right .top-actions { gap:4px; }
  .dashboard { grid-template-columns:1fr; gap:6px; }
  .dash-card { height:80px; }
  .main { padding:0 8px 8px; }
}
</style>
