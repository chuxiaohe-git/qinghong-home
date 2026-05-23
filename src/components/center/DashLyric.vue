<template>
  <div class="lyric-bar" @click.stop="toggleExpand">
    <audio ref="audioEl" style="display:none" @timeupdate="onTime"></audio>
    <div class="lyric-main">
      <span class="lyric-icon" :class="{ playing }">♫</span>
      <div class="lyric-text" v-if="currentSong">
        <span class="lyric-playing">{{ currentSong.title }}</span>
        <span class="lyric-sep"> / </span>
        <span class="lyric-author">{{ currentSong.author || currentSong.artists }}</span>
      </div>
      <div class="lyric-text" v-else>
        <span class="lyric-placeholder">♪ 选择歌曲开始播放</span>
      </div>
    </div>

    <!-- 歌词滚动条 -->
    <Transition name="slide-down">
      <div class="lyric-scroll" v-if="expanded && lyrics.length">
        <div class="lyric-lines" :style="{ transform: `translateY(${-scrollTop}px)` }">
          <div
            v-for="(l, idx) in lyrics"
            :key="idx"
            class="lyric-line"
            :class="{ active: idx === lyricIdx }"
          >{{ l.text }}</div>
        </div>
      </div>
    </Transition>

    <!-- Mini 歌词（不展开时单行滚动） -->
    <div class="lyric-mini" v-if="!expanded && currentLyric">
      <span class="lyric-mini-text">{{ currentLyric }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import {
  audioEl, playing, currentSong, lyrics, currentTime
} from '@/composables/useMusicPlayer'

const expanded = ref(false)
const scrollTop = ref(0)
const localAudio = ref(null)

// 当前歌词索引
const lyricIdx = computed(() => {
  const t = currentTime.value
  for (let i = lyrics.value.length - 1; i >= 0; i--) {
    if (t >= lyrics.value[i].time) return i
  }
  return -1
})

const currentLyric = computed(() => {
  if (lyricIdx.value >= 0) return lyrics.value[lyricIdx.value]?.text
  return null
})

watch(lyricIdx, (idx) => {
  if (idx >= 0 && expanded.value) {
    // 让当前行大致居中
    const lineH = 24
    scrollTop.value = Math.max(0, idx * lineH - 36)
  }
})

function onTime() {}

function toggleExpand() {
  expanded.value = !expanded.value
}

onMounted(() => {
  // 绑定 audio element
  const audio = document.querySelector('.music-card audio')
  if (audio) audioEl.value = audio
})
</script>

<style scoped>
.lyric-bar {
  height: 30px;
  border-bottom: 1px solid var(--border);
  background: color-mix(in srgb, var(--bg-card) 50%, transparent);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  cursor: pointer;
  overflow: hidden;
  position: relative;
  flex-shrink: 0;
}

.lyric-main {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 10px;
  height: 30px;
  overflow: hidden;
}

.lyric-icon {
  font-size: 13px;
  color: #FF6B6B;
  flex-shrink: 0;
}
.lyric-icon.playing {
  animation: pulse-note 1s infinite;
}
@keyframes pulse-note { 0%,100% { opacity: 1 } 50% { opacity: 0.3 } }

.lyric-text {
  display: flex;
  align-items: center;
  overflow: hidden;
  flex: 1;
}
.lyric-playing {
  font-size: 11px;
  color: var(--text);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.lyric-sep { font-size: 10px; color: var(--text3); }
.lyric-author {
  font-size: 10px;
  color: var(--text3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.lyric-placeholder { font-size: 10px; color: var(--text3); }

/* Mini 单行歌词 */
.lyric-mini {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  padding-left: 30px;
  overflow: hidden;
  pointer-events: none;
}
.lyric-mini-text {
  font-size: 11px;
  color: var(--text2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}

/* 展开歌词 */
.lyric-scroll {
  position: absolute;
  left: 0;
  right: 0;
  top: 30px;
  height: 80px;
  background: color-mix(in srgb, var(--bg-card) 90%, transparent);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  overflow: hidden;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

.lyric-lines {
  padding: 8px 12px;
  transition: transform 0.3s ease;
}

.lyric-line {
  font-size: 11px;
  color: var(--text3);
  line-height: 24px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.2s, font-size 0.2s;
}

.lyric-line.active {
  color: #FF6B6B;
  font-size: 12px;
  font-weight: 600;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: height 0.2s ease, opacity 0.2s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  height: 0;
  opacity: 0;
}
</style>
