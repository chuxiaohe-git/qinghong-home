<template>
  <div class="wiki-panel">
    <div v-if="loading" class="wiki-loading">加载中...</div>
    <div v-else-if="currentDoc" class="wiki-body">
      <!-- 查看模式 -->
      <div v-if="!editing" class="wiki-view">
        <div class="wiki-bar">
          <h1 class="wiki-title-view">{{ docTitle || '无标题' }}</h1>
          <div class="wiki-bar-actions">
            <button class="wiki-act" @click="enterEdit" title="编辑">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </button>
            <button class="wiki-act wiki-act-del" @click="deleteDoc" title="删除">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
        </div>
        <div ref="viewBodyRef" class="wiki-view-body"></div>
      </div>
      <!-- 编辑模式 -->
      <div v-else class="wiki-edit">
        <div class="wiki-bar">
          <input class="wiki-title" v-model="docTitle" placeholder="文档标题" />
          <div class="wiki-bar-actions">
            <button class="wiki-btn wiki-mode-btn" :class="{ active: htmlMode }" @click="htmlMode = !htmlMode">
              {{ htmlMode ? '📝 HTML' : '🎨 富文本' }}
            </button>
            <span v-if="saved" class="wiki-saved">已保存</span>
            <button class="wiki-btn" @click="saveDoc">保存</button>
            <button class="wiki-btn" @click="cancelEdit">取消</button>
          </div>
        </div>
        <!-- 富文本模式：TinyMCE -->
        <div v-if="!htmlMode" class="wiki-edit-scroll">
          <Editor
            v-model="docContent"
            tinymce-script-src="/tinymce/tinymce.min.js"
            license-key="gpl"
            :init="editorConfig"
            :disabled="false"
          />
        </div>
        <!-- HTML 模式：纯 textarea，无过滤 -->
        <div v-else class="wiki-edit-scroll">
          <textarea
            class="wiki-html-textarea"
            v-model="docContent"
            spellcheck="false"
          ></textarea>
        </div>
      </div>
    </div>
    <div v-else-if="wikiDocs && wikiDocs.length > 0" class="wiki-home">
      <!-- 顶栏 -->
      <div class="wiki-home-bar">
        <h1 class="wiki-home-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="wiki-home-logo">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          </svg>
          摸鱼WIKI
        </h1>
        <div class="wiki-home-search">
          <span class="whs-icon">🔍</span>
          <input v-model="searchQuery" type="text" placeholder="搜索文档标题..." />
        </div>
        <button class="wiki-home-new" @click="$emit('create-wiki-doc')">＋ 新建文档</button>
      </div>
      <!-- 内容 -->
      <div class="wiki-home-body">
        <!-- 统计 -->
        <div class="wh-stats">
          <div class="wh-stat"><span class="wh-stat-num">{{ wikiDocs.length }}</span><span>篇文档</span></div>
          <div class="wh-stat"><span class="wh-stat-num">{{ todayUpdates }}</span><span>今日更新</span></div>
        </div>
        <!-- 标题 -->
        <div class="wh-sec-title">全部文档</div>
        <!-- 文档网格 -->
        <div class="wh-grid">
          <div
            v-for="doc in filteredDocs"
            :key="doc.id"
            class="wh-card"
            @click="$emit('select-doc', doc.id)"
            @contextmenu.prevent.stop="openCardMenu($event, doc)"
          >
            <div class="wh-card-icon" :style="{ background: getStyle(doc).bg }">{{ getStyle(doc).icon }}</div>
            <div class="wh-card-content">
              <div class="wh-card-title">{{ doc.title || '未命名' }}</div>
              <div class="wh-card-preview">{{ getPreview(doc) }}</div>
            </div>
            <div class="wh-card-footer">
              <span class="wh-card-date">{{ formatDate(doc.updated_at) }}</span>
              <span class="wh-card-tag" :style="{ background: getStyle(doc).tagBg, color: getStyle(doc).tagColor }">{{ getTag(doc) }}</span>
            </div>
          </div>
      <div v-if="filteredDocs.length === 0" class="wh-no-result">
        <span class="wh-no-icon">🔍</span>
        <span>没有找到 "{{ searchQuery }}"</span>
      </div>
      </div>
      <!-- 右键菜单 -->
      <div v-if="ctxMenu.show" class="wh-ctx" :style="{ left: ctxMenu.x + 'px', top: ctxMenu.y + 'px' }">
        <div class="wh-ctx-item" @click="openEditDialog">📝 编辑卡片</div>
      </div>
      <!-- 编辑弹窗 -->
      <div v-if="editDialog.open" class="wh-overlay" @click.self="closeEditDialog">
        <div class="wh-dialog">
          <div class="wh-dlg-title">编辑卡片</div>
          <div class="wh-dlg-body">
            <label>图标</label>
            <div class="wh-icon-picker">
              <span v-for="e in EMOJIS" :key="e"
                class="wh-icon-opt" :class="{ active: editDialog.icon === e }"
                @click="editDialog.icon = e">{{ e }}</span>
            </div>
            <label>标题</label>
            <input class="wh-dlg-input" v-model="editDialog.title" />
            <label>简介</label>
            <textarea class="wh-dlg-textarea" v-model="editDialog.summary" rows="2"></textarea>
          </div>
          <div class="wh-dlg-actions">
            <button class="wh-btn-cancel" @click="closeEditDialog">取消</button>
            <button class="wh-btn-save" @click="saveCardEdit">保存</button>
          </div>
        </div>
      </div>
    </div>
    </div>
    <div v-else class="wiki-empty">
      <div class="we-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" opacity="0.15">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
        </svg>
      </div>
      <p class="we-text">还没有文档，开始创作吧</p>
      <button class="we-btn" @click="$emit('create-wiki-doc')">＋ 新建第一篇文档</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch, nextTick } from 'vue'
