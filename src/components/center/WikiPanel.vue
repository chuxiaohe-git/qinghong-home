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
        <div class="wiki-view-body" v-html="docContent"></div>
      </div>
      <!-- 编辑模式 -->
      <div v-else class="wiki-edit">
        <div class="wiki-bar">
          <input class="wiki-title" v-model="docTitle" placeholder="文档标题" />
          <div class="wiki-bar-actions">
            <span v-if="saved" class="wiki-saved">已保存</span>
            <button class="wiki-btn" @click="saveDoc">保存</button>
            <button class="wiki-btn" @click="cancelEdit">取消</button>
          </div>
        </div>
        <div class="wiki-edit-scroll">
          <Editor
            v-model="docContent"
            tinymce-script-src="/tinymce/tinymce.min.js"
            license-key="gpl"
            :init="editorConfig"
            :disabled="false"
          />
        </div>
      </div>
    </div>
    <div v-else-if="wikiDocs && wikiDocs.length > 0" class="wiki-home">
      <div class="wiki-bar">
        <h1 class="wiki-title-view">📖 摸鱼WIKI</h1>
      </div>
      <div class="wiki-home-body">
        <div class="wiki-home-grid">
          <div
            v-for="doc in wikiDocs"
            :key="doc.id"
            class="wiki-home-card"
            @click="$emit('select-doc', doc.id)"
          >
            <div class="wiki-home-card-title">{{ doc.title || '未命名' }}</div>
            <div class="wiki-home-card-meta">
              更新于 {{ formatDate(doc.updated_at) }}
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="wiki-empty">
      <div class="wiki-empty-icon">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" opacity="0.3"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
      </div>
      <p>在左侧 WIKI 目录中新建一个文档</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import Editor from '@tinymce/tinymce-vue'
import { updateWikiDoc, deleteWikiDoc, uploadWikiImage } from '@/api/wiki'

const props = defineProps({
  currentDoc: { type: Object, default: null },
  wikiDocs: { type: Array, default: () => [] },
})
const emit = defineEmits(['close-doc', 'doc-updated', 'doc-deleted', 'select-doc'])

const docTitle = ref('')
const docContent = ref('')
const loading = ref(false)
const saved = ref(true)
const editing = ref(false)

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

function enterEdit() {
  editing.value = true
}

function cancelEdit() {
  if (props.currentDoc) {
    docTitle.value = props.currentDoc.title ?? ''
    docContent.value = props.currentDoc.content ?? ''
  }
  editing.value = false
}

watch(() => props.currentDoc, (doc) => {
  loading.value = true
  if (doc) {
    editing.value = false
    docTitle.value = doc.title ?? ''
    docContent.value = doc.content ?? ''
    saved.value = true
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

.wiki-home { flex:1; display:flex; flex-direction:column; min-height:0; }
.wiki-home-body { flex:1; overflow-y:auto; padding:20px 24px; }
.wiki-home-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:12px; }
.wiki-home-card {
  background:rgba(255,255,255,0.03); border:1px solid var(--border); border-radius:10px; padding:16px;
  cursor:pointer; transition:all 0.15s; display:flex; flex-direction:column; gap:8px;
}
.wiki-home-card:hover {
  background:rgba(108,92,231,0.06); border-color:rgba(108,92,231,0.15); transform:translateY(-1px);
}
.wiki-home-card-title { font-size:14px; font-weight:600; color:var(--text); line-height:1.4; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.wiki-home-card-meta { font-size:11px; color:var(--text3); opacity:0.6; }

.wiki-edit { display:flex; flex-direction:column; flex:1; min-height:0; }
.wiki-edit-scroll { flex:1; min-height:0; overflow-y:auto; }
</style>
