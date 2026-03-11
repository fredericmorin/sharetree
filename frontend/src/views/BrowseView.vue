<script setup>
import { ref, computed, watch, onMounted, useTemplateRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDebounceFn, useEventListener } from '@vueuse/core'
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import EntryList from '@/components/EntryList.vue'
import Input from '@/components/ui/input/index.vue'
import Button from '@/components/ui/button/index.vue'
import Skeleton from '@/components/ui/skeleton/index.vue'
import Badge from '@/components/ui/badge/index.vue'
import Separator from '@/components/ui/separator/index.vue'
import { Search, AlertCircle, RefreshCw, KeyRound, ShieldCheck } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const entries = ref([])
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')
const searchInput = useTemplateRef('searchInputRef')

const activeCodes = ref([])
const isAdmin = ref(false)
const newCode = ref('')
const codeError = ref(null)
const submitting = ref(false)

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

async function fetchActiveCodes() {
  try {
    const res = await fetch('/api/v1/me', { credentials: 'same-origin' })
    if (!res.ok) return
    const data = await res.json()
    activeCodes.value = data.data?.active_code_details ?? []
    isAdmin.value = data.data?.is_admin ?? false
  } catch {
    // silently ignore
  }
}

async function activateCode() {
  codeError.value = null
  submitting.value = true
  try {
    const res = await fetch(`/api/v1/access_code/${encodeURIComponent(newCode.value.trim())}/activate`, {
      method: 'POST',
      credentials: 'same-origin',
    })
    if (res.status === 404) {
      codeError.value = 'Invalid access code.'
      return
    }
    if (!res.ok) {
      codeError.value = 'Activation failed. Please try again.'
      return
    }
    newCode.value = ''
    await fetchActiveCodes()
    await fetchEntries()
  } finally {
    submitting.value = false
  }
}

watch(() => route.params.path, fetchEntries)
onMounted(() => {
  fetchEntries()
  fetchActiveCodes()
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <Breadcrumbs :path="currentPath" />
      <Button v-if="isAdmin" variant="outline" size="sm" @click="router.push('/admin')">
        <ShieldCheck class="h-4 w-4 mr-2" />
        Admin
      </Button>
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
      <div v-if="entries.length > 50" class="relative mb-4">
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

    <Separator class="my-8" />

    <div class="space-y-6">
      <div v-if="activeCodes.length">
        <p class="text-sm font-medium text-muted-foreground mb-3">Active access codes</p>
        <ul class="flex flex-col gap-2">
          <li
            v-for="detail in activeCodes"
            :key="detail.code"
            class="flex items-center justify-between gap-2 rounded-md border bg-muted/40 px-3 py-2"
          >
            <div class="flex items-center gap-2 min-w-0">
              <p class="text-sm font-medium text-muted-foreground">{{ detail.nick }} ({{ detail.code }})</p>
              <Badge v-for="pattern in detail.patterns" :key="pattern" variant="secondary" class="shrink-0">{{ pattern }}</Badge>
            </div>
          </li>
        </ul>
      </div>

      <div>
        <div class="flex items-center gap-2 mb-3">
          <KeyRound class="h-4 w-4 text-muted-foreground" />
          <p class="text-sm font-medium text-muted-foreground">Activate additional access code</p>
        </div>
        <form @submit.prevent="activateCode" class="flex gap-2">
          <Input
            v-model="newCode"
            type="text"
            placeholder="Access code"
            autocomplete="off"
            :disabled="submitting"
            class="flex-1"
          />
          <Button type="submit" :disabled="submitting || !newCode.trim()">
            {{ submitting ? 'Activating…' : 'Activate' }}
          </Button>
        </form>
        <p v-if="codeError" class="mt-2 text-sm text-destructive">{{ codeError }}</p>
      </div>
    </div>
  </div>
</template>
