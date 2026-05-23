import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const store = useUserStore()

  // 首次加载时检查访客模式状态
  if (!store._guestChecked) {
    await store.checkGuestStatus()
    store._guestChecked = true
    localStorage.setItem('guest_mode', store.guestModeEnabled ? '1' : '')
  }

  if (to.meta.requiresAuth && !store.isLoggedIn) {
    if (store.guestModeEnabled) {
      // 访客模式开启 → 直接进首页
      next()
    } else {
      next('/login')
    }
  } else if (to.meta.guest && store.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router