import Editor from '@tinymce/tinymce-vue'
import { updateWikiDoc, deleteWikiDoc, uploadWikiImage } from '@/api/wiki'

const props = defineProps({
  currentDoc: { type: Object, default: null },
  wikiDocs: { type: Array, default: () => [] },
})

const docTitle = ref('')
const docContent = ref('')
const loading = ref(false)
const saved = ref(true)
const editing = ref(false)
const htmlMode = ref(false)
const viewBodyRef = ref(null)
const searchQuery = ref('')
const emit = defineEmits(['close-doc', 'doc-updated', 'doc-deleted', 'select-doc', 'create-wiki-doc'])

// 查看模式渲染：支持 HTML 内 script/style 标签，用 iframe 隔离渲染
function renderViewContent(html) {
  const el = viewBodyRef.value
  if (!el) {
    nextTick(() => renderViewContent(html))
    return
  }

  // 检测是否包含完整 HTML 页面
  const isFullPage = /<(html|head|style|script)[\s>]/i.test(html || '')

  if (!isFullPage) {
    el.style.padding = ''
    el.style.overflow = ''
    el.innerHTML = html || ''
    return
  }

  // 完整 HTML 页面：用 iframe 沙箱隔离渲染
  el.innerHTML = ''
  el.style.padding = '0'
  el.style.overflow = 'hidden'  // 关掉滚动条预留空间
  const raw = html || ''
  const iframe = document.createElement('iframe')
  iframe.style.cssText = 'width:100%;height:100%;border:none;background:transparent;display:block;'
  iframe.srcdoc = raw
  // iframe 加载后注入滚动条样式 + 修复 html 白色背景
  iframe.onload = () => {
    try {
      const doc = iframe.contentWindow.document
      // 修复 html 层白色背景（body 的背景不会透到 html）
      const bg = doc.body.style.background || 'transparent'
      doc.documentElement.style.background = bg
      // 注入滚动条样式
      const st = doc.createElement('style')
      st.textContent = [
        '::-webkit-scrollbar{width:8px;height:8px}',
        '::-webkit-scrollbar-track{background:transparent}',
        '::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.15);border-radius:4px;border:1px solid rgba(255,255,255,0.05)}',
        '::-webkit-scrollbar-thumb:hover{background:rgba(255,255,255,0.3)}',
        '*{scrollbar-width:thin;scrollbar-color:rgba(255,255,255,0.15) transparent}',
      ].join('')
      doc.head.appendChild(st)
    } catch(e) { /* cross-origin or timing */ }
  }
  el.appendChild(iframe)
}

