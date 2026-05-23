<template>
  <div class="ai-chat">
    <div v-if="!configured" class="ai-empty">
      <div class="ai-empty-icon">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--text3)" stroke-width="1.5">
          <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z"/><path d="M20 12a8 8 0 0 1-16 0"/>
        </svg>
      </div>
      <h3>AI 对话未配置</h3>
      <p>前往设置 → AI 设置，配置 API 地址和 Key 后启用</p>
    </div>

    <template v-else>
      <!-- 侧边栏 -->
      <div class="chat-sidebar">
        <div class="sidebar-header">
          <div class="sidebar-title">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            历史对话
          </div>
          <button class="new-chat-btn" @click="newChat" title="新对话">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
          </button>
        </div>

        <div class="sidebar-search">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input type="text" placeholder="搜索对话记录..." v-model="searchConv" @input="filterConvs" />
        </div>

        <div class="chat-list">
          <div
            v-for="c in filteredConvs"
            :key="c.id"
            class="chat-item"
            :class="{ active: currentConvId === c.id }"
            @click="switchConv(c.id)"
            @contextmenu.prevent="openCtxMenu($event, c)"
          >
            <div class="chat-item-icon">{{ convIcon(c.title) }}</div>
            <div class="chat-item-info">
              <span class="chat-item-title">{{ c.title }}</span>
              <span class="chat-item-preview">{{ c.preview || '暂无消息' }}</span>
            </div>
          </div>
          <div v-if="filteredConvs.length === 0" class="chat-list-empty">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <span>{{ searchConv ? '无匹配结果' : '暂无对话记录' }}</span>
          </div>
        </div>

        <!-- 右键菜单 -->
        <Teleport to="body">
          <div v-if="ctxMenu.show" class="ctx-menu" :style="ctxMenu.style" @click.stop>
            <button class="ctx-item" @click="renameConv">✏️ 重命名</button>
            <button class="ctx-item" @click="clearConv">🗑️ 清空聊天记录</button>
            <button class="ctx-item ctx-danger" @click="deleteConv">✕ 删除对话</button>
          </div>
          <div v-if="ctxMenu.show" class="ctx-overlay" @click="closeCtxMenu"></div>
        </Teleport>
      </div>

      <!-- 主区域 -->
      <div class="chat-main">
        <!-- 头部 -->
        <div class="chat-header">
          <div class="chat-header-icon">🤖</div>
          <div>
            <div class="chat-header-title">
              AI 对话
              <span class="chat-header-status">● 在线</span>
            </div>
          </div>
          <span class="chat-model">{{ model }}</span>
          <div class="chat-header-actions">
            <button class="header-action-btn" @click="clearCurrentConv" title="清除上下文">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- 消息体 -->
        <div class="chat-body" ref="bodyRef">
          <div v-for="(msg, i) in messages" :key="i" class="msg-row" :class="msg.role === 'ai' || msg.role === 'assistant' ? 'ai' : 'user'">
            <div class="msg-avatar" :class="msg.role === 'ai' || msg.role === 'assistant' ? 'ai' : 'user'">
              <span v-if="msg.role === 'ai' || msg.role === 'assistant'" class="ai-emoji">🤖</span>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 1 1 16 0"/>
              </svg>
            </div>
            <div class="msg-bubble">
              <div v-if="msg.toolCalls" class="tool-hint">
                <div class="tool-hint-label">🛠 正在处理</div>
                <div v-for="tc in msg.toolCalls" :key="tc.tool" class="tool-item" :class="{ done: tc.done }">
                  <span class="tool-spinner" v-if="!tc.done"></span>
                  <div v-else class="tool-done-icon">
                    <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--accent, #00CEC9)" stroke-width="4">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </div>
                  <span>{{ toolLabel(tc.tool) }}</span>
                </div>
              </div>
              <div v-if="msg.content" class="msg-text" v-html="rendered(msg.content)"></div>
            </div>
          </div>

          <!-- 流式回复 -->
          <div v-if="streaming" class="msg-row ai">
            <div class="msg-avatar ai"><span class="ai-emoji">🤖</span></div>
            <div class="msg-bubble">
              <div class="msg-text" v-if="streamText" v-html="rendered(streamText)"></div>
              <div v-else class="typing"><span></span><span></span><span></span></div>
            </div>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="chat-input-area">
          <div class="input-wrapper">
            <div class="input-tools">
              <button class="input-tool-btn" title="上传文件" @click="handleAttach">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
              </button>
            </div>
            <textarea
              v-model="inputText"
              @keydown.enter.prevent="sendMessage"
              placeholder="输入消息，Enter 发送，Shift+Enter 换行..."
              :disabled="streaming"
              rows="1"
            ></textarea>
            <button class="send-btn" :disabled="!inputText.trim() || streaming" @click="sendMessage">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
          <div class="input-footer">
            <div class="input-footer-text">
              <span></span>
              模型已就绪
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { streamChat } from '@/api/ai'
import { getSettings } from '@/api/settings'
import { getConversations, createConversation, getConversation, updateConversation, deleteConversation as apiDelConv } from '@/api/conversation'
import MarkdownIt from 'markdown-it'

