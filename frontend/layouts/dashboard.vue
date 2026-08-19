<template>
  <div class="flex min-h-screen flex-col bg-vanilla md:flex-row">
    <DashboardSidebar />
    <main class="flex-1 p-4 sm:p-6 lg:p-8">
      <slot />
    </main>
  </div>
</template>
