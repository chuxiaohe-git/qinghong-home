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

    <div v-if="!userStore.isGuest" class="nav-item active" @click="scrollTo('all')">
      <span class="nav-icon">⭐</span>
      <span class="nav-label">我的收藏</span>
      <span class="nav-count">{{ totalBookmarks }}</span>
    </div>
    <div v-if="!userStore.isGuest" class="nav-item" :class="{ active: activeView === 'todo-calendar' }" @click="goView('todo-calendar')">
      <span class="nav-icon">📅</span>
      <span class="nav-label">摸鱼日历</span>
    </div>
    <div v-if="!userStore.isGuest" class="nav-item" :class="{ active: activeView === 'scratch-note' }" @click="goView('scratch-note')">
      <span class="nav-icon">📝</span>
      <span class="nav-label">摸鱼笔记</span>
    </div>
    <div v-if="!userStore.isGuest" class="nav-item" :class="{ active: activeView === 'ai-chat' }" @click="goView('ai-chat')">
      <span class="nav-icon">🤖</span>
      <span class="nav-label">AI 对话</span>
    </div>

    <div class="sidebar-section-title">收藏分类</div>
    <div class="group-list">
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
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useGroupStore } from '@/stores/groups'
import { useUserStore } from '@/stores/user'

const groupStore = useGroupStore()
const userStore = useUserStore()
const activeId = ref(null)

const props = defineProps({
  totalBookmarks: { type: Number, default: 0 },
  bookmarkCounts: { type: Object, default: () => ({}) },
  activeView: { type: String, default: 'bookmarks' },
})

const emit = defineEmits(['navigate'])

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
.group-count { font-size: 11px; color: var(--text3); background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 10px; border: 1px solid var(--border); flex-shrink: 0; }
</style>