// markdown-it 实例，带自定义代码块渲染
const md = new MarkdownIt({
  html: false,
  breaks: true,   // 单换行 → <br>
  linkify: false,
  typographer: false,
})

// 自定义 fence（``` 代码块）渲染，添加头部 + 复制按钮
md.renderer.rules.fence = (tokens, idx) => {
  const token = tokens[idx]
  const lang = token.info || 'code'
  const code = token.content.trim()
  const encoded = btoa(unescape(encodeURIComponent(code)))
  return `<pre><div class="pre-header"><span class="pre-lang">${lang}</span><button class="pre-copy-btn" data-code="${encoded}">复制</button></div><code>${code}</code></pre>`
}

const bodyRef = ref(null)
const inputText = ref('')
const messages = ref([])
const streaming = ref(false)
const streamText = ref('')
const configured = ref(false)
const model = ref('')

// 对话管理
const conversations = ref([])
const currentConvId = ref(null)
const loadingConv = ref(false)

// 侧边栏搜索
const searchConv = ref('')

// 右键菜单
const ctxMenu = ref({ show: false, conv: null, style: {} })
const ctxTarget = ref(null)

// 对话图标
const CONV_ICONS = ['💡', '📊', '💻', '✍️', '🎨', '🔍', '📝', '🎯', '🧩', '⚙️']
function convIcon(title) {
  if (!title) return CONV_ICONS[0]
  const code = title.charCodeAt(0) || 0
  return CONV_ICONS[Math.abs(code) % CONV_ICONS.length]
}

// 对话搜索过滤
const filteredConvs = computed(() => {
  const q = searchConv.value.trim().toLowerCase()
  if (!q) return conversations.value
  return conversations.value.filter(c => c.title.toLowerCase().includes(q))
})
function filterConvs() {} // 纯 computed 驱动

function openCtxMenu(e, conv) {
  ctxMenu.value = {
    show: true,
    conv,
    style: { left: e.clientX + 'px', top: e.clientY + 'px' },
  }
  ctxTarget.value = conv
}
function closeCtxMenu() {
  ctxMenu.value = { show: false, conv: null, style: {} }
  ctxTarget.value = null
}

async function renameConv() {
  const c = ctxTarget.value
  if (!c) return
  closeCtxMenu()
  const newName = prompt('请输入新名称：', c.title)
  if (!newName || newName === c.title) return
  try {
    await updateConversation(c.id, { title: newName })
    c.title = newName
  } catch {}
}

async function clearConv() {
  const c = ctxTarget.value
  if (!c) return
  closeCtxMenu()
  if (!confirm('确定清空「' + c.title + '」的聊天记录？')) return
  try {
    await updateConversation(c.id, { messages: [] })
    if (currentConvId.value === c.id) {
      messages.value = []
    }
  } catch {}
}

async function deleteConv() {
  const c = ctxTarget.value
  if (!c) return
  closeCtxMenu()
  if (!confirm('确定删除对话「' + c.title + '」？')) return
  await delConv(c.id)
}

