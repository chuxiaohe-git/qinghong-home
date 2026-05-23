<template>
  <div class="tab-content">
    <p class="desc">备份当前数据库（SQLite），或上传备份文件恢复数据。仅超级管理员可操作。</p>
    <div class="actions">
      <button class="btn-primary" @click="doCreateBackup" :disabled="creating">
        {{ creating ? '备份中...' : '💾 创建备份' }}
      </button>
      <label class="btn-secondary btn-import" :class="{ disabled: restoring }">
        {{ restoring ? '恢复中...' : '📂 上传备份恢复' }}
        <input type="file" accept=".db" hidden @change="doRestoreUpload" />
      </label>
    </div>

    <div v-if="msg" class="result-bar" :class="{ success: msgOk, error: !msgOk }">
      {{ msg }}
    </div>

    <div class="section-divider"></div>
    <h3 class="section-title">备份列表</h3>

    <div v-if="loading" class="hint">加载中...</div>
    <div v-else-if="!backups.length" class="hint">暂无备份记录</div>
    <div v-else class="backup-list">
      <div v-for="b in backups" :key="b.name" class="backup-item">
        <div class="backup-info">
          <span class="backup-name">{{ b.name }}</span>
          <span class="backup-meta">{{ formatSize(b.size) }} · {{ b.time }}</span>
        </div>
        <div class="backup-actions">
          <button class="small-btn" @click="doDownload(b.name)" title="下载">⬇</button>
          <button class="small-btn danger" @click="doRestoreLocal(b.name)" title="恢复到此版本">↩</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { createBackup, listBackups, downloadBackup, restoreBackup, restoreLocalBackup } from '@/api/backup'

const creating = ref(false)
const restoring = ref(false)
const loading = ref(true)
const backups = ref([])
const msg = ref('')
const msgOk = ref(true)

function showMsg(ok, text) {
  msg.value = text
  msgOk.value = ok
  setTimeout(() => { msg.value = '' }, 5000)
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / 1024 / 1024).toFixed(1) + 'MB'
}

async function fetchList() {
  loading.value = true
  try {
    const res = await listBackups()
    backups.value = (res.data || res) || []
  } catch {
    backups.value = []
  } finally {
    loading.value = false
  }
}

async function doCreateBackup() {
  creating.value = true
  try {
    await createBackup()
    showMsg(true, '备份成功')
    fetchList()
  } catch (e) {
    showMsg(false, '备份失败：' + (e.message || e))
  } finally {
    creating.value = false
  }
}

async function doDownload(name) {
  try {
    const res = await downloadBackup(name)
    const blob = new Blob([res], { type: 'application/octet-stream' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = name
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    showMsg(false, '下载失败')
  }
}

async function doRestoreUpload(e) {
  const file = e.target.files?.[0]
  if (!file) return
  restoring.value = true
  try {
    await restoreBackup(file)
    showMsg(true, '恢复成功，请刷新页面')
  } catch (e) {
    showMsg(false, '恢复失败：' + (e.message || e))
  } finally {
    restoring.value = false
    e.target.value = ''
  }
}

async function doRestoreLocal(name) {
  if (!confirm(`确认恢复到备份 "${name}" 吗？当前数据将被覆盖。`)) return
  restoring.value = true
  try {
    await restoreLocalBackup(name)
    showMsg(true, '恢复成功，请刷新页面')
  } catch (e) {
    showMsg(false, '恢复失败：' + (e.message || e))
  } finally {
    restoring.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.tab-content { max-width: 600px; }
.desc { color: var(--text3); font-size: 13px; line-height: 1.6; margin-bottom: 16px; }
.actions { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.btn-primary {
  padding: 8px 20px; background: var(--primary); border: none; border-radius: 8px;
  color: white; font-size: 14px; font-weight: 600; cursor: pointer;
}
.btn-primary:hover { opacity: 0.85; }
.btn-secondary {
  padding: 8px 20px; background: var(--bg-glass); border: 1px solid var(--border);
  border-radius: 8px; color: var(--text2); font-size: 14px; cursor: pointer; display: inline-block;
}
.btn-secondary:hover { border-color: var(--primary); color: var(--text); }
.btn-import { position: relative; }
.btn-import input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
.disabled { opacity: 0.5; pointer-events: none; }
.result-bar {
  padding: 8px 14px; border-radius: 8px; font-size: 13px; margin-bottom: 16px;
}
.result-bar.success { background: color-mix(in srgb, #00CEC9 20%, transparent); color: #00CEC9; }
.result-bar.error { background: color-mix(in srgb, #FF6B6B 20%, transparent); color: #FF6B6B; }
.section-divider { border: none; border-top: 1px solid var(--border); margin: 20px 0; }
.section-title { font-size: 15px; font-weight: 700; margin-bottom: 12px; }
.hint { color: var(--text3); font-size: 13px; }
.backup-list { display: flex; flex-direction: column; gap: 6px; }
.backup-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 12px; border-radius: 8px; background: var(--bg-glass);
  border: 1px solid var(--border);
}
.backup-info { display: flex; flex-direction: column; gap: 2px; overflow: hidden; }
.backup-name { font-size: 13px; font-weight: 600; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.backup-meta { font-size: 11px; color: var(--text3); }
.backup-actions { display: flex; gap: 4px; flex-shrink: 0; }
.small-btn {
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  background: var(--bg-glass); border: 1px solid var(--border); border-radius: 5px;
  color: var(--text2); cursor: pointer; font-size: 13px;
}
.small-btn:hover { border-color: var(--primary); color: var(--text); }
.small-btn.danger:hover { border-color: #FF6B6B; color: #FF6B6B; }
</style>
