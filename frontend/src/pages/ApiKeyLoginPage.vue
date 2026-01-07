<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { api } from '@/api/client'

const router = useRouter()
const authStore = useAuthStore()

const apiKeyInput = ref('')
const errorMessage = ref('')
const isValidating = ref(false)

async function handleLogin() {
  if (!apiKeyInput.value.trim()) {
    errorMessage.value = 'Please enter an API key'
    return
  }

  if (!apiKeyInput.value.startsWith('3dp_')) {
    errorMessage.value = 'Invalid API key format. Keys should start with "3dp_"'
    return
  }

  isValidating.value = true
  errorMessage.value = ''

  try {
    // Test the API key by calling the health endpoint
    authStore.login(apiKeyInput.value)

    // Try a simple authenticated endpoint to verify the key works
    await api.get('/api/admin/system')

    // If successful, redirect to dashboard
    router.push('/')
  } catch (error: any) {
    authStore.logout()

    if (error.response?.status === 401) {
      errorMessage.value = 'Invalid API key. Please check and try again.'
    } else if (error.response?.status === 403) {
      errorMessage.value = 'Access forbidden. This API key may be inactive or expired.'
    } else {
      errorMessage.value = 'Failed to connect to the server. Please try again.'
    }
  } finally {
    isValidating.value = false
  }
}

function handleKeyPress(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    handleLogin()
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <div class="logo-section">
        <i class="pi pi-box" style="font-size: 3rem; color: var(--p-primary-color)"></i>
        <h1>3D Print Logger</h1>
        <p class="subtitle">Enter your API key to continue</p>
      </div>

      <Card class="login-card">
        <template #content>
          <div class="login-form">
            <Message v-if="errorMessage" severity="error" :closable="false">
              {{ errorMessage }}
            </Message>

            <div class="form-field">
              <label for="api-key">API Key</label>
              <InputText
                id="api-key"
                v-model="apiKeyInput"
                type="password"
                placeholder="3dp_..."
                class="w-full"
                :disabled="isValidating"
                @keypress="handleKeyPress"
                autofocus
              />
              <small class="help-text">
                If you don't have an API key, create one using the admin tools or contact your
                administrator.
              </small>
            </div>

            <Button
              label="Login"
              class="w-full"
              :loading="isValidating"
              :disabled="!apiKeyInput.trim()"
              @click="handleLogin"
            />
          </div>
        </template>
      </Card>

      <div class="help-section">
        <p class="help-text">
          <strong>Need an API key?</strong><br />
          Run this command on your server to generate one:
        </p>
        <pre class="command-box">docker exec print-logger python -c "
import secrets, hashlib
from sqlalchemy import create_engine, text
from datetime import datetime

key = f'3dp_{secrets.token_hex(32)}'
hash = hashlib.sha256(key.encode()).hexdigest()

engine = create_engine('sqlite:///data/printlog.db')
with engine.connect() as conn:
    conn.execute(text('''
        INSERT INTO api_keys (key_hash, key_prefix, name, is_active, created_at, updated_at)
        VALUES (:h, :p, :n, 1, :t, :t)
    '''), {'h': hash, 'p': key[:12], 'n': 'user', 't': datetime.utcnow()})
    conn.commit()
print(f'API Key: {key}')
"</pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--p-surface-ground) 0%, var(--p-surface-100) 100%);
  padding: 2rem;
}

.login-container {
  width: 100%;
  max-width: 480px;
}

.logo-section {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-section h1 {
  margin: 1rem 0 0.5rem 0;
  font-size: 2rem;
  color: var(--p-text-color);
}

.subtitle {
  color: var(--p-text-muted-color);
  margin: 0;
}

.login-card {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-field label {
  font-weight: 500;
  color: var(--p-text-color);
}

.help-text {
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
  margin: 0;
}

.w-full {
  width: 100%;
}

.help-section {
  margin-top: 2rem;
  padding: 1.5rem;
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
  border: 1px solid var(--p-surface-border);
}

.help-section .help-text {
  margin-bottom: 1rem;
  line-height: 1.6;
}

.command-box {
  background-color: var(--p-surface-100);
  padding: 1rem;
  border-radius: var(--p-border-radius);
  font-size: 0.75rem;
  overflow-x: auto;
  margin: 0;
  border: 1px solid var(--p-surface-border);
}

@media (max-width: 768px) {
  .login-page {
    padding: 1rem;
  }

  .logo-section h1 {
    font-size: 1.5rem;
  }

  .command-box {
    font-size: 0.65rem;
  }
}
</style>