async function clearCurrentConv() {
  if (!currentConvId.value) return
  const c = conversations.value.find(c => c.id === currentConvId.value)
  if (!c) return
  if (!confirm('确定清空当前对话记录？')) return
  try {
    await updateConversation(currentConvId.value, { messages: [] })
    messages.value = []
  } catch {}
}

function handleAttach() {
  // 预留：文件上传
}

onMounted(async () => {
  try {
    const res = await getSettings()
    const cfg = JSON.parse(res.data?.layout_config || '{}')
    configured.value = !!cfg.ai_enabled
    model.value = cfg.ai_model || 'deepseek-chat'
  } catch {}
  if (configured.value) {
    await loadConversations()
  }

  // 代码块复制 — 全局事件委托
  document.addEventListener('click', copyCodeHandler)
})

function copyCodeHandler(e) {
  const btn = e.target.closest('.pre-copy-btn')
  if (!btn) return
  const encoded = btn.getAttribute('data-code')
  if (!encoded) return
  try {
    const text = decodeURIComponent(escape(atob(encoded)))
    navigator.clipboard.writeText(text)
    btn.textContent = '已复制'
    setTimeout(() => { btn.textContent = '复制' }, 2000)
  } catch {}
}

async function loadConversations() {
  try {
    const res = await getConversations()
    conversations.value = res.data || []
    if (conversations.value.length > 0) {
      await switchConv(conversations.value[0].id)
    } else {
      await newChat()
    }
  } catch {}
}

async function newChat() {
  try {
    const res = await createConversation()
    conversations.value.unshift(res.data)
    currentConvId.value = res.data.id
    messages.value = []
    messages.value.push({
      role: 'ai',
      content: '你好！我是你的 AI 助手 👋\n\n我可以帮你：\n- 💬 聊天问答\n- 🔖 管理书签和收藏\n- 📝 创建和管理待办事项\n- 📓 记录笔记和灵感\n\n有什么可以帮你的吗？',
    })
    await saveMessages()
    scrollBottom()
  } catch {}
}

async function switchConv(id) {
  if (loadingConv.value || id === currentConvId.value) return
  loadingConv.value = true
  currentConvId.value = id
  try {
    const res = await getConversation(id)
    messages.value = (res.data?.messages || []).filter(m => m.role !== 'system')
  } catch {
    messages.value = []
  }
  loadingConv.value = false
  scrollBottom()
}

async function delConv(id) {
  try {
    await apiDelConv(id)
    conversations.value = conversations.value.filter(c => c.id !== id)
    if (currentConvId.value === id) {
      if (conversations.value.length > 0) {
        await switchConv(conversations.value[0].id)
      } else {
        await newChat()
      }
    }
  } catch {}
}

async function saveMessages() {
  if (!currentConvId.value) return
  const msgs = messages.value.map(m => ({
    role: m.role === 'ai' ? 'assistant' : 'user',
    content: m.content || '',
  }))
  await updateConversation(currentConvId.value, { messages: msgs })
}

function toolLabel(name) {
  const labels = {
    add_bookmark: '添加书签', search_bookmarks: '搜索书签', list_bookmarks: '列出书签',
    delete_bookmark: '删除书签', add_todo: '添加待办', list_todos: '查看待办',
    toggle_todo: '更新待办', delete_todo: '删除待办', create_note: '创建笔记',
    list_groups: '查看分组', create_group: '创建分组',
  }
  return labels[name] || name
}

