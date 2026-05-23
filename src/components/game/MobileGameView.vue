<template>
  <div class="mg-view" :class="{ landscape: isLandscape }">
    <!-- 横屏提示 -->
    <div v-if="!isLandscape" class="mg-rotate-hint">
      <div class="mg-phone-icon">📱</div>
      <div class="mg-rotate-text">请横屏使用</div>
      <div class="mg-rotate-sub">将手机旋转至横屏模式</div>
      <button class="mg-fs-btn" @click="toggleFullscreen">⛶ 进入全屏</button>
      <button class="mg-back-btn" @click="$emit('close')">← 返回</button>
    </div>

    <!-- 游戏区域 -->
    <div v-show="isLandscape" class="mg-game-wrap" ref="gameWrapRef">
      <DashGame />
      <div class="mg-top-btns">
        <button class="mg-top-btn" @click="toggleFullscreen" title="全屏">⛶</button>
        <button class="mg-top-btn" @click="$emit('close')">✕</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import DashGame from '@/components/center/DashGame.vue'

defineEmits(['close'])

const isLandscape = ref(window.innerWidth > window.innerHeight)
const gameWrapRef = ref(null)
const GAME_W = 264, GAME_H = 130

function checkOrientation() {
  isLandscape.value = window.innerWidth > window.innerHeight
}

function resizeGame() {
  const wrap = gameWrapRef.value
  if (!wrap) return
  const card = wrap.querySelector('.game-card')
  if (!card) return
  const scale = window.innerWidth / GAME_W
  card.style.setProperty('--g-scale', scale)
}

function toggleFullscreen() {
  if (document.fullscreenElement) {
    document.exitFullscreen().catch(() => {})
  } else {
    document.documentElement.requestFullscreen().catch(() => {})
  }
}

onMounted(() => {
  window.addEventListener('resize', () => {
    checkOrientation()
    setTimeout(resizeGame, 100)
  })
  window.addEventListener('orientationchange', () => {
    setTimeout(() => { checkOrientation(); setTimeout(resizeGame, 200) }, 300)
  })
  document.addEventListener('fullscreenchange', resizeGame)
  document.addEventListener('webkitfullscreenchange', resizeGame)

  // 等 DashGame 挂载后，拦截它的 touch 事件
  function hookCard() {
    const card = gameWrapRef.value?.querySelector('.game-card')
    if (card) {
      // touchstart: 只出拳，不移动拳套
      card.addEventListener('touchstart', onTouchCapture, { capture: true, passive: false })
      // touchmove: 只移动拳套，不出拳
      card.addEventListener('touchmove', onTouchMoveCapture, { capture: true, passive: false })
      resizeGame()
    } else {
      setTimeout(hookCard, 200)
    }
  }
  if (isLandscape.value) {
    setTimeout(hookCard, 500)
  } else {
    // 监听横屏变化
    const iv = setInterval(() => {
      if (window.innerWidth > window.innerHeight) {
        clearInterval(iv)
        setTimeout(() => {
          const card = gameWrapRef.value?.querySelector('.game-card')
          if (card) {
            card.addEventListener('touchstart', onTouchCapture, { capture: true, passive: false })
            card.addEventListener('touchmove', onTouchMoveCapture, { capture: true, passive: false })
            resizeGame()
          }
        }, 500)
      }
    }, 300)
  }
})

function onTouchCapture(e) {
  // 放行 UI 元素（名字输入、角色选择），不触发击打
  if (e.target.closest('#geNameInput,.ge-char-arrow,.ge-name-arrow,.ge-char-picker,.ge-char-item')) return
  e.preventDefault()
  e.stopPropagation()
  const touch = e.touches[0]
  const side = touch.clientX < window.innerWidth / 2 ? 'left' : 'right'
  e.currentTarget.dispatchEvent(new MouseEvent('mousedown', { button: side === 'left' ? 0 : 2, bubbles: true }))
}

function onTouchMoveCapture(e) {
  // 放行 UI 元素
  if (e.target.closest('#geNameInput,.ge-char-arrow,.ge-name-arrow,.ge-char-picker,.ge-char-item')) return
  e.preventDefault()
  e.stopPropagation()
  const touch = e.touches[0]
  e.currentTarget.dispatchEvent(new MouseEvent('mousemove', { clientX: touch.clientX, bubbles: true }))
}

onUnmounted(() => {
  window.removeEventListener('resize', checkOrientation)
  window.removeEventListener('orientationchange', checkOrientation)
  document.removeEventListener('fullscreenchange', resizeGame)
  document.removeEventListener('webkitfullscreenchange', resizeGame)
  const card = gameWrapRef.value?.querySelector('.game-card')
  if (card) {
    card.removeEventListener('touchstart', onTouchCapture, { capture: true })
    card.removeEventListener('touchmove', onTouchMoveCapture, { capture: true })
  }
})
</script>

<style scoped>
.mg-view {
  position:fixed; inset:0; z-index:9999;
  background:#0a0a14;
  display:flex; align-items:center; justify-content:center;
}
.mg-view.landscape { background:#000; }

/* 旋转提示 */
.mg-rotate-hint {
  display:flex; flex-direction:column; align-items:center; gap:12px;
  padding:40px; text-align:center;
}
.mg-phone-icon { font-size:48px; animation:mg-rotate 2s ease-in-out infinite; }
@keyframes mg-rotate {
  0%,100% { transform:rotate(0deg); }
  50% { transform:rotate(90deg); }
}
.mg-rotate-text { font-size:18px; font-weight:700; color:#c0c0d0; }
.mg-rotate-sub { font-size:13px; color:#707088; }
.mg-back-btn {
  margin-top:12px; padding:8px 24px;
  background:rgba(255,255,255,0.08);
  border:1px solid rgba(255,255,255,0.12);
  border-radius:8px; color:#c0c0d0; font-size:13px;
  cursor:pointer;
}
.mg-fs-btn {
  padding:10px 28px;
  background:rgba(108,92,231,0.2);
  border:1px solid rgba(108,92,231,0.35);
  border-radius:8px; color:#b0a0f0; font-size:14px; font-weight:600;
  cursor:pointer; letter-spacing:0.5px;
}

/* 游戏区域 */
.mg-game-wrap {
  position:relative; width:100%; height:100%;
  display:flex; align-items:center; justify-content:center;
  background:#000;
}
.mg-game-wrap :deep(.game-card) {
  width:264px; height:130px;
  background:#000;
  border:1px solid #000;
  border-radius:0 !important;
  position:absolute; left:50%; top:50%;
  transform:translate(-50%,-50%) scale(var(--g-scale,1));
  transform-origin:center center;
}
/* 游戏人物通过 transform scale 等比例放大（见 JS 中 --g-scale） */
.mg-game-wrap :deep(#geBgLayer) { background-size:cover; background-position:center; }
.mg-game-wrap :deep(#geFx) { width:100%; height:100%; }

/* 顶部按钮组 */
.mg-top-btns {
  position:fixed; top:12px; right:12px; z-index:99;
  display:flex; gap:8px;
}
.mg-top-btn {
  width:36px; height:36px; border-radius:50%;
  background:rgba(0,0,0,0.4);
  border:1px solid rgba(255,255,255,0.1);
  color:rgba(255,255,255,0.5); font-size:14px;
  cursor:pointer; display:flex; align-items:center; justify-content:center;
}
</style>
