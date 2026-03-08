<script setup>
import { useRouter } from 'vue-router'
import Button from '@/components/ui/button/index.vue'
import { Home } from 'lucide-vue-next'

const router = useRouter()
</script>

<template>
  <div class="flex flex-col items-center justify-center pt-24 gap-4 text-center">
    <p class="text-8xl font-bold text-muted-foreground/30">404</p>
    <h1 class="text-2xl font-semibold">Page not found</h1>
    <p class="text-muted-foreground">The page you're looking for doesn't exist.</p>
    <Button variant="outline" class="mt-2" @click="router.push('/')">
      <Home class="h-4 w-4 mr-2" />
      Go home
    </Button>
  </div>
</template>
