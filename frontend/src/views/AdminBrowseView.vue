<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDebounceFn } from '@vueuse/core'
import FileIcon from '@/components/FileIcon.vue'
import Input from '@/components/ui/input/index.vue'
import Button from '@/components/ui/button/index.vue'
import Badge from '@/components/ui/badge/index.vue'
import Skeleton from '@/components/ui/skeleton/index.vue'
import { Search, AlertCircle, RefreshCw, FolderOpen, House, FilePlus } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const entries = ref([])
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')

const currentPath = computed(() => {
  const p = route.params.path
  if (!p) return ''
  return '/' + (Array.isArray(p) ? p.join('/') : p)
})

const breadcrumbs = computed(() => {
  const parts = currentPath.value.split('/').filter(Boolean)
  return parts.map((part, i) => ({
    label: part,
    to: '/admin/browse/' + parts.slice(0, i + 1).join('/'),
  }))
})

async function checkAuth() {
  try {
    const res = await fetch('/api/v1/me', { credentials: 'same-origin' })
    if (!res.ok) {
      router.replace('/admin/login')
      return false
    }
    const data = await res.json()
    if (!data.data?.is_admin) {
      router.replace('/admin/login')
      return false
    }
    return true
  } catch {
    router.replace('/admin/login')
    return false
  }
}

async function fetchEntries() {
  loading.value = true
  error.value = null
  searchQuery.value = ''
  try {
    const apiPath = currentPath.value
      ? `/api/v1/admin/browse${currentPath.value}`
      : '/api/v1/admin/browse'
    const res = await fetch(apiPath, { credentials: 'same-origin' })
    if (res.status === 401 || res.status === 403) {
      router.replace('/admin/login')
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

const filteredEntries = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return entries.value
  return entries.value.filter((e) => e.name.toLowerCase().includes(q))
})

function formatSize(bytes) {
  if (bytes === null || bytes === undefined) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function navigateTo(entry) {
  router.push('/admin/browse' + entry.path)
}

function makePattern(entry) {
  return entry.type === 'directory' ? entry.path.replace(/\/$/, '') + '/**' : entry.path
}

function createAccessCode(entry) {
  router.push('/admin/access/create?pattern=' + encodeURIComponent(makePattern(entry)))
}

watch(() => route.params.path, fetchEntries)
onMounted(async () => {
  const ok = await checkAuth()
  if (ok) fetchEntries()
})
</script>

<template>
  <div>
    <!-- Breadcrumb header -->
    <div class="flex items-center gap-1.5 text-sm mb-6">
      <button
        class="text-muted-foreground hover:text-foreground transition-colors"
        @click="router.push('/admin/browse')"
      >
        <House class="h-4 w-4" />
      </button>
      <template v-for="(seg, i) in breadcrumbs" :key="seg.to">
        <span class="text-muted-foreground">/</span>
        <span
          v-if="i === breadcrumbs.length - 1"
          class="text-foreground font-medium"
        >{{ seg.label }}</span>
        <button
          v-else
          class="text-muted-foreground hover:text-foreground transition-colors"
          @click="router.push(seg.to)"
        >{{ seg.label }}</button>
      </template>
    </div>

    <!-- Loading skeletons -->
    <div v-if="loading" class="space-y-2">
      <Skeleton class="h-11 w-full rounded-md" />
      <Skeleton class="h-11 w-full rounded-md" />
      <Skeleton class="h-11 w-full rounded-md" />
      <Skeleton class="h-11 w-3/4 rounded-md" />
    </div>

    <!-- Error state -->
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
      <!-- Search -->
      <div v-if="entries.length > 50" class="relative mb-4">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <Input
          :model-value="searchQuery"
          @input="debouncedSearch($event.target.value)"
          type="search"
          placeholder="Filter files…"
          class="pl-9"
        />
      </div>

      <!-- Empty directory -->
      <div v-if="!entries.length" class="flex flex-col items-center gap-3 py-16 text-center">
        <FolderOpen class="h-10 w-10 text-muted-foreground/50" />
        <p class="text-sm text-muted-foreground">This directory is empty.</p>
      </div>

      <!-- No search results -->
      <div v-else-if="!filteredEntries.length" class="flex flex-col items-center gap-3 py-16 text-center">
        <FolderOpen class="h-10 w-10 text-muted-foreground/50" />
        <p class="text-sm text-muted-foreground">
          No matches for "<span class="font-medium text-foreground">{{ searchQuery }}</span>"
        </p>
      </div>

      <!-- Entry list -->
      <ul v-else class="rounded-lg border divide-y divide-border overflow-hidden">
        <li
          v-for="entry in filteredEntries"
          :key="entry.path"
          class="group flex items-center gap-3 px-4 py-2.5 bg-card hover:bg-accent/50 transition-colors"
        >
          <!-- Action column (left) -->
          <Button
            variant="outline"
            size="sm"
            class="shrink-0 gap-1.5 text-xs"
            @click.stop="createAccessCode(entry)"
          >
            <FilePlus class="h-3.5 w-3.5" />
            Create access code
          </Button>

          <!-- File icon -->
          <FileIcon :filename="entry.name" :is-directory="entry.type === 'directory'" />

          <!-- Name -->
          <template v-if="entry.type === 'directory'">
            <button
              class="flex-1 text-sm font-medium text-foreground min-w-0 truncate text-left hover:underline"
              @click="navigateTo(entry)"
            >
              {{ entry.name }}
            </button>
          </template>
          <template v-else>
            <span class="flex-1 text-sm text-foreground min-w-0 truncate">{{ entry.name }}</span>
            <Badge v-if="entry.size !== null && entry.size !== undefined" variant="secondary" class="shrink-0 font-mono text-xs">
              {{ formatSize(entry.size) }}
            </Badge>
          </template>
        </li>
      </ul>
    </template>
  </div>
</template>
