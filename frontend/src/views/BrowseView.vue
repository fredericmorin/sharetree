<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Breadcrumbs from '../components/Breadcrumbs.vue'
import EntryList from '../components/EntryList.vue'

const route = useRoute()
const router = useRouter()

const entries = ref([])
const loading = ref(false)
const error = ref(null)

const currentPath = computed(() => {
  const p = route.params.path
  if (!p) return ''
  return '/' + (Array.isArray(p) ? p.join('/') : p)
})

async function fetchEntries() {
  loading.value = true
  error.value = null
  try {
    const apiPath = currentPath.value
      ? `/api/v1/browse${currentPath.value}`
      : '/api/v1/browse'
    const res = await fetch(apiPath, { credentials: 'same-origin' })
    if (res.status === 403) {
      router.push({ path: '/access', query: { next: currentPath.value || '/' } })
      return
    }
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      error.value = body.detail ?? `HTTP ${res.status}`
      return
    }
    const data = await res.json()
    entries.value = data.entries
  } finally {
    loading.value = false
  }
}

watch(() => route.params.path, fetchEntries)
onMounted(fetchEntries)
</script>

<template>
  <div>
    <Breadcrumbs :path="currentPath" />
    <p v-if="loading" class="status">Loading…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>
    <EntryList v-else :entries="entries" />
  </div>
</template>

<style scoped>
.status {
  color: #6c757d;
  padding: 1rem 0;
}

.error {
  color: #dc3545;
}
</style>
