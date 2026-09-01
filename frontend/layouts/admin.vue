<template>
  <div class="flex min-h-screen flex-col bg-vanilla md:flex-row">
    <AdminSidebar />
    <div class="flex-1">
      <header class="flex justify-end border-b border-line bg-white px-4 py-3 sm:px-6 lg:px-8">
        <NotificationBell />
      </header>
      <main class="p-4 sm:p-6 lg:p-8">
        <slot />
      </main>
    </div>
  </div>
</template>
