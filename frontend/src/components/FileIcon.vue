<script setup>
import {
  Folder,
  File,
  FileText,
  Image,
  Video,
  Music,
  Archive,
  Code,
  FileSpreadsheet,
  Presentation,
} from 'lucide-vue-next'

const props = defineProps({
  filename: { type: String, default: '' },
  isDirectory: { type: Boolean, default: false },
  class: { type: String, default: '' },
})

const IMAGE_EXTS = new Set(['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico', 'avif'])
const VIDEO_EXTS = new Set(['mp4', 'mkv', 'avi', 'mov', 'webm', 'flv', 'wmv'])
const AUDIO_EXTS = new Set(['mp3', 'flac', 'wav', 'ogg', 'aac', 'm4a', 'opus'])
const ARCHIVE_EXTS = new Set(['zip', 'tar', 'gz', 'bz2', 'xz', 'rar', '7z', 'zst'])
const CODE_EXTS = new Set(['js', 'ts', 'jsx', 'tsx', 'vue', 'py', 'sh', 'bash', 'zsh', 'rb', 'go', 'rs', 'java', 'c', 'cpp', 'h', 'cs', 'php', 'html', 'css', 'json', 'yaml', 'yml', 'toml', 'xml', 'sql'])
const SPREADSHEET_EXTS = new Set(['xls', 'xlsx', 'csv', 'ods'])
const PRESENTATION_EXTS = new Set(['ppt', 'pptx', 'odp', 'key'])

function getIcon() {
  if (props.isDirectory) return Folder
  const ext = props.filename.split('.').pop()?.toLowerCase() ?? ''
  if (IMAGE_EXTS.has(ext)) return Image
  if (VIDEO_EXTS.has(ext)) return Video
  if (AUDIO_EXTS.has(ext)) return Music
  if (ARCHIVE_EXTS.has(ext)) return Archive
  if (CODE_EXTS.has(ext)) return Code
  if (SPREADSHEET_EXTS.has(ext)) return FileSpreadsheet
  if (PRESENTATION_EXTS.has(ext)) return Presentation
  if (ext === 'pdf') return FileText
  return File
}
</script>

<template>
  <component
    :is="getIcon()"
    :class="['w-4 h-4 shrink-0', isDirectory ? 'text-blue-500 dark:text-blue-400' : 'text-muted-foreground', props.class]"
    aria-hidden="true"
  />
</template>
