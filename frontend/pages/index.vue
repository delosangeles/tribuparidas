<script setup lang="ts">
import { businessService } from "~/services/business.service";
import { blogService } from "~/services/blog.service";
import type { Business, BlogPost } from "~/types";

const authStore = useAuthStore();
const featureFlagStore = useFeatureFlagStore();

// El blog puede tener activación programada (ver /admin/lanzamiento): no se
// promociona en el home hasta esa fecha, salvo para el equipo admin.
const canSeeBlog = computed(() => featureFlagStore.isBlogLive || authStore.isAdmin);

const featured = ref<Business[]>([]);
const latestPosts = ref<BlogPost[]>([]);

// La portada es pública: no exige sesión. Las noticias que se muestran
// dependen de si hay sesión (públicas + privadas) o no (solo públicas); eso
// lo decide la API.
try {
  const { data } = await businessService.list({ ordering: "-created_at", page_size: 4 });
  featured.value = data.results;
} catch {
  featured.value = [];
}

if (canSeeBlog.value) {
  try {
    const { data: blogData } = await blogService.list({ page_size: 4 });
    latestPosts.value = blogData.results;
  } catch {
    latestPosts.value = [];
  }
}

import { newsService } from "~/services/news.service";
import type { News } from "~/types";

const activeNews = ref<News[]>([]);
const currentNewsIndex = ref(0);
let newsInterval: ReturnType<typeof setInterval> | null = null;

async function loadActiveNews() {
  try {
    const { data } = await newsService.active();

    activeNews.value = data.slice(0, 5);
    currentNewsIndex.value = 0;

    startNewsCarousel();
  } catch (error) {
    console.error("Error cargando noticias:", error);
    activeNews.value = [];
  }
}

function startNewsCarousel() {
  if (newsInterval) {
    clearInterval(newsInterval);
  }

  if (activeNews.value.length <= 1) return;

  newsInterval = setInterval(() => {
    currentNewsIndex.value =
      (currentNewsIndex.value + 1) % activeNews.value.length;
  }, 5000);
}

function nextNews() {
  if (!activeNews.value.length) return;

  currentNewsIndex.value =
    (currentNewsIndex.value + 1) % activeNews.value.length;

  startNewsCarousel();
}

function previousNews() {
  if (!activeNews.value.length) return;

  currentNewsIndex.value =
    (currentNewsIndex.value - 1 + activeNews.value.length) %
    activeNews.value.length;

  startNewsCarousel();
}

function goToNews(index: number) {
  currentNewsIndex.value = index;
  startNewsCarousel();
}

await loadActiveNews();

onBeforeUnmount(() => {
  if (newsInterval) {
    clearInterval(newsInterval);
  }
});
</script>

<style>
.banner-enter-active,
.banner-leave-active {
  transition: opacity 0.4s ease;
}

.banner-enter-from,
.banner-leave-to {
  opacity: 0;
}
</style>

