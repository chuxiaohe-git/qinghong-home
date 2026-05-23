import { defineStore } from 'pinia'
import { getGroups, createGroup as apiCreate, updateGroup as apiUpdate, deleteGroup as apiDelete, sortGroups as apiSort } from '@/api/groups'

export const useGroupStore = defineStore('groups', {
  state: () => ({
    groups: [],
    activeGroupId: null,
  }),
  getters: {
    activeGroup: (state) => state.groups.find(g => g.id === state.activeGroupId) || state.groups[0] || null,
  },
  actions: {
    async fetchGroups() {
      const res = await getGroups()
      this.groups = res.data || []
      if (!this.activeGroupId && this.groups.length > 0) {
        this.activeGroupId = this.groups[0].id
      }
    },
    async createGroup(name) {
      const res = await apiCreate(name)
      this.groups.push(res.data)
      return res.data
    },
    async updateGroup(id, data) {
      const res = await apiUpdate(id, data)
      const idx = this.groups.findIndex(g => g.id === id)
      if (idx >= 0) this.groups[idx] = res.data
    },
    async deleteGroup(id) {
      await apiDelete(id)
      this.groups = this.groups.filter(g => g.id !== id)
      if (this.activeGroupId === id) {
        this.activeGroupId = this.groups[0]?.id || null
      }
    },
    setActiveGroup(id) {
      this.activeGroupId = id
    },
    async sortGroups(order) {
      await apiSort(order)
      await this.fetchGroups()
    },
  },
})
