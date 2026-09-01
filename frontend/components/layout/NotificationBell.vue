<script setup lang="ts">
import { notificationService } from "~/services/notification.service";
import type { AppNotification } from "~/types";

const open = ref(false);
const notifications = ref<AppNotification[]>([]);
const loading = ref(false);

const unreadCount = computed(() => notifications.value.filter((n) => !n.is_read).length);

async function load() {
  loading.value = true;
  try {
    const { data } = await notificationService.list({ page_size: 20 });
    notifications.value = data.results;
  } finally {
    loading.value = false;
  }
}
await load();

async function toggle() {
  open.value = !open.value;
  if (open.value) await load();
}

async function markRead(notification: AppNotification) {
  if (notification.is_read) return;
  notification.is_read = true;
  await notificationService.markRead(notification.id);
}

async function markAllRead() {
  notifications.value.forEach((n) => (n.is_read = true));
  await notificationService.markAllRead();
}

function timeAgo(value: string) {
  const diffMs = Date.now() - new Date(value).getTime();
  const minutes = Math.round(diffMs / 60000);
  if (minutes < 1) return "ahora";
  if (minutes < 60) return `hace ${minutes} min`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `hace ${hours} h`;
  return `hace ${Math.round(hours / 24)} d`;
}

const iconFor = (type: AppNotification["type"]) => (type === "new_registration" ? "users" : "logout");
</script>

<template>
  <div class="relative">
    <button
      class="relative flex h-9 w-9 items-center justify-center rounded-full border border-line bg-white text-muted hover:border-gold hover:text-gold"
      @click="toggle"
    >
      <AppIcon name="bell" :size="18" />
      <span
        v-if="unreadCount > 0"
        class="absolute -right-1 -top-1 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-gold px-1 text-[10px] font-semibold text-white"
      >
        {{ unreadCount > 9 ? "9+" : unreadCount }}
      </span>
    </button>

    <div
      v-if="open"
      class="absolute right-0 z-50 mt-2 w-80 rounded-xl2 border border-line bg-white p-2 shadow-soft"
      @click.self="open = false"
    >
      <div class="flex items-center justify-between px-2 py-1">
        <p class="text-sm font-semibold text-ink">Notificaciones</p>
        <button v-if="unreadCount > 0" class="text-xs font-semibold text-gold hover:underline" @click="markAllRead">
          Marcar todas leídas
        </button>
      </div>

      <LoadingSpinner v-if="loading" label="Cargando..." />
      <div v-else class="max-h-96 space-y-1 overflow-y-auto">
        <NuxtLink
          v-for="n in notifications"
          :key="n.id"
          to="/admin/users"
          class="flex items-start gap-3 rounded-xl2 px-2 py-2 text-sm hover:bg-gold-light/40"
          :class="!n.is_read && 'bg-gold-light/20'"
          @click="markRead(n)"
        >
          <span class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gold-light text-gold">
            <AppIcon :name="iconFor(n.type)" :size="14" />
          </span>
          <span class="flex-1">
            <span class="block text-ink">{{ n.message }}</span>
            <span class="mt-0.5 block text-xs text-muted">{{ timeAgo(n.created_at) }}</span>
          </span>
          <span v-if="!n.is_read" class="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-gold" />
        </NuxtLink>
        <p v-if="!notifications.length" class="px-2 py-6 text-center text-sm text-muted">No hay notificaciones.</p>
      </div>
    </div>
  </div>
</template>
