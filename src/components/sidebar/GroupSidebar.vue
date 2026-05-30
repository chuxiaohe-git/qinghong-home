<template>
  <div class="group-sidebar">
    <div class="sidebar-header">
      <div class="sidebar-logo">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/>
          <rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>
        </svg>
      </div>
      <span class="sidebar-title">轻鸿主页</span>
    </div>

    <div v-if="!userStore.isGuest" class="sidebar-section-title">导航</div>

    <div v-if="!userStore.isGuest" class="nav-item" :class="{ active: activeView === 'bookmarks' }" @click="scrollTo('all')">
      <span class="nav-icon">⭐</span>
      <span class="nav-label">我的收藏</span>
      <span class="nav-count">{{ totalBookmarks }}</span>
    </div>
    <div v-if="!userStore.isGuest && showNav('calendar')" class="nav-item" :class="{ active: activeView === 'todo-calendar' }" @click="goView('todo-calendar')">
      <span class="nav-icon">📅</span>
      <span class="nav-label">摸鱼日历</span>
    </div>
    <div v-if="!userStore.isGuest && showNav('notes')" class="nav-item" :class="{ active: activeView === 'scratch-note' }" @click="goView('scratch-note')">
      <span class="nav-icon">📝</span>
      <span class="nav-label">摸鱼笔记</span>
    </div>
    <div v-if="!userStore.isGuest && showNav('wiki')" class="nav-item" :class="{ active: activeView === 'wiki' }" @click="goView('wiki')">
      <span class="nav-icon">📖</span>
      <span class="nav-label">摸鱼WIKI</span>
    </div>
    <div v-if="!userStore.isGuest && showNav('ai')" class="nav-item" :class="{ active: activeView === 'ai-chat' }" @click="goView('ai-chat')">
      <span class="nav-icon">🤖</span>
      <span class="nav-label">AI 对话</span>
    </div>

    <!-- 收藏分类：仅"我的收藏"激活时显示 -->
    <div v-if="activeView === 'bookmarks'" class="sidebar-section-title">收藏分类</div>
    <div v-if="activeView === 'bookmarks'" class="group-list">
      <div
        v-for="group in groupStore.groups"
        :key="group.id"
        class="group-item"
        :class="{ active: activeId === group.id }"
        @click="scrollToGroup(group.id)"
      >
        <div class="sidebar-dot" :style="{ background: getGroupColor(group), color: getGroupColor(group) }"></div>
        <span class="group-name">{{ group.name }}</span>
        <span class="group-count">{{ getBookmarkCount(group.id) }}</span>
      </div>
    </div>

    <!-- WIKI 目录：仅"摸鱼WIKI"激活时显示 -->
    <div v-if="activeView === 'wiki'" class="sidebar-section-title">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="opacity:0.5;flex-shrink:0"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
      <span>WIKI 目录</span>
      <button class="wiki-add-btn" @click="$emit('create-wiki-doc')" title="新建文档">+</button>
    </div>
    <div v-if="activeView === 'wiki'" class="group-list">
      <div
        v-for="doc in wikiDocs"
        :key="doc.id"
        class="wiki-doc-item"
        :class="{ active: currentWikiDocId === doc.id }"
        @click="$emit('select-wiki-doc', doc.id)"
      >
        <span class="wiki-doc-icon">{{ doc.icon || '📄' }}</span>
        <span class="wiki-doc-name">{{ doc.title || '未命名' }}</span>
      </div>
      <div v-if="!wikiDocs.length" class="wiki-dir-empty">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" opacity="0.25"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        <span>暂无文档</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useGroupStore } from '@/stores/groups'
import { useUserStore } from '@/stores/user'

const groupStore = useGroupStore()
const userStore = useUserStore()
const activeId = ref(null)

const props = defineProps({
  totalBookmarks: { type: Number, default: 0 },
  bookmarkCounts: { type: Object, default: () => ({}) },
  activeView: { type: String, default: 'bookmarks' },
  wikiDocs: { type: Array, default: () => [] },
  currentWikiDocId: { type: Number, default: null },
})

const emit = defineEmits(['navigate', 'select-wiki-doc', 'create-wiki-doc', 'delete-wiki-doc'])

// 导航显隐控制（默认全部可见，收藏始终显示）
const hiddenNav = ref(JSON.parse(localStorage.getItem('hidden_nav') || '[]'))

function showNav(key) {
  return !hiddenNav.value.includes(key)
}

// 监听设置页的导航显隐事件
function onNavVisibilityChanged(e) {
  if (e.detail && Array.isArray(e.detail.hiddenNav)) {
    hiddenNav.value = e.detail.hiddenNav
    localStorage.setItem('hidden_nav', JSON.stringify(hiddenNav.value))
  }
}
onMounted(() => {
  window.addEventListener('nav-visibility-changed', onNavVisibilityChanged)
})
onBeforeUnmount(() => {
  window.removeEventListener('nav-visibility-changed', onNavVisibilityChanged)
})