// TinyMCE 配置
const editorConfig = {
  skin_url: '/tinymce/skins/ui/oxide',
  min_height: 200,
  menubar: false,
  language: 'zh_CN',
  plugins: 'table link image code lists advlist fullscreen searchreplace charmap',
  toolbar:
    'undo redo | bold italic underline strikethrough | superscript subscript | forecolor backcolor | '
    + 'fontsizeselect | alignleft aligncenter alignright | '
    + 'bullist numlist | indent outdent | '
    + 'table link image | fullscreen code',
  fontsize_formats: '8pt 10pt 12pt 14pt 16pt 18pt 24pt 36pt 48pt',
  table_default_attributes: { border: '1' },
  paste_data_images: true,
  image_advtab: true,
  images_upload_handler: (blobInfo, progress) => new Promise((resolve, reject) => {
    if (!props.currentDoc) { reject('请先选择一个文档'); return }
    const file = blobInfo.blob()
    uploadWikiImage(props.currentDoc.id, file)
      .then(res => {
        if (res.code === 0 && res.data?.url) resolve(res.data.url)
        else reject(res.message || '上传失败')
      })
      .catch(err => reject(err.message || '上传失败'))
  }),
  content_style: `
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; line-height: 1.8; color: #333; padding: 16px; }
    table { border-collapse: collapse; width: 100%; }
    td, th { border: 1px solid #ccc; padding: 8px 10px; }
    th { background: #f5f5f5; font-weight: 700; }
    img { max-width: 100%; }
    pre { background: #f4f4f4; padding: 12px; border-radius: 4px; overflow-x: auto; }
    blockquote { border-left: 3px solid #6C5CE7; padding-left: 16px; opacity: 0.8; margin: 1em 0; }
  `,
  setup: (editor) => {
    editor.on('init', () => {
      // 动态计算高度：.wiki-edit 的剩余空间
      const scroll = document.querySelector('.wiki-edit-scroll')
      if (scroll) {
        const h = scroll.clientHeight
        if (h > 100) {
          editor.getContainer().style.height = h + 'px'
        }
      }
    })
    editor.on('input', () => { saved.value = false })
    editor.on('change', () => { saved.value = false })
  },
}

function formatDate(d) {
  if (!d) return ''
  const date = new Date(d)
  const now = new Date()
  const diffMs = now - date
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return diffMin + '分钟前'
  const diffHour = Math.floor(diffMs / 3600000)
  if (diffHour < 24) return diffHour + '小时前'
  const diffDay = Math.floor(diffMs / 86400000)
  if (diffDay < 7) return diffDay + '天前'
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

// 搜索过滤
const filteredDocs = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return props.wikiDocs
  return props.wikiDocs.filter(d => (d.title || '').toLowerCase().includes(q))
})

// 今日更新数
const todayUpdates = computed(() => {
  const today = new Date()
  const y = today.getFullYear()
  const m = today.getMonth()
  const d = today.getDate()
  return props.wikiDocs.filter(doc => {
    if (!doc.updated_at) return false
    const up = new Date(doc.updated_at)
    return up.getFullYear() === y && up.getMonth() === m && up.getDate() === d
  }).length
})

