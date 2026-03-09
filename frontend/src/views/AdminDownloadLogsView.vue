<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import Button from '@/components/ui/button/index.vue'
import Badge from '@/components/ui/badge/index.vue'
import Skeleton from '@/components/ui/skeleton/index.vue'
import Breadcrumb from '@/components/ui/breadcrumb/index.vue'
import BreadcrumbList from '@/components/ui/breadcrumb/BreadcrumbList.vue'
import BreadcrumbItem from '@/components/ui/breadcrumb/BreadcrumbItem.vue'
import BreadcrumbLink from '@/components/ui/breadcrumb/BreadcrumbLink.vue'
import BreadcrumbPage from '@/components/ui/breadcrumb/BreadcrumbPage.vue'
import BreadcrumbSeparator from '@/components/ui/breadcrumb/BreadcrumbSeparator.vue'
import { ChevronLeft, ChevronRight, Download } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()

const entries = ref([])
const page = ref(1)
const totalEntries = ref(0)
const totalPages = ref(1)
const loading = ref(false)
const error = ref(null)

async function checkAuth() {
  try {
    const res = await fetch('/api/v1/me', { credentials: 'same-origin' })
    if (!res.ok) { router.replace('/admin/login'); return false }
    const data = await res.json()
    if (!data.data?.is_admin) { router.replace('/admin/login'); return false }
    return true
  } catch {
    router.replace('/admin/login')
    return false
  }
}

async function loadPage(p) {
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`/api/v1/admin/logs/downloads?page=${p}`, { credentials: 'same-origin' })
    if (res.status === 403) { router.replace('/admin/login'); return }
    if (!res.ok) { error.value = 'Failed to load download logs.'; return }
    const json = await res.json()
    const data = json.data
    entries.value = data.entries
    page.value = data.page
    totalEntries.value = data.total_entries
    totalPages.value = data.total_pages
  } catch {
    error.value = 'Network error. Please try again.'
  } finally {
    loading.value = false
  }
}

function goToPage(p) {
  router.push({ query: { page: p } })
}

function formatTimestamp(ts) {
  if (!ts) return '—'
  try {
    return new Date(ts).toLocaleString(undefined, {
      year: 'numeric', month: 'short', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    })
  } catch {
    return ts
  }
}

watch(
  () => route.query.page,
  (val) => loadPage(parseInt(val) || 1),
)

onMounted(async () => {
  const ok = await checkAuth()
  if (ok) loadPage(parseInt(route.query.page) || 1)
})
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 py-8">
    <div class="mb-6">
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink as-child>
              <RouterLink to="/admin" class="text-muted-foreground hover:text-foreground transition-colors no-underline">Admin</RouterLink>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>Download logs</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    </div>

    <div class="mb-6 flex items-center gap-2">
      <Download class="h-5 w-5 text-muted-foreground" />
      <h1 class="text-2xl font-semibold">Download logs</h1>
      <Badge v-if="!loading" variant="secondary" class="ml-auto">
        {{ totalEntries }} event{{ totalEntries !== 1 ? 's' : '' }}
      </Badge>
    </div>

    <!-- Loading skeletons -->
    <div v-if="loading" class="flex flex-col gap-4">
      <Skeleton class="h-10 w-full rounded-lg" v-for="i in 8" :key="i" />
    </div>

    <!-- Error state -->
    <p v-else-if="error" class="text-sm text-destructive">{{ error }}</p>

    <!-- Empty state -->
    <p v-else-if="entries.length === 0" class="text-sm text-muted-foreground">
      No download events recorded yet.
    </p>

    <!-- Log table -->
    <div v-else class="overflow-x-auto rounded-md border">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b bg-muted/50 text-left text-xs text-muted-foreground">
            <th class="px-3 py-2 font-medium">Timestamp</th>
            <th class="px-3 py-2 font-medium">Event</th>
            <th class="px-3 py-2 font-medium">Path</th>
            <th class="px-3 py-2 font-medium">Session</th>
            <th class="px-3 py-2 font-medium">Nicks</th>
            <th class="px-3 py-2 font-medium">Client IP</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(entry, i) in entries"
            :key="i"
            class="border-b last:border-0 hover:bg-muted/30"
          >
            <td class="px-3 py-1.5 font-mono text-xs text-muted-foreground whitespace-nowrap">
              {{ formatTimestamp(entry.timestamp) }}
            </td>
            <td class="px-3 py-1.5 text-xs">
              <Badge
                :variant="entry.event === 'download' ? 'default' : 'secondary'"
                class="text-xs"
              >
                {{ entry.event === 'download' ? 'direct' : 'caddy' }}
              </Badge>
            </td>
            <td class="px-3 py-1.5 font-mono text-xs max-w-xs truncate" :title="entry.path">
              {{ entry.path }}
            </td>
            <td class="px-3 py-1.5 font-mono text-xs text-muted-foreground">
              {{ entry.session_id ?? '—' }}
            </td>
            <td class="px-3 py-1.5 text-xs">
              <span v-if="entry.nicks.length === 0" class="text-muted-foreground">—</span>
              <div v-else class="flex flex-wrap gap-1">
                <code
                  v-for="nick in entry.nicks"
                  :key="nick"
                  class="rounded bg-muted px-1 py-0.5 text-xs font-mono"
                >{{ nick }}</code>
              </div>
            </td>
            <td class="px-3 py-1.5 font-mono text-xs text-muted-foreground">
              {{ entry.client_ip ?? '—' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination controls -->
    <div v-if="totalPages > 1" class="mt-6 flex items-center justify-between">
      <Button
        variant="outline"
        size="sm"
        :disabled="page <= 1 || loading"
        @click="goToPage(page - 1)"
      >
        <ChevronLeft class="mr-1 h-4 w-4" />
        Previous
      </Button>

      <span class="text-sm text-muted-foreground">Page {{ page }} of {{ totalPages }}</span>

      <Button
        variant="outline"
        size="sm"
        :disabled="page >= totalPages || loading"
        @click="goToPage(page + 1)"
      >
        Next
        <ChevronRight class="ml-1 h-4 w-4" />
      </Button>
    </div>
  </div>
</template>