function getBookmarkCount(groupId) {
  return props.bookmarkCounts[groupId] || 0
}

function scrollToGroup(groupId) {
  activeId.value = groupId
  const el = document.getElementById('group-' + groupId)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function scrollTo(section) {
  if (section === 'all') {
    emit('navigate', 'bookmarks')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

function goView(view) {
  emit('navigate', props.activeView === view ? 'bookmarks' : view)
}

const groupColors = ['#6C5CE7', '#00CEC9', '#FF6B6B', '#FDCB6E', '#A29BFE', '#4facfe', '#43e97b', '#fa709a']
function getGroupColor(group) {
  let hash = 0
  for (let i = 0; i < group.name.length; i++) hash = group.name.charCodeAt(i) + ((hash << 5) - hash)
  return groupColors[Math.abs(hash) % groupColors.length]
}
</script>

<style scoped>
.group-sidebar { display: flex; flex-direction: column; height: 100%; }
.sidebar-header {
  display: flex; align-items: center; gap: 10px;
  padding: 20px 24px 16px;
}
.sidebar-logo {
  width: 32px; height: 32px; border-radius: 8px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  display: flex; align-items: center; justify-content: center; color: white;
  filter: drop-shadow(0 0 10px rgba(108,92,231,0.5));
}
.sidebar-title {
  font-size: 16px; font-weight: 700;
  background: linear-gradient(135deg, #6C5CE7, #00CEC9);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.sidebar-section-title {
  font-size: 13px; color: var(--text2); text-transform: uppercase;
  letter-spacing: 1.5px; padding: 16px 24px 8px; font-weight: 600;
  display: flex; align-items: center; gap: 8px;
}
.sidebar-section-title span { flex: 1; }
.wiki-add-btn {
  width: 22px; height: 22px;
  display: flex; align-items: center; justify-content: center;
  background: none; border: 1px dashed var(--border); border-radius: 5px;
  color: var(--text3); font-size: 14px; cursor: pointer; transition: all 0.12s;
}
.wiki-add-btn:hover {
  border-color: var(--primary); color: var(--primary);
  background: rgba(108,92,231,0.08);
}
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 16px 10px 16px; cursor: pointer; transition: all 0.12s;
  margin: 1px 12px; border-radius: var(--radius-md);
}
.nav-item:hover { background: rgba(255,255,255,0.05); }
.nav-item.active {
  background: linear-gradient(135deg, rgba(108,92,231,0.2), rgba(0,206,201,0.1));
  box-shadow: 0 4px 15px rgba(108,92,231,0.2);
}
.nav-icon { font-size: 14px; width: 20px; text-align: center; flex-shrink: 0; }
.nav-label { font-size: 14px; color: var(--text2); font-weight: 500; flex: 1; min-width: 0; }
.nav-item.active .nav-label { color: var(--text); font-weight: 600; }
.nav-count {
  font-size: 11px; color: var(--text3);
  background: rgba(255,255,255,0.05); padding: 2px 8px;
  border-radius: 10px; border: 1px solid var(--border); flex-shrink: 0;
}
.group-list { display: flex; flex-direction: column; gap: 1px; }
.group-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 16px 10px 16px; cursor: pointer; transition: all 0.12s;
  margin: 1px 12px; border-radius: var(--radius-md);
}
.group-item:hover { background: rgba(255,255,255,0.05); }
.group-item.active {
  background: linear-gradient(135deg, rgba(108,92,231,0.2), rgba(0,206,201,0.1));
}
.sidebar-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; box-shadow: 0 0 8px currentColor; }
.group-name { font-size: 14px; color: var(--text2); font-weight: 500; flex: 1; min-width: 0; }
.group-item.active .group-name { color: var(--text); font-weight: 600; }
.group-count { font-size: 11px; color: var(--text3); background: rgba(255,255,255,0.05);   padding: 2px 8px; border-radius: 10px; border: 1px solid var(--border); flex-shrink: 0; }
.wiki-doc-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 24px; cursor: pointer;
  transition: all 0.12s;
  position: relative;
}
.wiki-doc-item:hover {
  background: rgba(255,255,255,0.03);
}
.wiki-doc-item.active {
  background: rgba(108,92,231,0.1);
}
.wiki-doc-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 4px;
  bottom: 4px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: linear-gradient(180deg, #6C5CE7, #00CEC9);
}
.wiki-doc-icon {
  font-size: 13px;
  width: 18px;
  text-align: center;
  flex-shrink: 0;
  opacity: 0.6;
}
.wiki-doc-item.active .wiki-doc-icon {
  opacity: 1;
}
.wiki-doc-name {
  font-size: 13px;
  color: var(--text2);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.wiki-doc-item.active .wiki-doc-name {
  color: var(--text);
  font-weight: 600;
}
.wiki-dir-empty {
  display: flex; align-items: center; gap: 8px; padding: 20px 24px;
  color: var(--text3); font-size: 13px; opacity: 0.5;
}
</style>
