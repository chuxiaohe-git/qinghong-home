<template>
  <div class="search-bar">
    <div class="search-input-wrapper">
      <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
      <input
        v-model="query"
        type="text"
        placeholder="搜索书签..."
        @input="onSearch"
        @keydown.enter="onSearch"
      />
      <button v-if="query" class="clear-btn" @click="doClear" title="清除">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const query = ref('')
const emit = defineEmits(['search'])

let timer = null
function onSearch() {
  clearTimeout(timer)
  timer = setTimeout(() => {
    emit('search', query.value)
  }, 300)
}
function doClear() {
  query.value = ''
  emit('search', '')
}
</script>

<style scoped>
.search-bar {
  flex: 1;
  max-width: 400px;
  min-width: 200px;
}
.search-input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 50px;
  transition: border-color 0.2s;
  width: 100%;
}
.search-input-wrapper:focus-within {
  border-color: var(--primary);
}
.search-icon {
  color: var(--text3);
  flex-shrink: 0;
}
.search-input-wrapper input {
  flex: 1;
  background: none;
  border: none;
  color: var(--text);
  font-size: 14px;
}
.search-input-wrapper input::placeholder {
  color: var(--text3);
}
.clear-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 50%;
  color: var(--text3);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s;
}
.clear-btn:hover {
  background: rgba(255, 80, 80, 0.15);
  border-color: rgba(255, 80, 80, 0.4);
  color: #ff5050;
}
</style>
