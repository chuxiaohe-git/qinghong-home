<template>
  <div class="tab-content">
    <div class="toolbar">
      <button class="btn-primary btn-sm" @click="showAdd = true">+ 添加分组</button>
    </div>

    <div v-if="showAdd" class="add-row">
      <input v-model="newName" class="input" placeholder="分组名称" @keydown.enter="addGroup" />
      <button class="btn-primary btn-sm" @click="addGroup">确定</button>
      <button class="btn-cancel btn-sm" @click="showAdd = false">取消</button>
    </div>

    <div class="group-list">
      <div v-for="g in groupStore.groups" :key="g.id"
        class="group-item"
        draggable="true"
        :data-group-id="g.id"
        @dragstart="onGStart($event, g.id)"
        @dragover.prevent="onGOver($event, g.id)"
        @dragend="onGEnd"
      >
        <div class="group-drag">⠿</div>
        <input v-if="editingId === g.id" ref="editInputRef" class="group-name group-edit-input"
          v-model="editName" maxlength="20"
          @keydown.enter="saveEdit(g)" @keydown.esc="cancelEdit" @blur="saveEdit(g)"
        />
        <span v-else class="group-name">{{ g.name }}</span>
        <div class="group-actions">
          <button v-if="editingId !== g.id" class="btn-icon" title="编辑" @click="startEdit(g)">✏️</button>
          <button v-else class="btn-icon" title="保存" @click="saveEdit(g)">💾</button>
          <button class="btn-icon" title="删除" @click="removeGroup(g.id)">🗑️</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useGroupStore } from '@/stores/groups'
import { sortGroups } from '@/api/groups'

const groupStore = useGroupStore()
const showAdd = ref(false)
const newName = ref('')

// ── 行内编辑 ──
const editingId = ref(null)
const editName = ref('')
const editInputRef = ref(null)

function startEdit(g) {
  editingId.value = g.id
  editName.value = g.name
  nextTick(() => editInputRef.value?.focus())
}
function cancelEdit() { editingId.value = null; editName.value = '' }
function saveEdit(g) {
  if (editName.value.trim() && editName.value.trim() !== g.name) {
    groupStore.updateGroup(g.id, { name: editName.value.trim() })
  }
  cancelEdit()
}

async function addGroup() {
  if (!newName.value.trim()) return
  await groupStore.createGroup(newName.value.trim())
  newName.value = ''
  showAdd.value = false
}

function removeGroup(id) {
  if (confirm('确定删除此分组？其下的收藏也会被删除。')) {
    groupStore.deleteGroup(id)
  }
}

// 拖拽排序
let dragGid = null
function onGStart(e, id) { dragGid = id; e.target.classList.add('dragging') }
function onGOver(e, id) {
  if (!dragGid || dragGid === id) return
  const list = groupStore.groups
  const from = list.findIndex(g => g.id === dragGid)
  const to = list.findIndex(g => g.id === id)
  if (from === -1 || to === -1) return
  const [item] = list.splice(from, 1)
  list.splice(to, 0, item)
  sortGroups(list.map(g => g.id))
  e.target.classList.remove('drag-over')
}
function onGEnd(e) { e.target.classList.remove('dragging'); dragGid = null }
</script>

<style scoped>
.tab-content { max-width: 600px; }
.toolbar { margin-bottom: 16px; }
.btn-sm { padding: 6px 14px; font-size: 13px; }
.btn-primary { background: var(--primary); border-radius: 8px; color: white; font-weight: 600; }
.btn-primary:hover { opacity: 0.85; }
.btn-cancel { background: transparent; border: 1px solid var(--border); border-radius: 8px; color: var(--text2); }
.btn-cancel:hover { background: var(--bg-glass); }
.add-row { display: flex; gap: 8px; margin-bottom: 16px; }
.input {
  flex: 1; padding: 8px 12px; background: rgba(255,255,255,0.06);
  border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-size: 13px;
}
.input:focus { border-color: var(--primary); }
.group-list { display: flex; flex-direction: column; gap: 6px; }
.group-item {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; background: var(--bg-glass); border-radius: 8px;
  cursor: default; transition: transform 0.12s, opacity 0.12s;
}
.group-item.dragging { opacity: 0.4; transform: scale(0.95); }
.group-drag { font-size: 12px; color: var(--text3); opacity: 0; cursor: grab; }
.group-item:hover .group-drag { opacity: 0.5; }
.group-name { font-size: 14px; }
.group-edit-input {
  flex: 1; padding: 4px 8px; font-size: 14px; font-family: inherit;
  background: rgba(255,255,255,0.1); border: 1px solid var(--primary);
  border-radius: 4px; color: var(--text); outline: none;
}
.group-actions { display: flex; gap: 4px; }
.btn-icon { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 6px; background: transparent; }
.btn-icon:hover { background: rgba(255,255,255,0.08); }
</style>
