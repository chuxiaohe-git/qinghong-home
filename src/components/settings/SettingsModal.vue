<template>
  <div class="settings-overlay">
    <div class="settings-modal">
      <div class="settings-sidebar">
        <div
          v-for="tab in tabs"
          :key="tab.key"
          class="settings-menu-item"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <span v-html="tab.icon"></span>
          <span>{{ tab.label }}</span>
        </div>
      </div>
      <div class="settings-content">
        <div class="settings-header">
          <h2>{{ currentTab?.label }}</h2>
          <button class="close-btn" @click="$emit('close')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="settings-body">
          <ProfileTab v-if="activeTab === 'profile'" />
          <PersonalizeTab v-if="activeTab === 'personalize'" />
          <GroupManageTab v-if="activeTab === 'groups'" />
          <GalleryTab v-if="activeTab === 'gallery'" />
          <ImportExportTab v-if="activeTab === 'import-export'" />
          <AISettingsTab v-if="activeTab === 'ai'" />
          <AccountManageTab v-if="activeTab === 'accounts'" />
          <GlobalSettingsTab v-if="activeTab === 'global'" />
          <BackupRestoreTab v-if="activeTab === 'backup'" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ProfileTab from './tabs/ProfileTab.vue'
import PersonalizeTab from './tabs/PersonalizeTab.vue'
import GroupManageTab from './tabs/GroupManageTab.vue'
import GalleryTab from './tabs/GalleryTab.vue'
import ImportExportTab from './tabs/ImportExportTab.vue'
import AISettingsTab from './tabs/AISettingsTab.vue'
import AccountManageTab from './tabs/AccountManageTab.vue'
import GlobalSettingsTab from './tabs/GlobalSettingsTab.vue'
import BackupRestoreTab from './tabs/BackupRestoreTab.vue'

defineEmits(['close'])

const activeTab = ref('profile')

const tabs = [
  { key: 'profile', label: '我的信息', icon: '&#128100;' },
  { key: 'personalize', label: '个性化设置', icon: '&#127912;' },
  { key: 'groups', label: '分组管理', icon: '&#128451;' },
  { key: 'gallery', label: '图库', icon: '&#128247;' },
  { key: 'import-export', label: '导入导出', icon: '&#128230;' },
  { key: 'ai', label: 'AI 设置', icon: '&#129302;' },
  { key: 'accounts', label: '账号管理', icon: '&#128101;' },
  { key: 'global', label: '全局设置', icon: '&#9881;' },
  { key: 'backup', label: '备份恢复', icon: '&#128190;' },
]

const currentTab = computed(() => tabs.find(t => t.key === activeTab.value))
</script>

<style scoped>
.settings-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
}
.settings-modal {
  display: flex;
  width: 900px;
  max-width: 90vw;
  height: 600px;
  max-height: 85vh;
  background: var(--bg-modal);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}
.settings-sidebar {
  width: 180px;
  flex-shrink: 0;
  padding: 20px 0;
  border-right: 1px solid var(--border);
  overflow-y: auto;
}
.settings-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text2);
  transition: all 0.2s;
  user-select: none;
}
.settings-menu-item:hover {
  background: var(--bg-glass);
  color: var(--text);
}
.settings-menu-item.active {
  background: var(--primary-light);
  color: var(--primary);
  font-weight: 600;
}
.settings-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 0;
}
.settings-header h2 {
  font-size: 18px;
  font-weight: 700;
}
.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-glass);
  border-radius: 8px;
  color: var(--text2);
  transition: all 0.2s;
}
.close-btn:hover {
  background: rgba(255,255,255,0.1);
  color: var(--text);
}
.settings-body {
  flex: 1;
  padding: 20px 24px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .settings-modal {
    width:100vw; height:100dvh;
    max-width:none; max-height:none;
    border-radius:0; margin:0;
  }
  .settings-sidebar {
    width:100%; height:auto; flex-shrink:0;
    display:flex; overflow-x:auto;
    padding:8px 10px; gap:2px;
    border-right:none; border-bottom:1px solid var(--border);
    flex-direction:row;
  }
  .settings-menu-item {
    white-space:nowrap; padding:6px 10px;
    border-radius:8px;
    flex-shrink:0; font-size:12px; gap:4px;
  }
  .settings-menu-item span:first-child { font-size:14px; }
  .settings-content { padding-top:0; }
  .settings-header { padding:12px 16px; }
  .settings-header h2 { font-size:16px; }
  .settings-body { padding:12px; }
  .close-btn { position:absolute; top:10px; right:10px; }
}
</style>
