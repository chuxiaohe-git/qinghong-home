<template>
  <div class="tab-content">
    <p class="desc">账号之间的数据不互通。仅管理员可管理账号。</p>
    <div v-if="!userStore.isAdmin" class="no-perm">
      <p>您没有管理账号的权限</p>
    </div>
    <template v-else>
      <button class="btn-primary btn-sm" @click="showAdd = true">+ 添加账号</button>

      <div v-if="showAdd" class="add-form">
        <input v-model="newUser.username" class="input" placeholder="用户名" />
        <input v-model="newUser.password" type="password" class="input" placeholder="密码（至少6位）" />
        <input v-model="newUser.nickname" class="input" placeholder="昵称" />
        <div class="form-actions">
          <button class="btn-primary btn-sm" @click="addUser">确定</button>
          <button class="btn-cancel btn-sm" @click="showAdd = false">取消</button>
        </div>
      </div>

      <div class="result-bar" v-if="resultMsg" :class="{ success: resultOk, error: !resultOk }">
        {{ resultMsg }}
      </div>

      <table class="user-table">
        <thead>
          <tr>
            <th>账号</th>
            <th>昵称</th>
            <th>角色</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>
              <span v-if="editId !== u.id">{{ u.username }}</span>
              <input v-else v-model="editForm.username" class="input-inline" placeholder="用户名" />
            </td>
            <td>
              <span v-if="editId !== u.id">{{ u.nickname }}</span>
              <input v-else v-model="editForm.nickname" class="input-inline" placeholder="昵称" />
            </td>
            <td>{{ u.role === 'admin' ? '管理员' : '普通用户' }}</td>
            <td>
              <span :class="u.is_active ? 'active' : 'inactive'">
                {{ u.is_active ? '正常' : '已禁用' }}
              </span>
            </td>
            <td class="actions">
              <template v-if="editId === u.id">
                <button class="btn-text" @click="confirmEdit(u)">保存</button>
                <button class="btn-text btn-text-danger" @click="cancelEdit">取消</button>
              </template>
              <template v-else>
                <button class="btn-text" @click="startEdit(u)">编辑</button>
                <button class="btn-text" @click="toggleStatus(u)">
                  {{ u.is_active ? '禁用' : '启用' }}
                </button>
                <button class="btn-text" @click="resetPw(u)">重置密码</button>
                <button
                  v-if="u.id !== userStore.user?.id"
                  class="btn-text btn-text-danger"
                  @click="confirmDelete(u)"
                >删除</button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { getUsers, createUser, toggleUser, resetUserPassword, updateUser, deleteUser } from '@/api/users'

const userStore = useUserStore()
const users = ref([])
const showAdd = ref(false)
const newUser = ref({ username: '', password: '', nickname: '' })
const resultMsg = ref('')
const resultOk = ref(false)
const editId = ref(null)
const editForm = ref({ username: '', nickname: '' })

function showResult(ok, msg) {
  resultMsg.value = msg
  resultOk.value = ok
  setTimeout(() => { resultMsg.value = '' }, 3000)
}

async function loadUsers() {
  try {
    const res = await getUsers()
    users.value = res.data?.items || []
  } catch {}
}

onMounted(async () => {
  if (userStore.isAdmin) {
    await loadUsers()
  }
})

async function addUser() {
  try {
    await createUser(newUser.value)
    showAdd.value = false
    newUser.value = { username: '', password: '', nickname: '' }
    await loadUsers()
    showResult(true, '账号已添加')
  } catch (e) {
    showResult(false, e.message || '添加失败')
  }
}

async function resetPw(u) {
  const pw = prompt(`为 ${u.username} 设置新密码（至少6位）`)
  if (pw && pw.length >= 6) {
    try {
      await resetUserPassword(u.id, pw)
      showResult(true, `${u.username} 密码已重置`)
    } catch (e) {
      showResult(false, e.message || '重置失败')
    }
  }
}

function startEdit(u) {
  editId.value = u.id
  editForm.value = { username: u.username, nickname: u.nickname }
}

function cancelEdit() {
  editId.value = null
  editForm.value = { username: '', nickname: '' }
}

async function confirmEdit(u) {
  try {
    await updateUser(u.id, { username: editForm.value.username, nickname: editForm.value.nickname })
    editId.value = null
    await loadUsers()
    showResult(true, '用户信息已更新')
  } catch (e) {
    showResult(false, e.message || '更新失败')
  }
}

async function toggleStatus(u) {
  const action = u.is_active ? '禁用' : '启用'
  if (!confirm(`确定${action}账号 ${u.username} 吗？`)) return
  try {
    await toggleUser(u.id)
    await loadUsers()
    showResult(true, `${u.username} 已${action}`)
  } catch (e) {
    showResult(false, e.message || '操作失败')
  }
}

async function confirmDelete(u) {
  if (!confirm(`确定要删除账号 ${u.username} 吗？\n该用户的所有数据（分组、书签、待办等）将被永久删除，不可恢复！`)) return
  if (!confirm(`再次确认：删除 ${u.username}？此操作不可撤销！`)) return
  try {
    await deleteUser(u.id)
    await loadUsers()
    showResult(true, `${u.username} 已删除`)
  } catch (e) {
    showResult(false, e.message || '删除失败')
  }
}
</script>

<style scoped>
.tab-content { max-width: 100%; }
.desc { color: var(--text3); font-size: 13px; margin-bottom: 16px; }
.no-perm { color: var(--text3); padding: 40px 0; text-align: center; }
.btn-sm { padding: 6px 14px; font-size: 13px; margin-bottom: 16px; }
.btn-primary { background: var(--primary); border-radius: 8px; color: white; font-weight: 600; }
.btn-primary:hover { opacity: 0.85; }
.btn-cancel { background: transparent; border: 1px solid var(--border); border-radius: 8px; color: var(--text2); }
.add-form { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; max-width: 320px; }
.form-actions { display: flex; gap: 8px; }
.input {
  padding: 8px 12px; background: rgba(255,255,255,0.06);
  border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-size: 13px;
}
.input-inline {
  padding: 4px 8px; background: rgba(255,255,255,0.06);
  border: 1px solid var(--primary); border-radius: 6px; color: var(--text); font-size: 13px; width: 120px;
}
.result-bar {
  padding: 6px 12px; border-radius: 8px; font-size: 13px; margin-bottom: 12px; display: inline-block;
}
.result-bar.success { background: color-mix(in srgb, #00CEC9 20%, transparent); color: #00CEC9; }
.result-bar.error { background: color-mix(in srgb, #FF6B6B 20%, transparent); color: #FF6B6B; }
.user-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.user-table th, .user-table td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); }
.user-table th { color: var(--text3); font-weight: 600; }
.active { color: var(--accent); }
.inactive { color: var(--danger); }
.actions { display: flex; gap: 6px; flex-wrap: wrap; }
.btn-text { background: none; border: none; color: var(--primary); font-size: 12px; padding: 4px 8px; border-radius: 6px; cursor: pointer; }
.btn-text:hover { background: var(--primary-light); }
.btn-text-danger { color: var(--danger); }
.btn-text-danger:hover { background: color-mix(in srgb, var(--danger) 15%, transparent); }
</style>
