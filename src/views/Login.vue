<template>
  <div class="login-page" :class="{ 'light-theme': isLight }">
    <div class="bg-layer">
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
      <div class="bg-orb bg-orb-3"></div>
    </div>
    <div class="login-card">
      <!-- Logo -->
      <div class="logo-wrap">
        <svg class="logo-svg" viewBox="0 0 48 46" fill="none">
          <path d="M25.946 44.938c-.664.845-2.021.375-2.021-.698V33.937a2.26 2.26 0 0 0-2.262-2.262H10.287c-.92 0-1.456-1.04-.92-1.788l7.48-10.471c1.07-1.497 0-3.578-1.842-3.578H1.237c-.92 0-1.456-1.04-.92-1.788L10.013.474c.214-.297.556-.474.92-.474h28.894c.92 0 1.456 1.04.92 1.788l-7.48 10.471c-1.07 1.498 0 3.579 1.842 3.579h11.377c.943 0 1.473 1.088.89 1.83L25.947 44.94z" fill="url(#logo-grad)"/>
          <defs><linearGradient id="logo-grad" x1="0" y1="0" x2="48" y2="46"><stop offset="0%" stop-color="var(--primary)"/><stop offset="100%" stop-color="var(--accent)"/></linearGradient></defs>
        </svg>
        <span class="logo-text">轻鸿</span>
      </div>
      <p class="subtitle">登录到你的个人空间</p>

      <form @submit.prevent="handleLogin">
        <div class="field">
          <svg class="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>
          <input v-model="username" type="text" placeholder="账号" :disabled="loading" autocomplete="username" />
        </div>
        <div class="field">
          <svg class="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
          <input v-model="password" type="password" placeholder="密码" :disabled="loading" autocomplete="current-password" />
        </div>

        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

        <button type="submit" class="login-btn" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          <span v-else>登录</span>
        </button>
      </form>

      <!-- 快速切换账号 -->
      <div v-if="recentUsers.length > 0" class="accounts-section">
        <p class="accounts-label">快速切换</p>
        <div class="accounts-grid">
          <button
            v-for="(u, i) in visibleAccounts"
            :key="u.username"
            class="account-cell"
            :class="{ active: u.username === store.user?.username }"
            @click="switchUser(u)"
            :title="u.nickname"
          >
            <span class="cell-avatar">{{ u.nickname.charAt(0) }}</span>
            <div class="cell-info">
              <span class="cell-name">{{ u.nickname }}</span>
            </div>
          </button>
          <button v-if="recentUsers.length > maxVisible" class="account-cell account-more" @click="showAllAccounts = !showAllAccounts">
            <span class="cell-more-icon">{{ showAllAccounts ? '−' : '+' }}</span>
            <div class="cell-info">
              <span class="cell-name">{{ showAllAccounts ? '收起' : `+${recentUsers.length - maxVisible} 更多` }}</span>
            </div>
          </button>
        </div>
      </div>

      <!-- 忘记密码 / 新人注册 -->
      <div class="action-links">
        <button class="link-btn" @click="showHint('forgot')">忘记密码</button>
        <span class="link-dot">·</span>
        <button class="link-btn" @click="showHint('register')">新人注册</button>
      </div>

      <div class="footer-divider"></div>
      <div class="brand-bar">
        <span class="brand-name">鸿联九五</span>
        <span class="brand-dot">·</span>
        <span class="brand-product">
          <svg class="brand-svg" viewBox="0 0 48 46" fill="none"><path d="M25.946 44.938c-.664.845-2.021.375-2.021-.698V33.937a2.26 2.26 0 0 0-2.262-2.262H10.287c-.92 0-1.456-1.04-.92-1.788l7.48-10.471c1.07-1.497 0-3.578-1.842-3.578H1.237c-.92 0-1.456-1.04-.92-1.788L10.013.474c.214-.297.556-.474.92-.474h28.894c.92 0 1.456 1.04.92 1.788l-7.48 10.471c-1.07 1.498 0 3.579 1.842 3.579h11.377c.943 0 1.473 1.088.89 1.83L25.947 44.94z" fill="var(--text3)" opacity=".5"/></svg>
          轻鸿主页
        </span>
      </div>
    </div>

    <!-- 提示弹窗 -->
    <Teleport to="body">
      <div v-if="hintVisible" class="hint-overlay" @click.self="hintVisible = false">
        <div class="hint-card">
          <div class="hint-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          </div>
          <h3 class="hint-title">{{ hintTitle }}</h3>
          <p class="hint-text">请联系网站管理员处理</p>
          <button class="hint-btn" @click="hintVisible = false">知道了</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const isLight = ref(true)
