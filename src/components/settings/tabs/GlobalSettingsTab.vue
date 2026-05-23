<template>
  <div class="tab-content">
    <div class="setting-group">
      <h3 class="group-title">访客模式</h3>
      <p class="group-desc">开启后，未登录用户可以直接访问主页，查看标记为"访客可见"的分组书签</p>
      <div class="toggle-row">
        <div class="toggle-info">
          <span class="toggle-label">全局访客模式</span>
          <span class="toggle-status" :class="{ on: guestEnabled }">{{ guestEnabled ? '已开启' : '已关闭' }}</span>
        </div>
        <button class="toggle-switch" :class="{ on: guestEnabled }" @click="toggleGuestMode" :disabled="saving">
          <span class="toggle-knob"></span>
        </button>
      </div>
      <p v-if="saved" class="saved-hint">✓ 已保存</p>
    </div>

    <div class="setting-group">
      <h3 class="group-title">预留功能</h3>
      <p class="group-desc">以下功能将在后续版本实现</p>
      <div class="feature-list">
        <div class="feature-item">站点标题</div>
        <div class="feature-item">登录页背景图片</div>
        <div class="feature-item">自定义 JS / CSS 文件</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getSettings, updateSettings } from '@/api/settings'

const guestEnabled = ref(false)
const saving = ref(false)
const saved = ref(false)
let saveTimer = null

onMounted(async () => {
  try {
    const res = await getSettings()
    const config = JSON.parse(res.data?.layout_config || '{}')
    guestEnabled.value = !!config.guest_mode
  } catch {}
})

async function toggleGuestMode() {
  saving.value = true
  saved.value = false
  const newVal = !guestEnabled.value
  const config = { guest_mode: newVal }
  try {
    await updateSettings({ layout_config: JSON.stringify(config) })
    guestEnabled.value = newVal
    saved.value = true
    clearTimeout(saveTimer)
    saveTimer = setTimeout(() => { saved.value = false }, 2000)
  } catch {}
  saving.value = false
}
</script>

<style scoped>
.tab-content { max-width: 600px; }
.setting-group { margin-bottom: 28px; }
.group-title { font-size: 15px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.group-desc { font-size: 13px; color: var(--text3); margin-bottom: 16px; line-height: 1.5; }
.toggle-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; background: var(--bg-glass); border-radius: 10px;
  border: 1px solid var(--border);
}
.toggle-info { display: flex; flex-direction: column; gap: 2px; }
.toggle-label { font-size: 14px; font-weight: 500; color: var(--text); }
.toggle-status { font-size: 12px; color: var(--text3); }
.toggle-status.on { color: var(--primary); }
.toggle-switch {
  position: relative; width: 44px; height: 24px;
  background: var(--border); border: none; border-radius: 12px;
  cursor: pointer; transition: background .2s; flex-shrink: 0;
}
.toggle-switch.on { background: var(--primary); }
.toggle-switch:disabled { opacity: .5; cursor: not-allowed; }
.toggle-knob {
  position: absolute; top: 2px; left: 2px;
  width: 20px; height: 20px; border-radius: 50%;
  background: #fff; transition: transform .2s;
  box-shadow: 0 1px 3px rgba(0,0,0,.2);
}
.toggle-switch.on .toggle-knob { transform: translateX(20px); }
.saved-hint { font-size: 12px; color: var(--success, #27ae60); margin-top: 6px; }
.feature-list { display: flex; flex-direction: column; gap: 8px; }
.feature-item { padding: 10px 14px; background: var(--bg-glass); border-radius: 8px; font-size: 13px; color: var(--text2); }
</style>
