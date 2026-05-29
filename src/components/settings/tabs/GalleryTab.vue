<template>
  <div class="tab-content">
    <div class="toolbar">
      <div class="tabs">
        <button :class="{ active: filter === 'all' }" @click="filter = 'all'">全部</button>
        <button :class="{ active: filter === 'wallpaper' }" @click="filter = 'wallpaper'">壁纸</button>
        <button :class="{ active: filter === 'icon' }" @click="filter = 'icon'">图标</button>
      </div>
      <label class="upload-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        上传
        <input type="file" accept="image/*" multiple @change="uploadFiles" hidden />
      </label>
    </div>

    <div v-if="uploading" class="uploading">上传中...</div>

    <div class="gallery-grid">
      <div v-for="img in filteredList" :key="img.id" class="gallery-item">
        <img :src="getUrl(img)" :alt="img.original_name" />
        <div class="item-overlay">
          <span class="item-type">{{ img.image_type }}</span>
          <button class="del-btn" @click="remove(img)">✕</button>
        </div>
      </div>
      <div v-if="filteredList.length === 0" class="empty">
        <p>暂无图片，点击上传添加</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getGallery, uploadImage, deleteImage } from '@/api/gallery'

const filter = ref('all')
const images = ref([])
const uploading = ref(false)

const filteredList = computed(() => {
  if (filter.value === 'all') return images.value
  return images.value.filter(i => i.image_type === filter.value)
})

function getUrl(img) {
  return img.url || `/uploads/${img.filename}`
}

async function load() {
  try {
    const res = await getGallery()
    images.value = res.data || []
  } catch {}
}

const ICON_SIZE = 150

async function uploadFiles(e) {
  const files = e.target.files
  if (!files.length) return
  uploading.value = true
  try {
    for (const file of files) {
      // 根据当前选中的 tab 决定类型
      const type = filter.value === 'icon' ? 'icon' : 'wallpaper'
      // 图标类型：大图自动裁剪为正方形，小图保持原样
      const uploadFile = (type === 'icon') ? await maybeResizeIcon(file) : file
      const res = await uploadImage(uploadFile, type)
      images.value.unshift(res.data)
    }
  } catch (e) {
    alert('上传失败：' + e.message)
  } finally {
    uploading.value = false
    e.target.value = ''
  }
}

/** 如果图片任一边 > ICON_SIZE，则居中裁剪为 ICON_SIZE×ICON_SIZE 正方形；否则原样返回 */
function maybeResizeIcon(file) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      const { naturalWidth: w, naturalHeight: h } = img
      // 小于等于目标尺寸，不处理
      if (w <= ICON_SIZE && h <= ICON_SIZE) { resolve(file); return }
      // 居中裁剪成正方形
      const size = Math.min(w, h)
      const sx = (w - size) / 2
      const sy = (h - size) / 2
      const canvas = document.createElement('canvas')
      canvas.width = ICON_SIZE
      canvas.height = ICON_SIZE
      const ctx = canvas.getContext('2d')
      ctx.drawImage(img, sx, sy, size, size, 0, 0, ICON_SIZE, ICON_SIZE)
      canvas.toBlob((blob) => {
        if (!blob) { resolve(file); return }
        const resized = new File([blob], file.name, { type: 'image/png' })
        resolve(resized)
      }, 'image/png')
    }
    img.onerror = () => resolve(file)
    img.src = URL.createObjectURL(file)
  })
}

async function remove(img) {
  if (!confirm(`确定删除「${img.original_name || img.filename}」？`)) return
  try {
    await deleteImage(img.id)
    images.value = images.value.filter(i => i.id !== img.id)
  } catch (e) {
    alert('删除失败：' + e.message)
  }
}

onMounted(load)
</script>

<style scoped>
.tab-content { max-width: 100%; }
.toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.tabs { display: flex; gap: 4px; }
.tabs button {
  padding: 6px 14px; background: var(--bg-glass); border: 1px solid var(--border);
  border-radius: 6px; color: var(--text2); font-size: 13px; cursor: pointer;
}
.tabs button.active { background: var(--primary); color: white; border-color: var(--primary); }
.upload-btn {
  display: flex; align-items: center; gap: 6px; padding: 8px 16px;
  background: var(--primary); border-radius: 8px; color: white; font-size: 13px;
  cursor: pointer; font-weight: 600;
}
.upload-btn:hover { opacity: 0.85; }
.uploading { color: var(--text3); font-size: 13px; padding: 8px 0; }
.gallery-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 10px; }
.gallery-item {
  position: relative; border-radius: 8px; overflow: hidden; aspect-ratio: 1;
  border: 1px solid var(--border);
}
.gallery-item img { width: 100%; height: 100%; object-fit: cover; }
.item-overlay {
  position: absolute; bottom: 0; left: 0; right: 0;
  display: flex; justify-content: space-between; align-items: center;
  padding: 4px 6px; background: rgba(0,0,0,0.5); opacity: 0; transition: opacity 0.15s;
}
.gallery-item:hover .item-overlay { opacity: 1; }
.item-type { font-size: 10px; color: rgba(255,255,255,0.7); }
.del-btn {
  width: 20px; height: 20px; display: flex; align-items: center; justify-content: center;
  background: rgba(255,107,107,0.8); border: none; border-radius: 4px;
  color: white; font-size: 11px; cursor: pointer;
}
.empty { grid-column: 1 / -1; text-align: center; color: var(--text3); font-size: 13px; padding: 40px 0; }
</style>
