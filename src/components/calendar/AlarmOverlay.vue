<template>
  <Teleport to="body">
    <Transition name="alarm">
      <div v-if="show" class="alarm-overlay" @click.self="dismiss">
        <div class="alarm-card">
          <div class="alarm-icon">🔔</div>
          <div class="alarm-label">🐟 摸鱼日历提醒</div>
          <div class="alarm-title">{{ todo?.title }}</div>
          <div class="alarm-time">{{ timeStr }}</div>
          <div class="alarm-actions">
            <button class="alarm-btn secondary" @click="snooze">稍后提醒<br><small>5分钟</small></button>
            <button class="alarm-btn primary" @click="dismiss">关闭</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  todo: { type: Object, default: null },
})
const emit = defineEmits(['dismiss', 'snooze'])

const timeStr = computed(() => {
  if (!props.todo?.reminder_at) return ''
  const d = new Date(props.todo.reminder_at)
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
})

function dismiss() { emit('dismiss') }
function snooze() { emit('snooze') }
</script>

<style scoped>
.alarm-overlay {
  position: fixed;
  inset: 0;
  z-index: 999999;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
}
.alarm-card {
  background: var(--bg-modal, #1a1a2e);
  border: 2px solid var(--primary, #6C5CE7);
  border-radius: 20px;
  padding: 40px 48px;
  text-align: center;
  box-shadow: 0 0 60px rgba(108, 92, 231, 0.3), 0 20px 60px rgba(0,0,0,0.5);
  max-width: 400px;
  width: 90vw;
  animation: pulse 0.6s ease;
}
@keyframes pulse {
  0% { transform: scale(0.85); opacity: 0; }
  50% { transform: scale(1.02); }
  100% { transform: scale(1); opacity: 1; }
}
.alarm-icon {
  font-size: 56px;
  margin-bottom: 16px;
  animation: bellRing 0.6s ease infinite alternate;
}
@keyframes bellRing {
  0% { transform: rotate(-12deg); }
  100% { transform: rotate(12deg); }
}
.alarm-label {
  font-size: 12px;
  color: var(--text3, rgba(255,255,255,0.5));
  margin-bottom: 12px;
  font-weight: 500;
  letter-spacing: 2px;
  text-transform: uppercase;
}
.alarm-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text, #fff);
  margin-bottom: 8px;
  line-height: 1.4;
}
.alarm-time {
  font-size: 13px;
  color: var(--text2, rgba(255,255,255,0.7));
  margin-bottom: 28px;
}
.alarm-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
.alarm-btn {
  padding: 12px 28px;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  min-width: 100px;
}
.alarm-btn.primary {
  background: var(--primary, #6C5CE7);
  color: #fff;
}
.alarm-btn.primary:hover {
  filter: brightness(1.15);
}
.alarm-btn.secondary {
  background: var(--bg-glass, rgba(255,255,255,0.05));
  color: var(--text2, rgba(255,255,255,0.7));
  border: 1px solid var(--border, rgba(255,255,255,0.08));
  font-size: 12px;
  line-height: 1.4;
}
.alarm-btn.secondary:hover {
  background: rgba(255,255,255,0.08);
}
.alarm-btn small {
  font-weight: 400;
  opacity: 0.7;
}

/* 过渡动画 */
.alarm-enter-active { transition: all 0.3s ease; }
.alarm-leave-active { transition: all 0.2s ease; }
.alarm-enter-from { opacity: 0; }
.alarm-leave-to { opacity: 0; }
</style>
