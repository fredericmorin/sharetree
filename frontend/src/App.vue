<template>
  <div id="app-root">
    <header>
      <RouterLink to="/" class="brand">sharetree</RouterLink>
    </header>
    <main>
      <RouterView />
    </main>
  </div>
</template>

<style>
*, *::before, *::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: system-ui, -apple-system, sans-serif;
  background: #f8f9fa;
  color: #212529;
}

#app-root {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 1rem;
}

header {
  padding: 1rem 0;
  border-bottom: 1px solid #dee2e6;
  margin-bottom: 1.5rem;
}

.brand {
  font-size: 1.25rem;
  font-weight: 600;
  color: #212529;
  text-decoration: none;
}

.brand:hover {
  color: #0d6efd;
}

a {
  color: #0d6efd;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
</style>
