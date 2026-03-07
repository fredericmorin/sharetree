<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Card from '@/components/ui/card/index.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import CardDescription from '@/components/ui/card/CardDescription.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import Button from '@/components/ui/button/index.vue'
import Badge from '@/components/ui/badge/index.vue'
import Skeleton from '@/components/ui/skeleton/index.vue'
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
    const res = await fetch('/api/v1/admin/me', { credentials: 'same-origin' })
    if (!res.ok) {
      router.replace('/admin/login')
      return false
    }
    const data = await res.json()
    if (!data.data?.authenticated) {
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

    <!-- Session list -->
    <div v-else class="flex flex-col gap-4">
      <Card v-for="group in sessions" :key="group.session_id ?? '__null__'">
        <CardHeader class="pb-2">
          <CardTitle class="font-mono text-sm font-medium text-muted-foreground">
            {{ group.session_id ?? '(no session)' }}
          </CardTitle>
          <CardDescription>
            {{ group.codes.length }} access code{{ group.codes.length !== 1 ? 's' : '' }}
          </CardDescription>
        </CardHeader>

        <CardContent>
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b text-left text-muted-foreground">
                <th class="pb-1 pr-4 font-medium">Code</th>
                <th class="pb-1 font-medium">Nick</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="entry in group.codes"
                :key="entry.code"
                class="border-b last:border-0"
              >
                <td class="py-1 pr-4 font-mono">{{ entry.code }}</td>
                <td class="py-1 text-muted-foreground">{{ entry.nick ?? '—' }}</td>
              </tr>
            </tbody>
          </table>
        </CardContent>
      </Card>
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
