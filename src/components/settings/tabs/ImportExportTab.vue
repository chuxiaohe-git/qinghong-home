<template>
  <div class="tab-content">
    <p class="desc">当前账号的配置数据（分组、书签、待办、设置）。导出的配置不包含自身上传的图标文件。</p>
    <div class="actions">
      <button class="btn-primary" @click="doExport" :disabled="exporting">
        {{ exporting ? '导出中...' : '📥 导出配置' }}
      </button>
      <button class="btn-primary" @click="openStrategy" :disabled="importing">
        {{ importing ? '导入中...' : '📤 导入配置' }}
      </button>
    </div>

    <div v-if="result" class="result-bar" :class="{ success: result.ok, error: !result.ok }">
      {{ result.msg }}
    </div>

    <div class="section-divider"></div>
    <h3 class="section-title">浏览器书签转换工具</h3>
    <p class="hint">支持导入 Chrome/Firefox 导出的书签 HTML 文件，自动转换为收藏项目。</p>

    <!-- 文件选择按钮（无 preview 时显示） -->
    <label v-if="!bmPreview" class="btn-primary btn-import" :class="{ disabled: importingBm }" style="margin-top: 12px; display: inline-block;">
      {{ importingBm ? '导入中...' : '🌐 选择书签文件' }}
      <input type="file" accept=".html" hidden @change="onBmFileSelected" />
    </label>

    <!-- 导入预览弹窗 -->
    <Teleport to="body">
      <div v-if="bmPreview" class="strategy-overlay" @click.self="bmPreview = null">
        <div class="strategy-dialog">
          <div class="strategy-head">
            <span>书签导入预览</span>
            <button class="strategy-close" @click="bmPreview = null">✕</button>
          </div>
          <div class="preview-stats">
            <div class="preview-stat">
              <span class="preview-num">{{ bmPreview.folders }}</span>
              <span class="preview-label">个分组</span>
            </div>
            <div class="preview-stat">
              <span class="preview-num">{{ bmPreview.links }}</span>
              <span class="preview-label">个书签</span>
            </div>
          </div>
          <div class="preview-folder-list">
            <div v-for="f in bmPreview.folderList.slice(0, 20)" :key="f.name" class="preview-folder-row">
              <span class="preview-folder-name">{{ f.name }}</span>
              <span class="preview-folder-count">{{ f.count }} 项</span>
            </div>
            <div v-if="bmPreview.folderList.length > 20" class="preview-more">…还有 {{ bmPreview.folderList.length - 20 }} 个分组</div>
          </div>
          <p class="preview-hint">确认后开始导入，书签图标将自动从 <code>favicon.im</code> 获取。</p>
          <div class="preview-actions">
            <button class="btn-cancel" @click="bmPreview = null">取消</button>
            <button class="strategy-confirm" :disabled="importingBm" @click="confirmBmImport">
              {{ importingBm ? '导入中…' : '确认导入' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 导入策略弹窗 -->
    <input type="file" accept=".json" hidden ref="fileInputRef" @change="onFilePicked" />
    <Teleport to="body">
      <div v-if="showStrategy" class="strategy-overlay" @click.self="showStrategy = false">
        <div class="strategy-dialog">
          <div class="strategy-head">
            <span>选择导入策略</span>
            <button class="strategy-close" @click="showStrategy = false">✕</button>
          </div>
          <label class="strategy-option" :class="{ active: pickMode === 'append' }">
            <input type="radio" v-model="pickMode" value="append" />
            <span class="strategy-label">全量追加</span>
            <span class="strategy-desc">始终在下方追加分组与书签，不覆盖任何现有数据</span>
          </label>
          <label class="strategy-option" :class="{ active: pickMode === 'merge' }">
            <input type="radio" v-model="pickMode" value="merge" />
            <span class="strategy-label">覆盖 + 追加</span>
            <span class="strategy-desc">以网址为唯一识别符，覆盖相同书签、追加不存在的书签</span>
          </label>
          <label class="strategy-option" :class="{ active: pickMode === 'overwrite' }">
            <input type="radio" v-model="pickMode" value="overwrite" />
            <span class="strategy-label">全量覆盖</span>
            <span class="strategy-desc">清空现有分组与书签，完全替换为导入的数据</span>
          </label>
          <button class="strategy-confirm" :disabled="!pickMode" @click="confirmImport">确认导入</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { exportConfig, importConfig, importBookmarksHtml } from '@/api/backup'

const exporting = ref(false)
const importing = ref(false)
const importingBm = ref(false)
const result = ref(null)
const showStrategy = ref(false)
const pickMode = ref('append')
const fileInputRef = ref(null)

// 书签导入预览
const bmPreview = ref(null)  // { file, folders, links, folderList }
let bmFile = null

function showResult(ok, msg) {
  result.value = { ok, msg }
  setTimeout(() => { result.value = null }, 5000)
}

async function doExport() {
  exporting.value = true
  try {
    const res = await exportConfig()
    const data = res.data || res
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `qinghong-config-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    showResult(true, '导出成功，已下载配置文件')
  } catch (e) {
    showResult(false, '导出失败：' + (e.message || e))
  } finally {
    exporting.value = false
  }
}

function openStrategy() {
  pickMode.value = 'append'
  showStrategy.value = true
}

async function confirmImport() {
  if (!pickMode.value) return
  showStrategy.value = false
  fileInputRef.value?.click()
}

async function onFilePicked(e) {
  const file = e.target.files?.[0]
  if (!file) return
  importing.value = true
  try {
    const text = await file.text()
    const data = JSON.parse(text)
    const res = await importConfig(data, pickMode.value)
    const d = res.data || res
    showResult(true, d.message || '导入完成')
    setTimeout(() => location.reload(), 1500)
  } catch (e) {
    showResult(false, '导入失败：' + (e.message || e))
  } finally {
    importing.value = false
    e.target.value = ''
  }
}

// ── 浏览器书签导入（预览 → 确认 → 上传） ──

function parseBookmarkHtml(html) {
  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')
  const folders = new Map()

  // 收集所有 <A> 标签，按上级 <H3> 分组
  const links = doc.querySelectorAll('a[href]')
  for (const a of links) {
    const href = a.getAttribute('href') || ''
    const title = a.textContent.trim()
    if (!title || !href || href.startsWith('place:') || href.startsWith('javascript:')) continue

    // 向上找最近的 <H3>
    let folder = '未分类'
    let el = a.parentElement
    while (el) {
      const prevH3 = el.querySelector('h3')
      if (prevH3) { folder = prevH3.textContent.trim(); break }
      // 找前面的 DT H3
      const prev = el.previousElementSibling
      if (prev) {
        const h3 = prev.querySelector('h3')
        if (h3) { folder = h3.textContent.trim(); break }
      }
      el = el.parentElement
    }

    if (!folders.has(folder)) folders.set(folder, 0)
    folders.set(folder, folders.get(folder) + 1)
  }

  const folderList = []
  for (const [name, count] of folders) {
    folderList.push({ name, count })
  }
  folderList.sort((a, b) => b.count - a.count)

  return {
    folders: folderList.length,
    links: folderList.reduce((s, f) => s + f.count, 0),
    folderList,
  }
}

async function onBmFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  e.target.value = ''
  try {
    const html = await file.text()
    const preview = parseBookmarkHtml(html)
    if (preview.links === 0) {
      showResult(false, '未在文件中找到书签链接，请确认是 Chrome/Firefox 导出的书签 HTML')
      return
    }
    bmFile = file
    bmPreview.value = preview
  } catch (err) {
    showResult(false, '文件解析失败：' + (err.message || err))
  }
}

async function confirmBmImport() {
  if (!bmFile) return
  importingBm.value = true
  try {
    const res = await importBookmarksHtml(bmFile)
    const d = res.data || res
    bmPreview.value = null
    bmFile = null
    showResult(true, d.message || '导入完成')
    setTimeout(() => location.reload(), 1500)
  } catch (e) {
    showResult(false, '导入失败：' + (e.message || e))
  } finally {
    importingBm.value = false
  }
}
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
.btn-import { position: relative; display: inline-block; cursor: pointer; }
.btn-import input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
.disabled { opacity: 0.5; pointer-events: none; }
.result-bar {
  padding: 8px 14px; border-radius: 8px; font-size: 13px; margin-bottom: 16px;
}
.result-bar.success { background: color-mix(in srgb, #00CEC9 20%, transparent); color: #00CEC9; }
.result-bar.error { background: color-mix(in srgb, #FF6B6B 20%, transparent); color: #FF6B6B; }
.section-divider { border: none; border-top: 1px solid var(--border); margin: 20px 0; }
.section-title { font-size: 15px; font-weight: 700; margin-bottom: 8px; }
.hint { color: var(--text3); font-size: 13px; }
</style>

<style>
/* 策略弹窗（全局样式，配合 Teleport） */
.strategy-overlay {
  position: fixed; inset: 0; z-index: 99999;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
}
.strategy-dialog {
  width: 380px; max-width: 90vw;
  background: var(--bg-modal); border: 1px solid var(--border);
  border-radius: 14px; padding: 20px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.4);
  display: flex; flex-direction: column; gap: 8px;
}
.strategy-head {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 15px; font-weight: 700; margin-bottom: 4px;
}
.strategy-close {
  width: 26px; height: 26px; display: flex; align-items: center; justify-content: center;
  background: var(--bg-glass); border: none; border-radius: 6px;
  color: var(--text2); cursor: pointer; font-size: 12px;
}
.strategy-option {
  display: flex; flex-direction: column; gap: 2px;
  padding: 10px 14px; border: 1px solid var(--border); border-radius: 8px;
  cursor: pointer; transition: all 0.12s;
}
.strategy-option:hover { border-color: var(--primary); }
.strategy-option.active {
  border-color: var(--primary);
  background: color-mix(in srgb, var(--primary) 10%, transparent);
}
.strategy-option input { display: none; }
.strategy-label { font-size: 14px; font-weight: 600; color: var(--text); }
.strategy-desc { font-size: 12px; color: var(--text3); }
.strategy-confirm {
  margin-top: 8px; padding: 10px; width: 100%;
  background: var(--primary); border: none; border-radius: 8px;
  color: white; font-size: 14px; font-weight: 600; cursor: pointer;
}
.strategy-confirm:hover { opacity: 0.85; }
.btn-cancel {
  padding: 10px 20px; background: var(--bg-glass); border: 1px solid var(--border);
  border-radius: 8px; color: var(--text2); font-size: 14px; cursor: pointer;
}
.btn-cancel:hover { background: var(--border); }
/* 预览弹窗 */
.preview-stats { display: flex; gap: 16px; justify-content: center; margin: 8px 0; }
.preview-stat { text-align: center; }
.preview-num { font-size: 28px; font-weight: 800; color: var(--primary); display: block; }
.preview-label { font-size: 12px; color: var(--text3); }
.preview-folder-list {
  max-height: 180px; overflow-y: auto; margin: 8px 0;
  display: flex; flex-direction: column; gap: 2px;
}
.preview-folder-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 4px 8px; border-radius: 4px; font-size: 13px;
}
.preview-folder-name { color: var(--text); font-weight: 500; }
.preview-folder-count { color: var(--text3); font-size: 12px; }
.preview-more { text-align: center; font-size: 12px; color: var(--text3); padding: 4px; }
.preview-hint { font-size: 12px; color: var(--text3); line-height: 1.5; }
.preview-hint code { font-size: 11px; background: var(--bg-glass); padding: 1px 4px; border-radius: 3px; }
.preview-actions { display: flex; gap: 8px; margin-top: 4px; }
.preview-actions .strategy-confirm { flex: 1; }
.preview-actions .btn-cancel { flex: 1; text-align: center; }
</style>
