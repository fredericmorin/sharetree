<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const codeInput = ref('')
const error = ref(null)
const submitting = ref(false)
const activeCodes = ref([])

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
  <div class="access-page">
    <h1>Enter access code</h1>
    <p class="hint">You need an access code to browse files.</p>
    <form @submit.prevent="activate" class="access-form">
      <input
        v-model="codeInput"
        type="text"
        placeholder="Access code"
        autocomplete="off"
        autofocus
        :disabled="submitting"
        class="code-input"
      />
      <button type="submit" :disabled="submitting || !codeInput.trim()" class="submit-btn">
        {{ submitting ? 'Activating…' : 'Activate' }}
      </button>
    </form>
    <p v-if="error" class="error">{{ error }}</p>

    <section v-if="activeCodes.length" class="active-codes">
      <h2>Active access codes</h2>
      <ul>
        <li v-for="detail in activeCodes" :key="detail.code" class="code-item">
          <code class="code-value">{{ detail.code }}</code>
          <span v-if="detail.nick" class="code-nick">{{ detail.nick }}</span>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.access-page {
  max-width: 400px;
  margin: 2rem auto;
}

h1 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.hint {
  color: #6c757d;
  margin-bottom: 1.5rem;
}

.access-form {
  display: flex;
  gap: 0.5rem;
}

.code-input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  font-size: 1rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  outline: none;
}

.code-input:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.15);
}

.submit-btn {
  padding: 0.5rem 1rem;
  font-size: 1rem;
  background: #0d6efd;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.submit-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.submit-btn:not(:disabled):hover {
  background: #0b5ed7;
}

.error {
  margin-top: 0.75rem;
  color: #dc3545;
}

.active-codes {
  margin-top: 2rem;
}

.active-codes h2 {
  font-size: 1rem;
  color: #6c757d;
  margin-bottom: 0.75rem;
}

.active-codes ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.code-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.4rem 0.6rem;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.code-value {
  font-family: monospace;
  font-size: 0.9rem;
  color: #212529;
}

.code-nick {
  font-size: 0.85rem;
  color: #6c757d;
}
</style>
