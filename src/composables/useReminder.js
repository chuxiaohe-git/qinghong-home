import { ref, onMounted, onUnmounted } from 'vue'
import { getReminders, updateCalendarTodo } from '@/api/calendar'

// ── 共享状态（所有组件共享同一个提醒队列） ──
const alarms = ref([])
const showAlarm = ref(false)
const currentAlarm = ref(null)
let timer = null
let periodTimer = null
let channel = null
let scanning = false

export function useReminder() {
  // ── 请求通知权限 ──
  function requestPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }

  // ── 扫描提醒队列 ──
  async function scanReminders() {
    // 未登录时跳过（避免访客模式下的 401 报错）
    if (!localStorage.getItem('token')) { alarms.value = []; scanning = false; return }
    if (scanning) return
    scanning = true
    try {
      const res = await getReminders()
      alarms.value = (res.data || []).sort(
        (a, b) => new Date(a.reminder_at) - new Date(b.reminder_at)
      )
      scheduleNext()
    } catch {
      alarms.value = []
    }
    scanning = false
  }

  // ── 定期扫描 ──
  function startPeriodicScan() {
    clearInterval(periodTimer)
    periodTimer = setInterval(scanReminders, 30000)
  }

  // ── 设置下一个提醒定时器 ──
  function scheduleNext() {
    clearTimeout(timer)
    timer = null

    const now = Date.now()
    const next = alarms.value.find(a => {
      const t = new Date(a.reminder_at).getTime()
      return t > now
    })
    if (!next) return

    const delay = Math.max(0, new Date(next.reminder_at).getTime() - now)
    timer = setTimeout(() => fireAlarm(next), delay)
  }

  // ── 触发提醒 ──
  async function fireAlarm(todo) {
    // 标记已提醒
    try {
      await updateCalendarTodo(todo.id, { reminded: true })
      todo.reminded = true
    } catch {}

    // 浏览器通知
    sendNotification(todo)

    // 全屏闹铃
    currentAlarm.value = todo
    showAlarm.value = true

    // 通知其他标签页
    if (channel) {
      channel.postMessage({ type: 'alarm-fired', id: todo.id })
    }

    // 从队列移除
    alarms.value = alarms.value.filter(a => a.id !== todo.id)
    scheduleNext()
  }

  // ── 浏览器通知 ──
  function sendNotification(todo) {
    if (!('Notification' in window)) return
    if (Notification.permission !== 'granted') return
    try {
      new Notification('🐟 摸鱼日历提醒', {
        body: `「${todo.title}」到时间了！`,
        icon: '/favicon.svg',
        tag: 'cal-reminder-' + todo.id,
      })
    } catch {}
  }

  // ── 关闭闹铃 ──
  function dismissAlarm() {
    showAlarm.value = false
    currentAlarm.value = null
  }

  // ── 稍后提醒（+5分钟） ──
  async function snoozeAlarm() {
    if (!currentAlarm.value) return
    const todo = currentAlarm.value
    const newTime = new Date(Date.now() + 5 * 60 * 1000)
    const timeStr = formatDateTime(newTime)
    try {
      await updateCalendarTodo(todo.id, { reminder_at: timeStr })
      todo.reminder_at = timeStr
      todo.reminded = false
      // 重新扫描
      scanReminders()
    } catch {}
    dismissAlarm()
  }

  function formatDateTime(d) {
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    const h = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    return `${y}-${m}-${dd} ${h}:${min}`
  }

  // ── 初始化 ──
  function init() {
    requestPermission()
    scanReminders()
    startPeriodicScan()

    // BroadcastChannel 跨标签页同步
    try {
      channel = new BroadcastChannel('cal-reminder')
      channel.onmessage = (e) => {
        if (e.data.type === 'alarm-fired') {
          // 其他标签页已经触发了这个提醒，从本地队列移除
          alarms.value = alarms.value.filter(a => a.id !== e.data.id)
          scheduleNext()
        }
        if (e.data.type === 'rescan') {
          scanReminders()
        }
      }
    } catch {}
  }

  function notifyRescan() {
    scanReminders()
    if (channel) {
      channel.postMessage({ type: 'rescan' })
    }
  }

  onMounted(init)
  onUnmounted(() => {
    clearTimeout(timer)
    clearInterval(periodTimer)
    if (channel) channel.close()
  })

  return {
    alarms,
    showAlarm,
    currentAlarm,
    dismissAlarm,
    snoozeAlarm,
    notifyRescan,
  }
}
