<template>
  <div class="tab-content">
    <p class="desc">配置 AI 模型的 API 接口信息，配置后可在 AI 对话中使用。</p>
    <div class="info-row">
      <label>API 地址</label>
      <input v-model="apiUrl" class="input" placeholder="例如：https://api.deepseek.com/v1" />
    </div>
    <div class="info-row">
      <label>API Key</label>
      <input v-model="apiKey" type="password" class="input" placeholder="输入 API Key" />
    </div>
    <div class="info-row">
      <label>模型</label>
      <input v-model="model" class="input" placeholder="例如：deepseek-chat" />
    </div>
    <div class="info-row">
      <label>状态</label>
      <label class="toggle">
        <input type="checkbox" v-model="enabled" />
        <span class="toggle-slider"></span>
        <span class="toggle-text">{{ enabled ? '已启用' : '已停用' }}</span>
      </label>
    </div>
    <p v-if="savedHint" class="saved-hint">✓ 已保存，刷新 AI 对话后生效</p>
    <button class="btn-primary" @click="save" :disabled="saving">{{ saving ? '保存中...' : '保存配置' }}</button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getSettings, updateSettings } from '@/api/settings'

const apiUrl = ref('')
const apiKey = ref('')
const model = ref('')
const enabled = ref(false)
const saving = ref(false)
const savedHint = ref(false)

onMounted(async () => {
  try {
    const res = await getSettings()
    const cfg = JSON.parse(res.data?.layout_config || '{}')
    apiUrl.value = cfg.ai_api_url || ''
    apiKey.value = cfg.ai_api_key || ''
    model.value = cfg.ai_model || ''
    enabled.value = !!cfg.ai_enabled
  } catch {}
})

async function save() {
  saving.value = true
  savedHint.value = false
  try {
    const res = await getSettings()
    const cfg = JSON.parse(res.data?.layout_config || '{}')
    cfg.ai_api_url = apiUrl.value
    cfg.ai_api_key = apiKey.value
    cfg.ai_model = model.value
    cfg.ai_enabled = enabled.value
    await updateSettings({ layout_config: JSON.stringify(cfg) })
    savedHint.value = true
    setTimeout(() => { savedHint.value = false }, 3000)
  } catch (e) {
    alert('保存失败: ' + (e.message || '未知错误'))
  }
  saving.value = false
}
</script>

<style scoped>
.tab-content { max-width: 560px; }
.desc { color: var(--text3); font-size: 13px; margin-bottom: 20px; }
.info-row { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.info-row label { width: 100px; font-size: 14px; color: var(--text2); flex-shrink: 0; }
.input {
  flex: 1; padding: 8px 12px; background: rgba(255,255,255,0.06);
  border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-size: 13px;
}
.input:focus { border-color: var(--primary); }
.toggle { display: flex; align-items: center; gap: 10px; cursor: pointer; }
.toggle input { display: none; }
.toggle-slider {
  width: 40px; height: 22px; background: rgba(255,255,255,0.15); border-radius: 11px;
  position: relative; transition: background 0.2s;
}
.toggle-slider::after {
  content: ''; position: absolute; top: 2px; left: 2px;
  width: 18px; height: 18px; background: white; border-radius: 50%; transition: transform 0.2s;
}
.toggle input:checked + .toggle-slider { background: var(--primary); }
.toggle input:checked + .toggle-slider::after { transform: translateX(18px); }
.toggle-text { font-size: 13px; color: var(--text2); }
.saved-hint { font-size: 12px; color: var(--success, #27ae60); margin-bottom: 8px; }
.btn-primary {
  padding: 8px 20px; background: var(--primary); border-radius: 8px; color: white;
  border: none; font-size: 14px; font-weight: 600; cursor: pointer;
}
.btn-primary:hover:not(:disabled) { opacity: 0.85; }
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }
</style>
