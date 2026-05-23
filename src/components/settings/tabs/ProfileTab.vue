<template>
  <div class="tab-content">
    <!-- 头像 -->
    <div class="avatar-section">
      <div class="avatar-preview" @click="avatarInput.click()" title="点击更换头像">
        <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" />
        <span v-else class="avatar-text">{{ (userStore.user?.nickname || userStore.user?.username || '?').charAt(0) }}</span>
        <div class="avatar-overlay">更换</div>
      </div>
      <input ref="avatarInput" type="file" accept="image/png,image/jpeg,image/gif,image/webp" hidden @change="onAvatarChange" />
      <div v-if="uploading" class="avatar-uploading">上传中...</div>
    </div>

    <div class="info-row">
      <label>账号</label>
      <span class="value readonly">{{ userStore.user?.username }}</span>
    </div>
    <div class="info-row">
      <label>昵称</label>
      <input v-model="nickname" class="input" placeholder="请输入昵称" />
    </div>
    <div class="info-row">
      <label>角色</label>
      <span class="value readonly">{{ userStore.user?.role === 'admin' ? '超级管理员' : '普通用户' }}</span>
    </div>
    <button class="btn-primary" @click="saveProfile">保存</button>

    <div class="section-divider"></div>
    <h3 class="section-title">修改密码</h3>
    <div class="info-row">
      <label>旧密码</label>
      <input v-model="oldPw" type="password" class="input" placeholder="输入旧密码" />
    </div>
    <div class="info-row">
      <label>新密码</label>
      <input v-model="newPw" type="password" class="input" placeholder="输入新密码（至少6位）" />
    </div>
    <div class="info-row">
      <label>确认新密码</label>
      <input v-model="confirmPw" type="password" class="input" placeholder="再次输入新密码" />
    </div>
    <button class="btn-primary" @click="changePw">修改密码</button>
    <p v-if="msg" class="msg" :class="{ err: msgIsErr }">{{ msg }}</p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { changePassword, uploadAvatar } from '@/api/auth'

const userStore = useUserStore()
const nickname = ref(userStore.user?.nickname || '')
const oldPw = ref('')
const newPw = ref('')
const confirmPw = ref('')
const msg = ref('')
const msgIsErr = ref(false)
const avatarInput = ref(null)
const uploading = ref(false)
const localAvatar = ref('')

const avatarUrl = computed(() => {
  const a = localAvatar.value || userStore.user?.avatar
  return a ? `/uploads/${a}` : null
})

async function onAvatarChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const res = await uploadAvatar(file)
    const d = res.data || res
    const filename = d.avatar || d.url?.replace('/uploads/', '') || ''
    localAvatar.value = filename
    userStore.updateUser({ avatar: filename })
    msg.value = '头像更新成功'
    msgIsErr.value = false
  } catch (e) {
    msg.value = '上传失败：' + (e.message || e)
    msgIsErr.value = true
  } finally {
    uploading.value = false
    e.target.value = ''
  }
}

async function saveProfile() {
  // TODO: implement via settings API
  msg.value = '保存成功'
  msgIsErr.value = false
  userStore.updateUser({ nickname: nickname.value })
}

async function changePw() {
  if (newPw.value.length < 6) {
    msg.value = '新密码至少6位'
    msgIsErr.value = true
    return
  }
  if (newPw.value !== confirmPw.value) {
    msg.value = '两次密码不一致'
    msgIsErr.value = true
    return
  }
  try {
    await changePassword(oldPw.value, newPw.value)
    msg.value = '密码修改成功'
    msgIsErr.value = false
    oldPw.value = ''
    newPw.value = ''
    confirmPw.value = ''
  } catch (e) {
    msg.value = e.message
    msgIsErr.value = true
  }
}
</script>

<style scoped>
.tab-content { max-width: 480px; }
.info-row { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.info-row label { width: 80px; font-size: 14px; color: var(--text2); flex-shrink: 0; }
.value { font-size: 14px; }
.value.readonly { color: var(--text3); }
.input {
  flex: 1; padding: 8px 12px; background: rgba(255,255,255,0.06);
  border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-size: 13px;
}
.input:focus { border-color: var(--primary); }
.btn-primary {
  padding: 8px 20px; background: var(--primary); border-radius: 8px; color: white;
  font-size: 14px; font-weight: 600; transition: opacity 0.2s;
}
.btn-primary:hover { opacity: 0.85; }
.section-divider { border: none; border-top: 1px solid var(--border); margin: 24px 0; }
.section-title { font-size: 15px; font-weight: 700; margin-bottom: 16px; }
.msg { margin-top: 12px; font-size: 13px; color: var(--accent); }
.msg.err { color: var(--danger); }

.avatar-section { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.avatar-preview {
  width: 60px; height: 60px; border-radius: 50%; position: relative;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; overflow: hidden; flex-shrink: 0;
}
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-text { color: white; font-size: 22px; font-weight: 700; }
.avatar-overlay {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,0.5); color: white; font-size: 12px; opacity: 0; transition: opacity 0.2s;
}
.avatar-preview:hover .avatar-overlay { opacity: 1; }
.avatar-uploading { font-size: 13px; color: var(--text3); }
</style>
