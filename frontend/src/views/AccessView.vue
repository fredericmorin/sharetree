<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClipboard } from '@vueuse/core'
import Card from '@/components/ui/card/index.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import CardDescription from '@/components/ui/card/CardDescription.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardFooter from '@/components/ui/card/CardFooter.vue'
import Button from '@/components/ui/button/index.vue'
import Input from '@/components/ui/input/index.vue'
import Badge from '@/components/ui/badge/index.vue'
import Separator from '@/components/ui/separator/index.vue'
import { Copy, Check, KeyRound } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const codeInput = ref('')
const error = ref(null)
const submitting = ref(false)
const activeCodes = ref([])

const { copy, copied, isSupported: clipboardSupported } = useClipboard()

async function fetchActiveCodes() {
  try {
    const res = await fetch('/api/v1/access', { credentials: 'same-origin' })
    if (!res.ok) return
    const data = await res.json()
    activeCodes.value = data.data?.active_code_details ?? []
  } catch {
    // silently ignore
  }
}

async function activate() {
  error.value = null
  submitting.value = true
  try {
    const res = await fetch('/api/v1/access/activate', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: codeInput.value.trim() }),
    })
    if (res.status === 404) {
      error.value = 'Invalid access code.'
      return
    }
    if (!res.ok) {
      error.value = 'Activation failed. Please try again.'
      return
    }
    codeInput.value = ''
    await fetchActiveCodes()
    const next = route.query.next || '/'
    router.push(next)
  } finally {
    submitting.value = false
  }
}

onMounted(fetchActiveCodes)
</script>

<template>
  <div class="flex justify-center pt-8">
    <Card class="w-full max-w-md">
      <CardHeader>
        <div class="flex items-center gap-2">
          <KeyRound class="h-5 w-5 text-muted-foreground" />
          <CardTitle class="text-xl">Enter access code</CardTitle>
        </div>
        <CardDescription>You need an access code to browse files.</CardDescription>
      </CardHeader>

      <CardContent>
        <form @submit.prevent="activate" class="flex gap-2">
          <Input
            v-model="codeInput"
            type="text"
            placeholder="Access code"
            autocomplete="off"
            autofocus
            :disabled="submitting"
            class="flex-1"
          />
          <Button type="submit" :disabled="submitting || !codeInput.trim()">
            {{ submitting ? 'Activating…' : 'Activate' }}
          </Button>
        </form>

        <p v-if="error" class="mt-3 text-sm text-destructive flex items-center gap-1.5">
          {{ error }}
        </p>
      </CardContent>

      <template v-if="activeCodes.length">
        <Separator />
        <CardFooter class="flex-col items-start gap-3 pt-4">
          <p class="text-sm text-muted-foreground font-medium">Active access codes</p>
          <ul class="flex flex-col gap-2 w-full">
            <li
              v-for="detail in activeCodes"
              :key="detail.code"
              class="flex items-center justify-between gap-2 rounded-md border bg-muted/40 px-3 py-2"
            >
              <div class="flex items-center gap-2 min-w-0">
                <code class="font-mono text-sm truncate">{{ detail.code }}</code>
                <Badge v-if="detail.nick" variant="secondary" class="shrink-0">{{ detail.nick }}</Badge>
              </div>
              <Button
                v-if="clipboardSupported"
                variant="ghost"
                size="icon"
                class="h-7 w-7 shrink-0"
                type="button"
                :aria-label="`Copy code ${detail.code}`"
                @click="copy(detail.code)"
              >
                <Check v-if="copied" class="h-3.5 w-3.5 text-green-500" />
                <Copy v-else class="h-3.5 w-3.5" />
              </Button>
            </li>
          </ul>
        </CardFooter>
      </template>
    </Card>
  </div>
</template>
