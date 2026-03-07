<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import Breadcrumb from '@/components/ui/breadcrumb/index.vue'
import BreadcrumbList from '@/components/ui/breadcrumb/BreadcrumbList.vue'
import BreadcrumbItem from '@/components/ui/breadcrumb/BreadcrumbItem.vue'
import BreadcrumbLink from '@/components/ui/breadcrumb/BreadcrumbLink.vue'
import BreadcrumbPage from '@/components/ui/breadcrumb/BreadcrumbPage.vue'
import BreadcrumbSeparator from '@/components/ui/breadcrumb/BreadcrumbSeparator.vue'
import { House } from 'lucide-vue-next'

const props = defineProps({
  path: { type: String, default: '' },
})

const segments = computed(() => {
  const parts = props.path.split('/').filter(Boolean)
  return parts.map((part, i) => ({
    label: part,
    to: '/browse/' + parts.slice(0, i + 1).join('/'),
  }))
})
</script>

<template>
  <Breadcrumb>
    <BreadcrumbList>
      <BreadcrumbItem>
        <BreadcrumbLink as-child>
          <RouterLink to="/" class="flex items-center text-muted-foreground hover:text-foreground transition-colors no-underline">
            <House class="h-4 w-4" />
          </RouterLink>
        </BreadcrumbLink>
      </BreadcrumbItem>

      <template v-for="(seg, i) in segments" :key="seg.to">
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          <BreadcrumbPage v-if="i === segments.length - 1">{{ seg.label }}</BreadcrumbPage>
          <BreadcrumbLink v-else as-child>
            <RouterLink :to="seg.to" class="text-muted-foreground hover:text-foreground transition-colors no-underline">
              {{ seg.label }}
            </RouterLink>
          </BreadcrumbLink>
        </BreadcrumbItem>
      </template>
    </BreadcrumbList>
  </Breadcrumb>
</template>