const store = useUserStore()

onMounted(() => {
  const theme = localStorage.getItem('theme')
  isLight.value = theme !== 'dark'
})

const router = useRouter()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

// 快捷切换
const maxVisible = 6
const showAllAccounts = ref(false)
const recentUsers = computed(() => store.recentUsers || [])
const visibleAccounts = computed(() => {
  if (showAllAccounts.value) return recentUsers.value
  return recentUsers.value.slice(0, maxVisible)
})

async function switchUser(u) {
  try {
    await store.switchToUser(u)
    router.push('/')
  } catch {
    // token 失效，移除该条目
    store.removeRecentUser(u.username)
  }
}

// 提示弹窗
const hintVisible = ref(false)
const hintTitle = ref('')

function showHint(type) {
  hintTitle.value = type === 'forgot' ? '忘记密码' : '新人注册'
  hintVisible.value = true
}

async function handleLogin() {
  if (!username.value || !password.value) {
    errorMsg.value = '请输入账号和密码'
    return
  }
  loading.value = true
  errorMsg.value = ''
  try {
    await store.login(username.value, password.value)
    router.push('/')
  } catch (e) {
    errorMsg.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: #f0f2f5;
}
.login-page:not(.light-theme) {
  background: #0f0f1a;
}

/* ====== 背景光晕 ====== */
.bg-layer { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: .5;
}
.bg-orb-1 {
  width: 400px; height: 400px;
  background: var(--primary);
  top: -100px; left: -100px;
}
.bg-orb-2 {
  width: 350px; height: 350px;
  background: var(--accent);
  bottom: -80px; right: -80px;
}
.bg-orb-3 {
  width: 250px; height: 250px;
  background: var(--danger);
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  opacity: .25;
}

/* ====== 登录卡 ====== */
.login-card {
  position: relative;
  z-index: 1;
  width: 380px;
  background: var(--bg-card);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 44px 36px;
  box-shadow: 0 4px 24px rgba(0,0,0,.06), 0 1px 3px rgba(0,0,0,.04);
  transition: background .3s, border-color .3s;
}
:root:not(.light-theme) .login-card {
  background: rgba(255,255,255,.04);
  box-shadow: 0 8px 40px rgba(0,0,0,.4);
}

/* ====== Logo ====== */
.logo-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
  margin-bottom: 20px;
}
.logo-svg {
  width: 36px;
  height: 34px;
  flex-shrink: 0;
}
.logo-text {
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ====== 标题 ====== */
.subtitle {
  text-align: center;
  color: var(--text3);
  font-size: 14px;
  margin-bottom: 28px;
}

/* ====== 输入框 ====== */
.field {
  position: relative;
  margin-bottom: 14px;
}
.field-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: var(--text3);
  pointer-events: none;
  transition: color .2s;
}
.field input {
  width: 100%;
  padding: 13px 14px 13px 42px;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--text);
  font-size: 14px;
  outline: none;
  transition: all .2s;
}
.field input:focus {
  border-color: var(--primary);
  background: color-mix(in srgb, var(--primary) 6%, var(--bg));
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 12%, transparent);
}
.field input:focus ~ .field-icon,
.field:focus-within .field-icon {
  color: var(--primary);
}
:root:not(.light-theme) .field input {
  background: rgba(255,255,255,.06);
}
:root:not(.light-theme) .field input:focus {
  background: rgba(108,92,231,.08);
}

