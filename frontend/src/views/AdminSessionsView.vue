<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Button from '@/components/ui/button/index.vue'
import Badge from '@/components/ui/badge/index.vue'
import Skeleton from '@/components/ui/skeleton/index.vue'
import Breadcrumb from '@/components/ui/breadcrumb/index.vue'
import BreadcrumbList from '@/components/ui/breadcrumb/BreadcrumbList.vue'
import BreadcrumbItem from '@/components/ui/breadcrumb/BreadcrumbItem.vue'
import BreadcrumbLink from '@/components/ui/breadcrumb/BreadcrumbLink.vue'
import BreadcrumbPage from '@/components/ui/breadcrumb/BreadcrumbPage.vue'
import BreadcrumbSeparator from '@/components/ui/breadcrumb/BreadcrumbSeparator.vue'
import { RouterLink } from 'vue-router'
import { ChevronLeft, ChevronRight, ShieldCheck } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()

const sessions = ref([])
const page = ref(1)
const totalSessions = ref(0)
const totalPages = ref(1)
const loading = ref(false)
const error = ref(null)

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

async function loadPage(p) {
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`/api/v1/admin/access/sessions?page=${p}`, { credentials: 'same-origin' })
    if (res.status === 403) {
      router.replace('/admin/login')
      return
    }
    if (!res.ok) {
      error.value = 'Failed to load sessions.'
      return
    }
    const json = await res.json()
    const data = json.data
    sessions.value = data.sessions
    page.value = data.page
    totalSessions.value = data.total_sessions
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

watch(
  () => route.query.page,
  (val) => {
    const p = parseInt(val) || 1
    loadPage(p)
  },
)

onMounted(async () => {
  const ok = await checkAuth()
  if (ok) {
    const p = parseInt(route.query.page) || 1
    loadPage(p)
  }
})
</script>

<template>
  <div class="mx-auto max-w-4xl px-4 py-8">
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
            <BreadcrumbPage>Session claims</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    </div>

    <div class="mb-6 flex items-center gap-2">
      <ShieldCheck class="h-5 w-5 text-muted-foreground" />
      <h1 class="text-2xl font-semibold">Session claims</h1>
      <Badge v-if="!loading" variant="secondary" class="ml-auto">
        {{ totalSessions }} session{{ totalSessions !== 1 ? 's' : '' }}
      </Badge>
    </div>

    <!-- Loading skeletons -->
    <div v-if="loading" class="flex flex-col gap-4">
      <Skeleton class="h-28 w-full rounded-lg" v-for="i in 3" :key="i" />
    </div>

    <!-- Error state -->
    <p v-else-if="error" class="text-sm text-destructive">{{ error }}</p>

    <!-- Empty state -->
    <p v-else-if="sessions.length === 0" class="text-sm text-muted-foreground">
      No sessions have claimed any access codes yet.
    </p>

    <!-- Session table -->
    <div v-else class="overflow-x-auto rounded-md border">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b bg-muted/50 text-left text-xs text-muted-foreground">
            <th class="px-3 py-2 font-medium">Session</th>
            <th class="px-3 py-2 font-medium">Code</th>
            <th class="px-3 py-2 font-medium">Nick</th>
            <th class="px-3 py-2 font-medium">Patterns</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="group in sessions" :key="group.session_id ?? '__null__'">
            <tr
              v-for="(entry, i) in group.codes"
              :key="entry.code"
              class="border-b last:border-0 hover:bg-muted/30"
            >
              <td class="px-3 py-1.5 font-mono text-xs text-muted-foreground align-top">
                <span v-if="i === 0">{{ group.session_id ?? '(no session)' }}</span>
              </td>
              <td class="px-3 py-1.5 font-mono text-xs align-top">{{ entry.code }}</td>
              <td class="px-3 py-1.5 text-xs text-muted-foreground align-top">{{ entry.nick ?? '—' }}</td>
              <td class="px-3 py-1.5 align-top">
                <div class="flex flex-wrap gap-1">
                  <code
                    v-for="pattern in entry.patterns"
                    :key="pattern"
                    class="rounded bg-muted px-1 py-0.5 text-xs font-mono"
                  >{{ pattern }}</code>
                </div>
              </td>
            </tr>
          </template>
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
