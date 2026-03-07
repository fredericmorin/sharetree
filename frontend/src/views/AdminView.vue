<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/card/index.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import CardDescription from '@/components/ui/card/CardDescription.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import Button from '@/components/ui/button/index.vue'
import { ShieldCheck, Users } from 'lucide-vue-next'

const router = useRouter()

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

onMounted(checkAuth)
</script>

<template>
  <div class="flex justify-center pt-8">
    <Card class="w-full max-w-md">
      <CardHeader>
        <div class="flex items-center gap-2">
          <ShieldCheck class="h-5 w-5 text-muted-foreground" />
          <CardTitle class="text-xl">Admin dashboard</CardTitle>
        </div>
        <CardDescription>Manage sharetree access codes and sessions.</CardDescription>
      </CardHeader>

      <CardContent class="flex flex-col gap-2">
        <Button variant="outline" class="w-full justify-start gap-2" @click="router.push('/admin/sessions')">
          <Users class="h-4 w-4" />
          View session claims
        </Button>
      </CardContent>
    </Card>
  </div>
</template>