<template>
  <div>
    <section
      v-if="activeNews.length"
      class="w-full flex justify-center overflow-hidden"
    >
      <div class="relative w-full md:w-3/4 max-w-[1400px]">

        <!-- Banner actual -->
        <div class="w-full">
          <a
            v-if="activeNews[currentNewsIndex]?.link"
            :href="activeNews[currentNewsIndex].link"
            target="_blank"
            rel="noopener noreferrer"
            class="block w-full"
          >
            <picture>
              <source
                media="(max-width: 767px)"
                :srcset="activeNews[currentNewsIndex].image_mobile"
              />

              <img
                :src="activeNews[currentNewsIndex].image_desktop"
                :alt="activeNews[currentNewsIndex].title"
                class="w-full h-auto block"
              />
            </picture>
          </a>

          <picture v-else>
            <source
              media="(max-width: 767px)"
              :srcset="activeNews[currentNewsIndex].image_mobile"
            />

            <img
              :src="activeNews[currentNewsIndex].image_desktop"
              :alt="activeNews[currentNewsIndex].title"
              class="w-full h-auto block"
            />
          </picture>
        </div>

        <!-- Flecha anterior -->
        <button
          v-if="activeNews.length > 1"
          type="button"
          class="absolute left-3 top-1/2 -translate-y-1/2 rounded-full bg-black/30 px-3 py-2 text-2xl leading-none text-white transition hover:bg-black/50"
          aria-label="Banner anterior"
          @click="previousNews"
        >
          ‹
        </button>

        <!-- Flecha siguiente -->
        <button
          v-if="activeNews.length > 1"
          type="button"
          class="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-black/30 px-3 py-2 text-2xl leading-none text-white transition hover:bg-black/50"
          aria-label="Siguiente banner"
          @click="nextNews"
        >
          ›
        </button>

        <!-- Indicadores -->
        <div
          v-if="activeNews.length > 1"
          class="absolute bottom-3 left-1/2 flex -translate-x-1/2 gap-2"
        >
          <button
            v-for="(item, index) in activeNews"
            :key="item.id"
            type="button"
            :aria-label="`Ir al banner ${index + 1}`"
            class="h-2.5 w-2.5 rounded-full transition"
            :class="
              currentNewsIndex === index
                ? 'scale-110 bg-white'
                : 'bg-white/50'
            "
            @click="goToNews(index)"
          />
        </div>

      </div>
    </section>

    <!-- <section class="w-full flex justify-center overflow-hidden">
      <NuxtLink
        to="https://wa.me/+573008478168?text=Hola%20Maria%20Isabel%20de%20Tribu%20Paridas,%20quiero%20inscribirme%20en%20la%20Media%20Marat%C3%B3n%20de%20Palmira"
        class="block w-full md:w-3/4 max-w-[1400px]"
      >
        <picture>
          <source
            media="(max-width: 767px)"
            :srcset="useAssetUrl('MaratonMamas2709.jpg')"
          />

          <img
            :src="useAssetUrl('MaratonMamas2709BAnner.jpg')"
            alt="Mamás en movimiento - Media Maratón Internacional Ciudad de Palmira"
            class="w-full h-auto block"
          />
        </picture>
      </NuxtLink>
    </section> -->
    <!-- <img :src="useAssetUrl('hero-inicio.png')" alt="Bienvenidas a nuestra página web" class="w-full" /> -->

    <!-- <section class="mx-auto max-w-7xl px-4 pt-8 sm:px-6">
      <CountdownTimer target="2026-09-01T19:00:00-05:00" label="¡Falta poco!" />
    </section> -->

    <!-- Del blog -->
    <section v-if="canSeeBlog && latestPosts.length" class="mx-auto max-w-7xl px-4 pt-10 sm:px-6">
      <div class="mb-6 flex items-center justify-between">
        <h2 class="flex items-center gap-2 text-xl font-bold text-ink">
          <AppIcon name="file-text" :size="18" class="text-gold" />
          Del blog
        </h2>
        <NuxtLink to="/blog" class="text-sm font-semibold text-gold hover:underline">Ver todos</NuxtLink>
      </div>

      <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <article
          v-for="post in latestPosts"
          :key="post.id"
          class="card group cursor-pointer overflow-hidden transition hover:-translate-y-1 hover:shadow-md"
          @click="navigateTo(`/blog/${post.slug}`)"
        >
          <div class="aspect-[4/3] overflow-hidden bg-gold-light">
            <img
              v-if="post.main_image"
              :src="post.main_image"
              :alt="post.title"
              class="h-full w-full object-cover transition duration-300 group-hover:scale-105"
            />
            <div v-else class="flex h-full w-full items-center justify-center text-gold">
              <AppIcon name="file-text" :size="28" />
            </div>
          </div>

          <div class="p-3">
            <span class="badge bg-gold-light text-gold">{{ post.category_name }}</span>
            <h3 class="mt-2 line-clamp-2 text-sm font-semibold text-ink">{{ post.title }}</h3>
          </div>
        </article>
      </div>
    </section>

    <section class="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <div class="mb-6 flex items-center justify-between">
        <h2 class="flex items-center gap-2 text-xl font-bold text-ink">
          <AppIcon name="heart" :size="18" class="text-gold" />
          Últimos emprendimientos
        </h2>
        <NuxtLink to="/emprendimientos" class="text-sm font-semibold text-gold hover:underline">Ver todos</NuxtLink>
      </div>

      <div v-if="featured?.length" class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        <BusinessCard v-for="business in featured" :key="business.id" :business="business" />
      </div>
      <EmptyState v-else icon="briefcase" title="Todavía no hay emprendimientos publicados" description="Vuelve pronto, estamos sumando nuevas historias." />
    </section>
  </div>
</template>
