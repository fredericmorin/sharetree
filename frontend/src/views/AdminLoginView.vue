<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/card/index.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import CardDescription from '@/components/ui/card/CardDescription.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import Button from '@/components/ui/button/index.vue'
import Input from '@/components/ui/input/index.vue'
import { ShieldCheck } from 'lucide-vue-next'

const router = useRouter()

const password = ref('')
const error = ref(null)
const submitting = ref(false)

async function checkAlreadyAuthenticated() {
  try {
    const res = await fetch('/api/v1/me', { credentials: 'same-origin' })
    if (res.ok) {
      const data = await res.json()
      if (data.data?.is_admin) {
        router.replace('/admin')
      }
    }
  } catch {
    // ignore
  }
}

async function login() {
  error.value = null
  submitting.value = true
  try {
    const res = await fetch('/api/v1/admin/login', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: password.value }),
    })
    if (res.status === 401) {
      error.value = 'Invalid password.'
      return
    }
    if (res.status === 503) {
      error.value = 'Admin login is not configured on this server.'
      return
    }
    if (!res.ok) {
      error.value = 'Login failed. Please try again.'
      return
    }
    router.push('/admin')
  } finally {
    submitting.value = false
  }
}

onMounted(checkAlreadyAuthenticated)
</script>

<template>
  <div class="flex justify-center pt-8">
    <Card class="w-full max-w-md">
      <CardHeader>
        <div class="flex items-center gap-2">
          <ShieldCheck class="h-5 w-5 text-muted-foreground" />
          <CardTitle class="text-xl">Admin login</CardTitle>
        </div>
        <CardDescription>Enter the admin password to continue.</CardDescription>
      </CardHeader>

      <CardContent>
        <form @submit.prevent="login" class="flex gap-2">
          <Input
            v-model="password"
            type="password"
            placeholder="Password"
            autocomplete="current-password"
            autofocus
            :disabled="submitting"
            class="flex-1"
          />
          <Button type="submit" :disabled="submitting || !password">
            {{ submitting ? 'Logging in…' : 'Login' }}
          </Button>
        </form>

        <p v-if="error" class="mt-3 text-sm text-destructive">
          {{ error }}
        </p>
      </CardContent>
    </Card>
  </div>
</template>