function rendered(text) {
  if (!text) return ''
  text = text.replace(/^([a-zA-Z+#]+)复制/gm, '```$1')
  return md.render(text)
}

function scrollBottom() {
  nextTick(() => { if (bodyRef.value) bodyRef.value.scrollTop = bodyRef.value.scrollHeight })
}

function sendMessage() {
  const text = inputText.value.trim()
  if (!text || streaming.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  scrollBottom()

  const apiMessages = messages.value.map(m => ({
    role: m.role === 'ai' ? 'assistant' : 'user',
    content: m.content || '',
  }))

  streaming.value = true
  streamText.value = ''
  let currentToolCalls = []

  streamChat(apiMessages, {
    onData: (data) => {
      if (data.type === 'text') {
        streamText.value += data.content; scrollBottom()
      } else if (data.type === 'tool_start') {
        currentToolCalls.push({ tool: data.tool, done: false })
      } else if (data.type === 'tool_end') {
        const tc = currentToolCalls.find(t => t.tool === data.tool)
        if (tc) tc.done = true
      } else if (data.type === 'error') {
        streamText.value += '\n\n⚠️ ' + data.content
      }
    },
    onError: (err) => {
      const msg = err.message || ''
      let chineseMsg = '请求失败'
      if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) chineseMsg = '无法连接到服务器'
      else if (msg.includes('400')) chineseMsg = '请求参数错误'
      else if (msg.includes('timeout') || msg.includes('Timeout')) chineseMsg = '连接超时'
      else chineseMsg = '请求失败: ' + msg
      messages.value.push({ role: 'ai', content: '⚠️ ' + chineseMsg, toolCalls: currentToolCalls.length > 0 ? currentToolCalls : undefined })
      streaming.value = false
      currentToolCalls = []
      saveMessages()
      scrollBottom()
    },
    onDone: async () => {
      if (streamText.value) {
        messages.value.push({ role: 'ai', content: streamText.value, toolCalls: currentToolCalls.length > 0 ? currentToolCalls.map(t => ({ ...t, done: true })) : undefined })
      }
      streaming.value = false
      streamText.value = ''
      currentToolCalls = []
      await saveMessages()
      scrollBottom()
      window.dispatchEvent(new CustomEvent('ai-action-done'))
    },
  })
}
</script>

<style scoped>
.ai-chat {
  display: flex;
  height: calc(100% - 12px);
  margin-top: 12px;
  border-radius: 12px;
  border: 1px solid var(--border);
  overflow: hidden;
  background: color-mix(in srgb, var(--bg-card) 85%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

/* ====== 空状态 ====== */
.ai-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  width: 100%; gap: 12px; padding: 40px; text-align: center;
}
.ai-empty h3 { font-size: 16px; font-weight: 600; color: var(--text2); }
.ai-empty p { font-size: 13px; color: var(--text3); line-height: 1.6; max-width: 280px; }

/* ====== 侧边栏 ====== */
.chat-sidebar {
  width: 220px; flex-shrink: 0;
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column; overflow: hidden;
}
.sidebar-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 14px; border-bottom: 1px solid var(--border);
}
.sidebar-title {
  font-size: 13px; font-weight: 600; color: var(--text2);
  display: flex; align-items: center; gap: 6px; letter-spacing: .5px;
}
.sidebar-title svg { opacity: .6; }
.new-chat-btn {
  width: 32px; height: 32px;
  border-radius: 8px; border: 1px solid var(--border);
  background: var(--bg-glass); color: var(--text2);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all .2s; flex-shrink: 0;
}
.new-chat-btn:hover {
  background: var(--primary); border-color: var(--primary); color: #fff;
  box-shadow: 0 0 12px rgba(108,92,231,.4);
}
.new-chat-btn svg { transition: transform .3s; }
.new-chat-btn:hover svg { transform: rotate(90deg); }

.sidebar-search {
  padding: 10px 12px; position: relative; flex-shrink: 0;
}
.sidebar-search input {
  width: 100%; height: 34px;
  padding: 0 10px 0 32px;
  border-radius: 8px; border: 1px solid var(--border);
  background: var(--bg-glass); color: var(--text);
  font-size: 12px; outline: none; font-family: inherit;
  transition: border-color .2s;
}
.sidebar-search input:focus { border-color: var(--primary); }
.sidebar-search input::placeholder { color: var(--text3); }
.sidebar-search svg {
  position: absolute; left: 20px; top: 50%;
  transform: translateY(-50%); opacity: .35; pointer-events: none;
}

.chat-list {
  flex: 1; overflow-y: auto; padding: 6px 8px 8px;
  display: flex; flex-direction: column; gap: 2px;
}
.chat-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 10px; border-radius: 10px;
  cursor: pointer; transition: all .2s;
  border: 1px solid transparent;
}
.chat-item:hover { background: var(--bg-glass); border-color: var(--border); }
.chat-item.active {
  background: linear-gradient(135deg, rgba(108,92,231,.12), rgba(0,206,201,.06));
  border-color: rgba(108,92,231,.25);
}
.chat-item-icon {
  width: 30px; height: 30px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; flex-shrink: 0; transition: transform .2s;
}
.chat-item:hover .chat-item-icon { transform: scale(1.08); }
.chat-item.active .chat-item-icon {
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: #fff; box-shadow: 0 0 10px rgba(108,92,231,.3);
}
.chat-item-info { flex: 1; min-width: 0; }
.chat-item-title {
  font-size: 12.5px; color: var(--text); font-weight: 500;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  display: block; line-height: 1.3;
}
.chat-item-preview {
  font-size: 11px; color: var(--text3);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  display: block; margin-top: 2px;
}
.chat-list-empty {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 8px;
  padding: 40px 20px; text-align: center;
}
.chat-list-empty svg { opacity: .25; }
.chat-list-empty span { font-size: 12px; color: var(--text3); }

/* ====== 右键菜单 ====== */
.ctx-overlay { position: fixed; inset: 0; z-index: 99998; }
.ctx-menu {
  position: fixed; z-index: 99999; min-width: 160px;
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 10px; padding: 4px; box-shadow: 0 4px 16px rgba(0,0,0,.15);
}
.ctx-item {
  display: block; width: 100%; padding: 8px 12px; border: none; background: none;
  font-size: 13px; color: var(--text); cursor: pointer; border-radius: 6px;
  text-align: left; font-family: inherit;
}
.ctx-item:hover { background: var(--bg-glass); }
.ctx-danger:hover { background: color-mix(in srgb, var(--danger) 15%, var(--bg)); color: var(--danger); }

/* ====== 主区域 ====== */
.chat-main { flex: 1; display: flex; flex-direction: column; min-width: 0; background: var(--bg); }

/* 头部 */
.chat-header {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 18px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  background: var(--bg-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  position: relative; z-index: 2;
}
.chat-header-icon {
  width: 34px; height: 34px; border-radius: 10px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; flex-shrink: 0;
}
.chat-header-title {
  font-size: 14px; font-weight: 600;
  display: flex; align-items: center; gap: 6px;
}
.chat-header-status {
  font-size: 10px; padding: 2px 8px; border-radius: 20px;
  background: rgba(0,206,201,.12); color: var(--accent); font-weight: 500;
}
.chat-header-actions {
  margin-left: auto; display: flex; gap: 6px; align-items: center;
}
.header-action-btn {
  width: 32px; height: 32px; border-radius: 8px;
  border: 1px solid var(--border); background: transparent;
  color: var(--text3); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s;
}
.header-action-btn:hover {
  background: var(--bg-glass); color: var(--text2); border-color: var(--border-light);
}
.chat-model {
  font-size: 10px; padding: 3px 10px; border-radius: 20px;
  background: var(--bg-glass); color: var(--text3);
  border: 1px solid var(--border); font-weight: 500;
}

/* 消息体 */
.chat-body {
  flex: 1; overflow-y: auto; padding: 18px;
  display: flex; flex-direction: column; gap: 16px;
}

.msg-row {
  display: flex; gap: 12px; max-width: 85%;
  animation: msgIn .35s ease both;
}
.msg-row.user { align-self: flex-end; flex-direction: row-reverse; }
.msg-row.ai { align-self: flex-start; }

@keyframes msgIn {
  from { opacity: 0; transform: translateY(12px) scale(.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.msg-avatar {
  width: 34px; height: 34px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; font-size: 16px; position: relative;
}
.msg-avatar.ai {
  background: linear-gradient(135deg, rgba(108,92,231,.15), rgba(0,206,201,.1));
  border: 1px solid rgba(108,92,231,.2);
}
.msg-avatar.user {
  background: linear-gradient(135deg, var(--primary), #8b7cf7);
  color: #fff; box-shadow: 0 2px 8px rgba(108,92,231,.25);
}
.ai-emoji { line-height: 1; }

.msg-bubble {
  padding: 12px 16px; border-radius: 12px;
  font-size: 13.5px; line-height: 1.65;
  min-width: 0; word-break: break-word; position: relative;
}
.msg-row.user .msg-bubble {
  background: linear-gradient(135deg, var(--primary), #5a4bd4);
  color: #fff; border-bottom-right-radius: 4px;
  box-shadow: 0 2px 8px rgba(108,92,231,.2);
}
.msg-row.ai .msg-bubble {
  background: var(--bg-glass); backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid var(--border); border-bottom-left-radius: 4px;
  color: var(--text);
}

/* 气泡尾巴 */
.msg-row.ai .msg-bubble::before {
  content: ''; position: absolute; left: -6px; top: 14px;
  width: 10px; height: 10px;
  background: var(--bg-glass);
  border-left: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  transform: rotate(45deg);
}
.msg-row.user .msg-bubble::after {
  content: ''; position: absolute; right: -6px; top: 14px;
  width: 10px; height: 10px;
  background: var(--primary); transform: rotate(45deg);
  border-radius: 0 0 2px 0;
}

/* Markdown 样式 */
.msg-text :is(h1, h2, h3, h4) { margin: 10px 0 6px; line-height: 1.3; }
.msg-text h1 { font-size: 18px; font-weight: 700; }
.msg-text h2 { font-size: 16px; font-weight: 700; }
.msg-text h3 { font-size: 14px; font-weight: 600; }
.msg-text p { margin: 4px 0; }
.msg-text ul, .msg-text ol { padding-left: 20px; margin: 6px 0; }
.msg-text li { margin: 3px 0; }
.msg-text strong { font-weight: 600; }

/* 表格 — :deep() 穿透 scoped CSS 限制，匹配 v-html 插入的 DOM */
.msg-text :deep(table) {
  border-collapse: collapse; margin: 8px 0; width: 100%; font-size: 12.5px;
  background: var(--bg-glass);
}
.msg-text :deep(th), .msg-text :deep(td) {
  border: 1px solid rgba(128,128,128,.15); padding: 7px 12px; text-align: left;
}
.msg-text :deep(th) {
  background: rgba(108,92,231,.08); font-weight: 600; color: var(--text2);
  font-size: 11.5px;
}
.msg-text :deep(tbody tr:hover) {
  background: rgba(255,255,255,.03);
}
/* 分隔线 */
.msg-text :deep(hr) {
  border: none; height: 1px; background: var(--border); margin: 12px 0;
}

/* ====== 代码块（:deep 穿透 v-html） ====== */
.msg-text :deep(code) {
  background: rgba(108,92,231,.1); padding: 1px 6px; border-radius: 4px;
  font-size: 12.5px; color: var(--text);
  border: 1px solid rgba(108,92,231,.08);
}
.msg-row.user .msg-text :deep(code) {
  background: rgba(255,255,255,.12); color: #fff; border-color: rgba(255,255,255,.1);
}

.msg-text :deep(pre) {
  background: #1a1a2e; border: 1px solid rgba(108,92,231,.2);
  border-radius: 10px; margin: 8px 0; overflow: hidden;
}
.msg-text :deep(.pre-header) {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 12px; background: rgba(108,92,231,.1);
  border-bottom: 1px solid rgba(108,92,231,.15);
  font-size: 11px; color: #b0b0d0; font-family: inherit;
}
.msg-text :deep(.pre-lang) {
  display: flex; align-items: center; gap: 4px; color: #c0c0e0;
}
.msg-text :deep(.pre-copy-btn) {
  background: none; border: 1px solid rgba(108,92,231,.15);
  color: #9090b0; cursor: pointer;
  font-size: 11px; padding: 2px 8px; border-radius: 4px;
  transition: all .2s; font-family: inherit;
}
.msg-text :deep(.pre-copy-btn:hover) {
  color: #d0d0ff; border-color: rgba(108,92,231,.3);
}

.msg-text :deep(pre code) {
  display: block; padding: 12px 14px; background: none; border: none;
  color: #e0e0ff; font-size: 12.5px; line-height: 1.6; overflow-x: auto;
}

/* 工具调用 */
.tool-hint {
  margin-bottom: 10px; padding: 10px 12px;
  background: rgba(108,92,231,.06); border-radius: 8px;
  border: 1px solid rgba(108,92,231,.1);
}
.tool-hint-label {
  font-size: 10px; color: var(--text3); font-weight: 600;
  letter-spacing: .3px; margin-bottom: 4px;
}
.tool-item {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; color: var(--text3); transition: color .3s;
}
.tool-item.done { color: var(--accent); }
.tool-spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(108,92,231,.15); border-top-color: var(--primary);
  border-radius: 50%; animation: spin .7s linear infinite; flex-shrink: 0;
}
.tool-done-icon {
  width: 14px; height: 14px; border-radius: 50%;
  background: rgba(0,206,201,.15);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 打字动画 */
.typing { display: flex; gap: 5px; padding: 4px 2px; align-items: center; }
.typing span {
  width: 7px; height: 7px; border-radius: 50%; background: var(--text3);
  animation: dot 1.4s infinite;
}
.typing span:nth-child(2) { animation-delay: .2s; }
.typing span:nth-child(3) { animation-delay: .4s; }
@keyframes dot {
  0%,60%,100% { opacity: .25; transform: scale(1); }
  30% { opacity: 1; transform: scale(1.2); background: var(--primary); }
}

/* 输入区 */
.chat-input-area {
  padding: 12px 18px 14px;
  border-top: 1px solid var(--border); flex-shrink: 0;
  background: var(--bg-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  position: relative; z-index: 2;
}
.input-wrapper {
  display: flex; gap: 8px; align-items: flex-end;
  background: var(--bg-glass); border: 1px solid var(--border);
  border-radius: 12px; padding: 4px;
  transition: border-color .25s, box-shadow .25s;
}
.input-wrapper:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(108,92,231,.08);
}
.input-tools {
  display: flex; align-items: center; gap: 2px; padding: 0 2px;
}
.input-tool-btn {
  width: 32px; height: 32px; border-radius: 8px;
  border: none; background: transparent; color: var(--text3);
  cursor: pointer; display: flex; align-items: center;
  justify-content: center; transition: all .2s; flex-shrink: 0;
}
.input-tool-btn:hover { background: var(--bg-glass2, rgba(0,0,0,.04)); color: var(--text2); }

.chat-input-area textarea {
  flex: 1; border: none; background: transparent;
  padding: 8px 4px; font-size: 13.5px; color: var(--text);
  resize: none; outline: none; font-family: inherit;
  line-height: 1.5; min-height: 24px; max-height: 120px;
}
.chat-input-area textarea::placeholder { color: var(--text3); }

.send-btn {
  width: 38px; height: 38px; border-radius: 10px; border: none;
  background: linear-gradient(135deg, var(--primary), #5a4bd4);
  color: #fff; cursor: pointer; display: flex;
  align-items: center; justify-content: center; flex-shrink: 0;
  transition: all .25s; position: relative; overflow: hidden;
}
.send-btn::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(135deg, transparent, rgba(255,255,255,.1));
  opacity: 0; transition: opacity .25s;
}
.send-btn:hover:not(:disabled)::before { opacity: 1; }
.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 2px 12px rgba(108,92,231,.35);
}
.send-btn:active:not(:disabled) { transform: scale(.95); }
.send-btn:disabled {
  background: var(--bg-glass2, rgba(128,128,128,.1));
  color: var(--text3); cursor: not-allowed; box-shadow: none !important;
}

.input-footer {
  margin-top: 6px; padding: 0 4px;
  display: flex; justify-content: flex-end;
}
.input-footer-text {
  font-size: 10.5px; color: var(--text3);
  display: flex; align-items: center; gap: 4px;
}
.input-footer-text span {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent); display: inline-block;
}

/* 滚动条 */
.chat-body::-webkit-scrollbar,
.chat-list::-webkit-scrollbar { width: 5px; }
.chat-body::-webkit-scrollbar-track,
.chat-list::-webkit-scrollbar-track { background: transparent; }
.chat-body::-webkit-scrollbar-thumb,
.chat-list::-webkit-scrollbar-thumb {
  background: rgba(128,128,128,.15); border-radius: 3px;
}
.chat-body::-webkit-scrollbar-thumb:hover,
.chat-list::-webkit-scrollbar-thumb:hover {
  background: rgba(128,128,128,.3);
}
</style>
