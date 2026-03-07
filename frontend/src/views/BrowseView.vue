<script setup>
import { ref, computed, watch, onMounted, useTemplateRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDebounceFn, useEventListener } from '@vueuse/core'
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import EntryList from '@/components/EntryList.vue'
import Input from '@/components/ui/input/index.vue'
import Button from '@/components/ui/button/index.vue'
import Skeleton from '@/components/ui/skeleton/index.vue'
import { Search, AlertCircle, RefreshCw } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const entries = ref([])
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')
const searchInput = useTemplateRef('searchInputRef')

const currentPath = computed(() => {
  const p = route.params.path
  if (!p) return ''
  return '/' + (Array.isArray(p) ? p.join('/') : p)
})

async function fetchEntries() {
  loading.value = true
  error.value = null
  searchQuery.value = ''
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

const debouncedSearch = useDebounceFn((val) => {
  searchQuery.value = val
}, 150)

useEventListener(document, 'keydown', (e) => {
  if (e.key === '/' && document.activeElement?.tagName !== 'INPUT') {
    e.preventDefault()
    searchInput.value?.focus()
  }
})

watch(() => route.params.path, fetchEntries)
onMounted(fetchEntries)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <Breadcrumbs :path="currentPath" />
    </div>

    <div v-if="loading" class="space-y-2">
      <Skeleton class="h-11 w-full rounded-md" />
      <Skeleton class="h-11 w-full rounded-md" />
      <Skeleton class="h-11 w-full rounded-md" />
      <Skeleton class="h-11 w-3/4 rounded-md" />
    </div>

    <div v-else-if="error" class="flex flex-col items-center gap-4 py-12 text-center">
      <AlertCircle class="h-10 w-10 text-destructive" />
      <div>
        <p class="font-medium text-foreground">Failed to load directory</p>
        <p class="text-sm text-muted-foreground mt-1">{{ error }}</p>
      </div>
      <Button variant="outline" size="sm" @click="fetchEntries">
        <RefreshCw class="h-4 w-4 mr-2" />
        Retry
      </Button>
    </div>

    <template v-else>
      <div v-if="entries.length > 0" class="relative mb-4">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <Input
          ref="searchInputRef"
          :model-value="searchQuery"
          @input="debouncedSearch($event.target.value)"
          type="search"
          placeholder="Filter files… ( / )"
          class="pl-9"
        />
      </div>
      <EntryList :entries="entries" :search-query="searchQuery" />
    </template>
  </div>
</template>