// 提取预览：优先用自定义 summary，否则从内容取
function getPreview(doc) {
  if (doc.summary) return doc.summary
  if (!doc.content) return '暂无内容'
  const text = doc.content.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim()
  return text.slice(0, 80) + (text.length > 80 ? '...' : '') || '暂无内容'
}

// 标签和图标配色方案
const TAG_STYLES = [
  { keywords: ['绩效', '奖金', '薪资', '工资', '薪酬', '考核'], tag: '绩效', icon: '📊', bg: 'rgba(108,92,231,0.1)', tagBg: 'rgba(108,92,231,0.08)', tagColor: 'rgba(162,155,254,0.7)' },
  { keywords: ['API', '接口', '技术', '代码', '部署', '架构'], tag: '技术', icon: '⚙️', bg: 'rgba(255,107,107,0.1)', tagBg: 'rgba(255,107,107,0.08)', tagColor: 'rgba(255,107,107,0.7)' },
  { keywords: ['天气', '数据', '分析', '报告', '统计'], tag: '数据', icon: '📈', bg: 'rgba(0,206,201,0.1)', tagBg: 'rgba(0,206,201,0.08)', tagColor: 'rgba(0,206,201,0.7)' },
  { keywords: ['周报', '日报', '模板', '计划'], tag: '模板', icon: '📋', bg: 'rgba(253,203,110,0.1)', tagBg: 'rgba(253,203,110,0.08)', tagColor: 'rgba(253,203,110,0.7)' },
  { keywords: ['指南', '说明', '手册', '入职'], tag: '指南', icon: '📖', bg: 'rgba(46,204,113,0.1)', tagBg: 'rgba(46,204,113,0.08)', tagColor: 'rgba(46,204,113,0.7)' },
  { keywords: ['HTML', '页面', '可视化'], tag: 'HTML', icon: '🌐', bg: 'rgba(155,89,182,0.1)', tagBg: 'rgba(155,89,182,0.08)', tagColor: 'rgba(155,89,182,0.7)' },
]

function getTag(doc) {
  if (!doc.content && !doc.title) return '文档'
  const text = (doc.title + ' ' + (doc.content || '')).toLowerCase()
  for (const s of TAG_STYLES) {
    if (s.keywords.some(k => text.includes(k))) return s.tag
  }
  return '文档'
}

function getStyle(doc) {
  // 优先用自定义图标
  if (doc.icon && doc.icon !== '📄') {
    let tagColor = 'rgba(162,155,254,0.7)'
    for (const s of TAG_STYLES) {
      if (s.icon === doc.icon) { tagColor = s.tagColor; break }
    }
    return { icon: doc.icon, bg: 'rgba(108,92,231,0.08)', tagBg: 'rgba(108,92,231,0.06)', tagColor }
  }
  // 自动匹配
  if (!doc.content && !doc.title) return { icon: '📄', bg: 'rgba(108,92,231,0.06)', tagBg: 'rgba(108,92,231,0.06)', tagColor: 'rgba(162,155,254,0.5)' }
  const text = (doc.title + ' ' + (doc.content || '')).toLowerCase()
  for (const s of TAG_STYLES) {
    if (s.keywords.some(k => text.includes(k))) return s
  }
  return { icon: '📄', tag: '文档', bg: 'rgba(108,92,231,0.06)', tagBg: 'rgba(108,92,231,0.06)', tagColor: 'rgba(162,155,254,0.5)' }
}

// 右键菜单 + 编辑弹窗
const EMOJIS = ['📄','📊','⚙️','📈','📋','📖','🌐','🗂','✍️','🎯','💡','🔧','📝','🎨','📌','⭐','🔥','💎','🛠','🧩']
const ctxMenu = reactive({ show: false, x: 0, y: 0, doc: null })
const editDialog = reactive({ open: false, docId: null, icon: '📄', title: '', summary: '' })

