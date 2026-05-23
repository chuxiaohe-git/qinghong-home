import { defineStore } from 'pinia'
import { login as loginApi, getMe } from '@/api/auth'
import { getGuestStatus } from '@/api/guest'
import axios from 'axios'

const RECENT_KEY = 'recent_users'

function getRecent() {
  try { return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]') } catch { return [] }
}

function saveRecent(list) {
  localStorage.setItem(RECENT_KEY, JSON.stringify(list))
}

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    guestModeEnabled: false,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
    isGuest: (state) => !state.token && state.guestModeEnabled,
    nickname: (state) => state.user?.nickname || state.user?.username || '',
    recentUsers: () => getRecent(),
  },
  actions: {
    async checkGuestStatus() {
      try {
        const res = await getGuestStatus()
        this.guestModeEnabled = res.data?.enabled === true
      } catch {
        this.guestModeEnabled = false
      }
    },
    async login(username, password) {
      const res = await loginApi(username, password)
      this.token = res.data.token
      this.user = res.data.user
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('user', JSON.stringify(this.user))
      this.saveRecentUser()
    },
    saveRecentUser() {
      const list = getRecent().filter(u => u.username !== this.user?.username)
      list.unshift({
        username: this.user?.username,
        nickname: this.user?.nickname || this.user?.username,
        avatar: this.user?.avatar || '',
        role: this.user?.role || '',
        token: this.token,
      })
      saveRecent(list)
    },
    removeRecentUser(username) {
      const list = getRecent().filter(u => u.username !== username)
      saveRecent(list)
    },
    async switchToUser(userData) {
      if (userData.username === this.user?.username) return
      if (userData.token === this.token) return

      // 临时切换到目标 token 做静默验证
      this.token = userData.token
      localStorage.setItem('token', userData.token)

      try {
        // 用原生 axios 调 API（不走 request 拦截器，避免 401 自动跳转）
        await axios.get('/api/auth/me', {
          headers: { Authorization: `Bearer ${userData.token}` }
        })
        // 验证通过 → 切换
        this.user = {
          username: userData.username,
          nickname: userData.nickname || userData.username,
          avatar: userData.avatar || '',
          role: userData.role || '',
        }
        localStorage.setItem('user', JSON.stringify(this.user))
        this.saveRecentUser()
        location.reload()
      } catch {
        // 验证失败 → 移除该账号记录 → 清空 token 跳登录页
        this.removeRecentUser(userData.username)
        this.token = ''
        this.user = null
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
    },
    async fetchUser() {
      try {
        const res = await getMe()
        this.user = res.data
        localStorage.setItem('user', JSON.stringify(res.data))
      } catch {
        this.logout()
      }
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
    updateUser(data) {
      this.user = { ...this.user, ...data }
      localStorage.setItem('user', JSON.stringify(this.user))
    },
  },
})
