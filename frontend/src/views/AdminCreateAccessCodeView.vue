<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClipboard } from '@vueuse/core'
import Card from '@/components/ui/card/index.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import CardDescription from '@/components/ui/card/CardDescription.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import Button from '@/components/ui/button/index.vue'
import Input from '@/components/ui/input/index.vue'
import { FilePlus, Copy, Check, ArrowLeft } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const patterns = ref('')
const nick = ref('')
const submitting = ref(false)
const error = ref(null)
const createdCode = ref(null)

const { copy, copied, isSupported: clipboardSupported } = useClipboard()

async function checkAuth() {
  try {
    const res = await fetch('/api/v1/admin/me', { credentials: 'same-origin' })
    if (!res.ok) {
      router.replace('/admin/login')
      return
    }
    const data = await res.json()
    if (!data.data?.authenticated) {
      router.replace('/admin/login')
    }
  } catch {
    router.replace('/admin/login')
  }
}

async function submit() {
  error.value = null
  submitting.value = true
  try {
    const patternList = patterns.value
      .split('\n')
      .map((p) => p.trim())
      .filter(Boolean)

    if (!patternList.length) {
      error.value = 'At least one pattern is required.'
      return
    }

    const res = await fetch('/api/v1/admin/access/create', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patterns: patternList, nick: nick.value.trim() || null }),
    })

    if (res.status === 401 || res.status === 403) {
      router.replace('/admin/login')
      return
    }

    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      error.value = body.detail ?? 'Failed to create access code.'
      return
    }

    const json = await res.json()
    createdCode.value = json.data
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  checkAuth()
  const pattern = route.query.pattern
  if (pattern) {
    patterns.value = pattern
  }
})
</script>

<template>
  <div class="flex justify-center pt-8">
    <Card class="w-full max-w-lg">
      <CardHeader>
        <div class="flex items-center gap-2">
          <FilePlus class="h-5 w-5 text-muted-foreground" />
          <CardTitle class="text-xl">Create access code</CardTitle>
        </div>
        <CardDescription>
          Generate a new access code with the specified glob patterns.
        </CardDescription>
      </CardHeader>

      <CardContent class="flex flex-col gap-4">
        <!-- Success state -->
        <template v-if="createdCode">
          <div class="rounded-md border border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950 p-4 flex flex-col gap-3">
            <p class="text-sm font-medium text-green-800 dark:text-green-200">Access code created successfully</p>
            <div class="flex items-center gap-2">
              <code class="flex-1 font-mono text-sm bg-background rounded px-2 py-1 border truncate">
                {{ createdCode.code }}
              </code>
              <Button
                v-if="clipboardSupported"
                variant="outline"
                size="icon"
                class="h-8 w-8 shrink-0"
                type="button"
                aria-label="Copy access code"
                @click="copy(createdCode.code)"
              >
                <Check v-if="copied" class="h-3.5 w-3.5 text-green-500" />
                <Copy v-else class="h-3.5 w-3.5" />
              </Button>
            </div>
            <div v-if="createdCode.nick" class="text-sm text-muted-foreground">
              Label: <span class="font-medium text-foreground">{{ createdCode.nick }}</span>
            </div>
            <div class="text-sm text-muted-foreground">
              Patterns:
              <ul class="mt-1 space-y-0.5">
                <li v-for="p in createdCode.patterns" :key="p" class="font-mono text-xs text-foreground">{{ p }}</li>
              </ul>
            </div>
          </div>

          <div class="flex gap-2">
            <Button variant="outline" class="flex-1 gap-2" @click="router.back()">
              <ArrowLeft class="h-4 w-4" />
              Back to browse
            </Button>
            <Button
              variant="outline"
              class="flex-1"
              @click="() => { createdCode = null; error = null }"
            >
              Create another
            </Button>
          </div>
        </template>

        <!-- Form -->
        <template v-else>
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium">Patterns <span class="text-muted-foreground font-normal">(one per line)</span></label>
            <textarea
              v-model="patterns"
              rows="4"
              placeholder="/reports/**"
              class="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
              :disabled="submitting"
            />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium">
              Label <span class="text-muted-foreground font-normal">(optional)</span>
            </label>
            <Input
              v-model="nick"
              type="text"
              placeholder="e.g. Q1 reports for Alice"
              :disabled="submitting"
            />
          </div>

          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>

          <div class="flex gap-2">
            <Button variant="outline" class="gap-2" @click="router.back()">
              <ArrowLeft class="h-4 w-4" />
              Back
            </Button>
            <Button class="flex-1" :disabled="submitting || !patterns.trim()" @click="submit">
              {{ submitting ? 'Creating…' : 'Create access code' }}
            </Button>
          </div>
        </template>
      </CardContent>
    </Card>
  </div>
</template>