function openCardMenu(e, doc) {
  ctxMenu.show = true
  ctxMenu.x = e.clientX
  ctxMenu.y = e.clientY
  ctxMenu.doc = doc
  document.addEventListener('click', closeCtxMenu, { once: true })
}
function closeCtxMenu() { ctxMenu.show = false; ctxMenu.doc = null }

function openEditDialog() {
  const doc = ctxMenu.doc
  if (!doc) return
  editDialog.open = true
  editDialog.docId = doc.id
  editDialog.icon = doc.icon || '📄'
  editDialog.title = doc.title || ''
  editDialog.summary = doc.summary || ''
  ctxMenu.show = false
}
function closeEditDialog() {
  editDialog.open = false
  editDialog.docId = null
}

async function saveCardEdit() {
  if (!editDialog.docId) return
  const data = { icon: editDialog.icon, title: editDialog.title.trim(), summary: editDialog.summary.trim() }
  if (!data.title) { alert('标题不能为空'); return }
  const res = await updateWikiDoc(editDialog.docId, data)
  if (res.code === 0) {
    closeEditDialog()
    emit('doc-updated', res.data)
  }
}

// 检测内容是否包含完整 HTML 页面（含 style/script 标签）
function isFullPageContent(content) {
  return /<(script|style)[\s>]/i.test(content || '')
}

function enterEdit() {
  // 自动检测：内容含 script/style 则切 HTML 模式
  htmlMode.value = isFullPageContent(docContent.value)
  editing.value = true
}

function cancelEdit() {
  if (props.currentDoc) {
    docTitle.value = props.currentDoc.title ?? ''
    docContent.value = props.currentDoc.content ?? ''
    renderViewContent(docContent.value)
  }
  editing.value = false
}

watch(() => props.currentDoc, (doc) => {
  loading.value = true
  if (doc) {
    editing.value = false
    htmlMode.value = false
    docTitle.value = doc.title ?? ''
    docContent.value = doc.content ?? ''
    saved.value = true
    renderViewContent(doc.content ?? '')
  } else {
    docTitle.value = ''
    docContent.value = ''
  }
  loading.value = false
}, { immediate: true })

async function saveDoc() {
  if (!props.currentDoc) return

  const newContent = docContent.value
  const oldContent = props.currentDoc.content ?? ''
  const newTitle = docTitle.value.trim()
  const oldTitle = (props.currentDoc.title ?? '').trim()
  const data = {}

  const n = (newContent || '').replace(/<p><br><\/p>/g, '').replace(/<p><\/p>/g, '').trim()
  const o = (oldContent || '').replace(/<p><br><\/p>/g, '').replace(/<p><\/p>/g, '').trim()
  if (n === '' && o !== '') {
    alert('⚠️ 检测到内容为空，已阻止保存。\n\n请重新编辑后再保存，避免内容丢失。')
    return
  }

  if (newTitle !== oldTitle) data.title = newTitle
  if (newContent !== oldContent) data.content = newContent

  if (Object.keys(data).length === 0) {
    saved.value = true
    editing.value = false
    return
  }

  const res = await updateWikiDoc(props.currentDoc.id, data)
  if (res.code === 0) {
    docContent.value = newContent
    saved.value = true
    editing.value = false
    // 不直接调用 renderViewContent，由 watch 触发
    emit('doc-updated', { ...props.currentDoc, ...data })
  }
}

async function deleteDoc() {
  if (!props.currentDoc) return
  if (!confirm(`确定删除「${docTitle.value || '未命名'}」？`)) return
  await deleteWikiDoc(props.currentDoc.id)
  emit('doc-deleted', props.currentDoc.id)
}
</script>