/* ====== 错误 ====== */
.error-msg {
  color: var(--danger);
  font-size: 13px;
  text-align: center;
  margin-bottom: 14px;
  padding: 8px 12px;
  background: color-mix(in srgb, var(--danger) 10%, transparent);
  border-radius: 8px;
}

/* ====== 按钮 ====== */
.login-btn {
  width: 100%;
  padding: 13px;
  background: linear-gradient(135deg, var(--primary), color-mix(in srgb, var(--primary) 70%, var(--accent)));
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all .25s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.login-btn:hover:not(:disabled) {
  opacity: .92;
  box-shadow: 0 4px 20px color-mix(in srgb, var(--primary) 35%, transparent);
  transform: translateY(-1px);
}
.login-btn:active:not(:disabled) {
  transform: translateY(0);
}
.login-btn:disabled {
  opacity: .6;
  cursor: not-allowed;
}

/* ====== 加载动画 ====== */
.spinner {
  width: 18px; height: 18px;
  border: 2px solid rgba(255,255,255,.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ====== 品牌栏 ====== */
.footer-divider {
  margin: 24px -36px 0;
  border: none;
  border-top: 1px solid var(--border);
}
.brand-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 14px 0 0;
  font-size: 12px;
}
.brand-name {
  font-weight: 600;
  color: var(--text2);
  letter-spacing: .5px;
}
.brand-dot {
  color: var(--border);
  font-size: 10px;
}
.brand-product {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text3);
}
.brand-svg {
  width: 14px;
  height: 13px;
  flex-shrink: 0;
}

/* ====== 快速切换 ====== */
.accounts-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
.accounts-label {
  font-size: 12px;
  color: var(--text3);
  margin-bottom: 10px;
  text-align: center;
}
.accounts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}
.account-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  transition: all .15s;
  text-align: left;
  font-family: inherit;
}
.account-cell:hover {
  border-color: var(--primary);
  background: color-mix(in srgb, var(--primary) 6%, var(--bg));
}
.account-cell.active {
  border-color: var(--primary);
  background: color-mix(in srgb, var(--primary) 8%, var(--bg));
}
.cell-avatar {
  width: 26px; height: 26px;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  background: var(--primary);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}
.cell-info {
  overflow: hidden;
  min-width: 0;
}
.cell-name {
  display: block;
  font-size: 12px;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.account-more {
  justify-content: center;
  border-style: dashed;
  background: transparent;
}
.account-more:hover {
  border-style: solid;
}
.cell-more-icon {
  width: 26px; height: 26px;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  background: var(--bg-glass);
  color: var(--text3);
  font-size: 16px;
  font-weight: 600;
  flex-shrink: 0;
  border: 1px solid var(--border);
}

/* ====== 操作链接 ====== */
.action-links {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 16px;
}
.link-btn {
  background: none;
  border: none;
  color: var(--text3);
  font-size: 13px;
  cursor: pointer;
  padding: 2px 4px;
  transition: color .15s;
}
.link-btn:hover {
  color: var(--primary);
}
.link-dot {
  color: var(--border);
  font-size: 10px;
}

/* ====== 提示弹窗 ====== */
.hint-overlay {
  position: fixed; inset: 0; z-index: 99999;
  background: rgba(0,0,0,.5);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
}
.hint-card {
  width: 300px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 32px 24px 24px;
  text-align: center;
  box-shadow: 0 12px 40px rgba(0,0,0,.3);
  animation: hintIn .2s ease;
}
@keyframes hintIn {
  from { opacity: 0; transform: scale(.95) translateY(8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.hint-icon { margin-bottom: 12px; }
.hint-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
}
.hint-text {
  font-size: 14px;
  color: var(--text2);
  margin-bottom: 20px;
}
.hint-btn {
  padding: 10px 36px;
  background: var(--primary);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity .15s;
}
.hint-btn:hover { opacity: .85; }
</style>