<style>
.wiki-panel {
  flex: 1; display: flex; flex-direction: column; overflow: hidden;
  min-height: 0;
  border-radius: var(--radius-lg, 12px);
  background: var(--bg-menu, rgba(30,30,50,0.4));
}
.wiki-loading { display:flex; align-items:center; justify-content:center; height:100%; color:var(--text3); font-size:14px; }
.wiki-body { display:flex; flex-direction:column; flex:1; min-height:0; }
.wiki-bar {
  display:flex; align-items:center; gap:8px; padding:10px 20px;
  border-bottom:1px solid var(--border, rgba(255,255,255,0.06)); flex-shrink:0;
}
.wiki-title { flex:1; background:none; border:none; outline:none; font-size:18px; font-weight:700; color:var(--text); padding:4px 0; }
.wiki-title::placeholder { color:var(--text3); opacity:0.4; }
.wiki-title-view { flex:1; margin:0; font-size:18px; font-weight:700; color:var(--text); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.wiki-bar-actions { display:flex; align-items:center; gap:6px; flex-shrink:0; }
.wiki-saved { font-size:11px; color:var(--success,#4CAF50); background:rgba(76,175,80,0.1); padding:2px 6px; border-radius:4px; }
.wiki-btn { padding:5px 12px; height:30px; background:rgba(255,255,255,0.04); border:1px solid var(--border); border-radius:6px; color:var(--text2); font-size:12px; cursor:pointer; transition:all 0.12s; }
.wiki-btn:hover { background:linear-gradient(135deg,rgba(108,92,231,0.15),rgba(0,206,201,0.1)); color:var(--primary); border-color:rgba(108,92,231,0.25); }
.wiki-act { width:30px; height:30px; display:flex; align-items:center; justify-content:center; background:none; border:1px solid transparent; border-radius:6px; color:var(--text3); cursor:pointer; transition:all 0.12s; }
.wiki-act:hover { background:rgba(108,92,231,0.1); color:var(--primary); border-color:rgba(108,92,231,0.2); }
.wiki-act-del:hover { background:rgba(255,77,79,0.1); color:#FF4D4F; border-color:rgba(255,77,79,0.2); }
.wiki-view-body { flex:1; overflow-y:auto; padding:16px 24px 40px; line-height:1.8; color:var(--text); }
.wiki-view { flex:1; display:flex; flex-direction:column; min-height:0; }
.wiki-view-body table { border-collapse: collapse; width: 100%; margin: 1em 0; }
.wiki-view-body td, .wiki-view-body th { border: 1px solid var(--border); padding: 8px 10px; }
.wiki-view-body th { background: rgba(255,255,255,0.04); font-weight: 700; }
.wiki-empty { display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:var(--text3); font-size:14px; gap:12px; }
.wiki-empty-icon { display:flex; align-items:center; justify-content:center; }
.wiki-empty p { margin:0; opacity:0.5; user-select:none; }

/* ===== 摸鱼WIKI 首页（新版） ===== */
.wiki-home { flex:1; display:flex; flex-direction:column; min-height:0; }

/* 顶栏 */
.wiki-home-bar {
  display:flex; align-items:center; gap:12px;
  padding:14px 20px;
  border-bottom:1px solid var(--border); flex-shrink:0; flex-wrap:wrap;
}
.wiki-home-title {
  font-size:16px; font-weight:700; color:var(--text);
  display:flex; align-items:center; gap:8px; margin:0;
}
.wiki-home-logo { color:var(--primary,#6C5CE7); flex-shrink:0; }
.wiki-home-search { position:relative; flex:1; max-width:240px; }
.wiki-home-search input {
  width:100%; padding:6px 10px 6px 28px;
  background:var(--bg-input,rgba(255,255,255,0.04));
  border:1px solid var(--border); border-radius:8px;
  color:var(--text2); font-size:13px; outline:none; transition:all 0.15s;
}
.wiki-home-search input:focus { border-color:rgba(108,92,231,0.3); background:rgba(108,92,231,0.04); }
.wiki-home-search input::placeholder { color:var(--text3); opacity:0.4; }
.whs-icon { position:absolute; left:8px; top:50%; transform:translateY(-50%); font-size:13px; opacity:0.25; pointer-events:none; }
.wiki-home-new {
  display:flex; align-items:center; gap:4px; padding:6px 14px;
  background:linear-gradient(135deg,rgba(108,92,231,0.15),rgba(0,206,201,0.08));
  border:1px solid rgba(108,92,231,0.2); border-radius:8px;
  color:var(--primary,#a29bfe); font-size:13px; cursor:pointer; transition:all 0.15s; white-space:nowrap;
}
.wiki-home-new:hover { background:linear-gradient(135deg,rgba(108,92,231,0.25),rgba(0,206,201,0.15)); border-color:rgba(108,92,231,0.35); }

/* 内容区 */
.wiki-home-body { flex:1; overflow-y:auto; padding:16px 20px 32px; }

/* 统计 */
.wh-stats { display:flex; gap:24px; margin-bottom:20px; }
.wh-stat { display:flex; align-items:center; gap:6px; font-size:12px; color:var(--text3); }
.wh-stat-num {
  font-size:20px; font-weight:700;
  background:linear-gradient(135deg,var(--primary,#6C5CE7),#a29bfe);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}

/* 段落标题 */
.wh-sec-title {
  font-size:12px; font-weight:600; letter-spacing:0.5px;
  color:var(--text3); opacity:0.5;
  margin-bottom:12px; padding-bottom:8px;
  border-bottom:1px solid var(--border);
}

/* 文档网格 */
.wh-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:10px; }

/* 文档卡片 */
.wh-card {
  position:relative;
  background:var(--bg-glass,rgba(255,255,255,0.02));
  border:1px solid var(--border); border-radius:10px; padding:14px;
  cursor:pointer; transition:all 0.2s;
  display:flex; flex-direction:column; gap:10px;
}
.wh-card::before {
  content:''; position:absolute; top:0; left:12px; right:12px; height:1px;
  background:linear-gradient(90deg,transparent,var(--primary,rgba(108,92,231,0.3)),transparent);
  opacity:0; transition:all 0.3s;
}
.wh-card:hover { background:rgba(108,92,231,0.04); border-color:rgba(108,92,231,0.15); transform:translateY(-2px); }
.wh-card:hover::before { opacity:1; }

/* 卡片图标 */
.wh-card-icon { width:32px; height:32px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:15px; flex-shrink:0; }
.wh-card-content { flex:1; display:flex; flex-direction:column; gap:4px; }
.wh-card-title {
  font-size:14px; font-weight:600; color:var(--text); line-height:1.3;
  display:-webkit-box; -webkit-line-clamp:1; -webkit-box-orient:vertical; overflow:hidden;
}
.wh-card-preview {
  font-size:12px; color:var(--text3); opacity:0.5; line-height:1.5;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;
}

/* 卡片底部 */
.wh-card-footer { display:flex; align-items:center; justify-content:space-between; padding-top:6px; border-top:1px solid var(--border); }
.wh-card-date { font-size:11px; color:var(--text3); opacity:0.4; }
.wh-card-tag { font-size:10px; padding:1px 8px; border-radius:4px; }

/* 搜索无结果 */
.wh-no-result { grid-column:1/-1; display:flex; flex-direction:column; align-items:center; gap:8px; padding:40px 20px; font-size:13px; color:var(--text3); opacity:0.5; }
.wh-no-icon { font-size:24px; }

/* 空状态 */
.we-icon { display:flex; align-items:center; justify-content:center; margin-bottom:4px; }
.we-text { margin:0 0 12px; opacity:0.3; font-size:14px; color:var(--text3); }
.we-btn {
  display:inline-flex; align-items:center; gap:6px; padding:8px 18px;
  background:linear-gradient(135deg,rgba(108,92,231,0.12),rgba(0,206,201,0.06));
  border:1px solid rgba(108,92,231,0.15); border-radius:10px;
  color:var(--primary,#a29bfe); font-size:13px; cursor:pointer; transition:all 0.15s;
}
.we-btn:hover { background:linear-gradient(135deg,rgba(108,92,231,0.2),rgba(0,206,201,0.1)); border-color:rgba(108,92,231,0.3); }

.wiki-edit { display:flex; flex-direction:column; flex:1; min-height:0; }
.wiki-edit-scroll { flex:1; min-height:0; overflow-y:auto; }
.wiki-mode-btn { font-size: 11px !important; padding: 4px 8px !important; }
.wiki-mode-btn.active { background: rgba(108,92,231,0.15) !important; color: var(--primary) !important; border-color: rgba(108,92,231,0.3) !important; }
.wiki-html-textarea {
  width: 100%; height: 100%; min-height: 300px;
  background: #1a1a2e; color: #e0e0e0;
  border: none; outline: none; resize: none;
  padding: 16px 20px; font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px; line-height: 1.6; tab-size: 2;
}

/* 右键菜单 */
.wh-ctx {
  position: fixed; z-index: 9999;
  min-width: 120px;
  background: var(--bg-modal, #1a1a2e);
  border: 1px solid var(--border, rgba(255,255,255,0.1));
  border-radius: 8px; padding: 4px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.3);
}
.wh-ctx-item {
  padding: 7px 12px; font-size: 13px; color: var(--text2);
  border-radius: 6px; cursor: pointer; transition: all 0.1s;
}
.wh-ctx-item:hover { background: rgba(108,92,231,0.1); color: var(--primary); }

/* 弹窗遮罩 */
.wh-overlay {
  position: fixed; inset: 0; z-index: 9998;
  background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
}
.wh-dialog {
  background: var(--bg-modal, #1a1a2e);
  border: 1px solid var(--border, rgba(255,255,255,0.08));
  border-radius: 14px; width: 380px; max-width: 90vw;
  box-shadow: 0 16px 40px rgba(0,0,0,0.4);
  overflow: hidden;
}
.wh-dlg-title {
  padding: 16px 20px 0; font-size: 16px; font-weight: 700; color: var(--text);
}
.wh-dlg-body { padding: 16px 20px; display: flex; flex-direction: column; gap: 8px; }
.wh-dlg-body label { font-size: 12px; color: var(--text3); font-weight: 500; }
.wh-dlg-input, .wh-dlg-textarea {
  padding: 8px 10px; font-size: 13px; color: var(--text);
  background: var(--bg-input, rgba(255,255,255,0.04));
  border: 1px solid var(--border); border-radius: 8px; outline: none; width: 100%;
  box-sizing: border-box;
}
.wh-dlg-textarea { resize: none; }
.wh-dlg-input:focus, .wh-dlg-textarea:focus { border-color: rgba(108,92,231,0.3); }

/* 图标选择器 */
.wh-icon-picker {
  display: flex; flex-wrap: wrap; gap: 4px;
}
.wh-icon-opt {
  width: 34px; height: 34px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 8px; cursor: pointer; font-size: 16px;
  border: 1px solid transparent; transition: all 0.1s;
}
.wh-icon-opt:hover { background: rgba(108,92,231,0.08); }
.wh-icon-opt.active { background: rgba(108,92,231,0.15); border-color: rgba(108,92,231,0.3); }

.wh-dlg-actions {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 0 20px 16px;
}
.wh-btn-cancel, .wh-btn-save {
  padding: 7px 16px; font-size: 13px; border-radius: 8px; cursor: pointer; transition: all 0.12s;
}
.wh-btn-cancel {
  background: transparent; border: 1px solid var(--border); color: var(--text2);
}
.wh-btn-cancel:hover { background: rgba(255,255,255,0.04); }
.wh-btn-save {
  background: linear-gradient(135deg, rgba(108,92,231,0.2), rgba(0,206,201,0.1));
  border: 1px solid rgba(108,92,231,0.25); color: var(--primary, #a29bfe);
}
.wh-btn-save:hover { background: linear-gradient(135deg, rgba(108,92,231,0.3), rgba(0,206,201,0.15)); }
</style>
