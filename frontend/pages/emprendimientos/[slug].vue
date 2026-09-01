<script setup lang="ts">
import { businessService } from "~/services/business.service";
import { questionService } from "~/services/question.service";
import { reviewService } from "~/services/review.service";
import type { Question, Review } from "~/types";

const route = useRoute();
const slug = route.params.slug as string;
const authStore = useAuthStore();

const { data: business, error } = await useAsyncData(`business-${slug}`, async () => {
  const { data } = await businessService.retrieve(slug);
  return data;
});

if (error.value) {
  throw createError({ statusCode: 404, statusMessage: "Emprendimiento no encontrado" });
}

const BENEFIT_LABELS: Record<string, string> = {
  descuento: "Descuento",
  envio_gratis: "Envío gratis",
  promocion: "Promoción",
  precio_especial: "Precio especial",
  beneficio_exclusivo: "Beneficio exclusivo",
  otro: "Beneficio especial",
};

const tabs = [
  { key: "inicio", label: "Inicio" },
  { key: "sobre", label: "Sobre mí" },
  { key: "opiniones", label: "Opiniones" },
  { key: "preguntas", label: "Preguntas" },
];
const activeTab = ref("inicio");

const reviews = ref<Review[]>([]);
const questions = ref<Question[]>([]);
const isFavorite = ref(false);
const loadingSecondary = ref(false);

async function loadSecondaryData() {
  if (!business.value) return;
  loadingSecondary.value = true;
  try {
    const [reviewsRes, questionsRes] = await Promise.all([
      reviewService.listByBusiness(business.value.id),
      questionService.listByBusiness(business.value.id),
    ]);
    reviews.value = reviewsRes.data.results;
    questions.value = questionsRes.data.results;
  } finally {
    loadingSecondary.value = false;
  }
}
await loadSecondaryData();

const newQuestion = ref("");
const askingQuestion = ref(false);
const questionError = ref("");
async function submitQuestion() {
  if (!authStore.isAuthenticated) return navigateTo("/login");
  if (!newQuestion.value.trim() || !business.value) return;
  askingQuestion.value = true;
  questionError.value = "";
  try {
    const { data } = await questionService.ask(business.value.id, newQuestion.value.trim());
    questions.value = [data, ...questions.value];
    newQuestion.value = "";
    activeTab.value = "preguntas";
  } catch (err) {
    questionError.value = useErrorMessage(err);
  } finally {
    askingQuestion.value = false;
  }
}

const newRating = ref(5);
const newComment = ref("");
const submittingReview = ref(false);
const reviewError = ref("");
async function submitReview() {
  if (!authStore.isAuthenticated) return navigateTo("/login");
  if (!business.value) return;
  submittingReview.value = true;
  reviewError.value = "";
  try {
    const { data } = await reviewService.create(business.value.id, newRating.value, newComment.value.trim());
    reviews.value = [data, ...reviews.value];
    newComment.value = "";
  } catch (err) {
    reviewError.value = useErrorMessage(err);
  } finally {
    submittingReview.value = false;
  }
}

async function toggleFavorite() {
  if (!authStore.isAuthenticated || !business.value) return navigateTo("/login");
  if (isFavorite.value) {
    await reviewService.removeFavorite(business.value.id);
    isFavorite.value = false;
  } else {
    await reviewService.addFavorite(business.value.id);
    isFavorite.value = true;
  }
}

function shareBusiness() {
  if (import.meta.client && navigator.share && business.value) {
    navigator.share({ title: business.value.name, url: window.location.href }).catch(() => {});
  }
}
</script>

<template>
  <div v-if="business" class="mx-auto max-w-6xl px-4 py-6 sm:px-6">
    <nav class="mb-4 flex items-center gap-1 text-xs text-muted">
      <NuxtLink to="/" class="hover:text-gold">Inicio</NuxtLink>
      <span>/</span>
      <NuxtLink to="/emprendimientos" class="hover:text-gold">Emprendimientos</NuxtLink>
      <span>/</span>
      <NuxtLink :to="`/emprendimientos?category=${business.category.slug}`" class="hover:text-gold">{{ business.category.name }}</NuxtLink>
      <span>/</span>
      <span class="text-ink">{{ business.name }}</span>
    </nav>

    <div class="flex items-start justify-between">
      <div class="flex items-center gap-5">
        <span class="flex h-32 w-32 shrink-0 overflow-hidden rounded-full bg-gold-light">
          <img v-if="business.logo" :src="business.logo" :alt="business.name" class="h-full w-full object-cover" />
          <span v-else class="flex h-full w-full items-center justify-center text-gold">
            <AppIcon name="briefcase" :size="40" />
          </span>
        </span>
        <div>
          <div class="flex flex-wrap items-center gap-2">
            <h1 class="text-2xl font-bold text-ink">{{ business.name }}</h1>
            <span v-if="business.is_mama_tribu" class="badge bg-gold-light text-gold">Mamá Tribu</span>
            <span v-if="business.tribe_recommended" class="badge bg-gold-light text-gold">Recomendado por la tribu</span>
          </div>
          <p class="text-sm text-muted">{{ business.category.name }}</p>
          <div class="mt-2 flex flex-wrap items-center gap-3 text-sm text-muted">
            <span class="inline-flex items-center gap-1"><AppIcon name="location" :size="14" />{{ business.city }}</span>
            <span v-if="business.home_delivery" class="inline-flex items-center gap-1"><AppIcon name="check-circle" :size="14" />Domicilio</span>
            <a v-if="business.instagram" :href="`https://instagram.com/${business.instagram.replace('@','')}`" target="_blank" class="inline-flex items-center gap-1 hover:text-gold">
              <AppIcon name="instagram" :size="14" />@{{ business.instagram.replace('@','') }}
            </a>
            <a v-if="business.whatsapp" :href="`https://wa.me/${business.whatsapp.replace(/\\D/g,'')}`" target="_blank" class="inline-flex items-center gap-1 text-emerald-600 hover:underline">
              <AppIcon name="whatsapp" :size="14" />{{ business.whatsapp }}
            </a>
          </div>
        </div>
      </div>
      <div class="flex shrink-0 gap-2">
        <button class="btn-ghost" @click="toggleFavorite">
          <AppIcon :name="isFavorite ? 'heart-filled' : 'heart'" :size="16" :class="isFavorite && 'text-gold'" /> Guardar
        </button>
        <button class="btn-ghost" @click="shareBusiness">
          <AppIcon name="share" :size="16" /> Compartir
        </button>
      </div>
    </div>

    <div v-if="business.images?.length" class="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
      <img
        v-for="image in business.images.slice(0, 4)"
        :key="image.id"
        :src="image.image"
        class="aspect-square w-full rounded-xl2 object-cover"
      />
    </div>

    <div class="mt-8 flex gap-6 overflow-x-auto border-b border-line text-sm font-medium">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="whitespace-nowrap border-b-2 px-1 pb-3 transition"
        :class="activeTab === tab.key ? 'border-gold text-gold' : 'border-transparent text-muted hover:text-ink'"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="mt-6 grid gap-8 lg:grid-cols-3">
      <div class="lg:col-span-2">
        <div v-if="activeTab === 'inicio'">
          <h2 class="font-semibold text-ink">Sobre el emprendimiento</h2>
          <p class="mt-2 whitespace-pre-line text-sm text-muted">{{ business.description || "Este emprendimiento aún no agregó una descripción." }}</p>

          <div v-if="business.tribe_benefit" class="mt-6 rounded-xl2 border border-gold/30 bg-gold-light/40 p-4">
            <p class="flex items-center gap-2 text-sm font-semibold text-gold-dark">
              <AppIcon name="heart-filled" :size="16" />
              Beneficio Tribu: {{ BENEFIT_LABELS[business.benefit_type] || "Beneficio especial" }}
            </p>
            <p v-if="business.benefit_detail" class="mt-1 text-sm text-ink">{{ business.benefit_detail }}</p>
          </div>
        </div>

        <div v-else-if="activeTab === 'sobre'">
          <h2 class="font-semibold text-ink">Sobre mí</h2>
          <p class="mt-2 whitespace-pre-line text-sm text-muted">{{ business.description || "Sin información adicional." }}</p>
          <dl class="mt-4 space-y-2 text-sm">
            <div v-if="business.address" class="flex gap-2"><dt class="w-32 shrink-0 text-muted">Dirección</dt><dd class="text-ink">{{ business.address }}</dd></div>
            <div v-if="business.department" class="flex gap-2"><dt class="w-32 shrink-0 text-muted">Departamento</dt><dd class="text-ink">{{ business.department }}</dd></div>
            <div v-if="business.opening_hours" class="flex gap-2"><dt class="w-32 shrink-0 text-muted">Horario</dt><dd class="text-ink">{{ business.opening_hours }}</dd></div>
            <div class="flex gap-2"><dt class="w-32 shrink-0 text-muted">Domicilio</dt><dd class="text-ink">{{ business.home_delivery ? "Sí" : "No" }}</dd></div>
            <div v-if="business.responsible_name" class="flex gap-2"><dt class="w-32 shrink-0 text-muted">Responsable</dt><dd class="text-ink">{{ business.responsible_name }}</dd></div>
            <div v-if="business.website" class="flex gap-2"><dt class="w-32 shrink-0 text-muted">Web</dt><dd><a :href="business.website" target="_blank" class="text-gold hover:underline">{{ business.website }}</a></dd></div>
          </dl>
        </div>

        <div v-else-if="activeTab === 'opiniones'">
          <div class="flex items-center justify-between">
            <h2 class="font-semibold text-ink">Opiniones</h2>
            <StarRating :rating="business.average_rating" />
          </div>

          <div v-if="authStore.isAuthenticated" class="mt-4 card p-4">
            <p class="text-sm font-medium text-ink">Deja tu opinión</p>
            <StarRatingInput v-model="newRating" class="mt-2" />
            <textarea v-model="newComment" rows="2" class="field mt-2" placeholder="Cuéntanos tu experiencia..." />
            <p v-if="reviewError" class="mt-1 text-xs text-rose-500">{{ reviewError }}</p>
            <button class="btn-primary mt-2" :disabled="submittingReview" @click="submitReview">Publicar opinión</button>
          </div>

          <div class="mt-4">
            <ReviewItem v-for="review in reviews" :key="review.id" :review="review" />
            <p v-if="!reviews.length" class="py-6 text-sm text-muted">Aún no hay opiniones para este emprendimiento.</p>
          </div>
        </div>

        <div v-else-if="activeTab === 'preguntas'">
          <div class="flex items-center justify-between">
            <h2 class="font-semibold text-ink">Preguntas y respuestas</h2>
          </div>

          <div class="mt-4 flex gap-2">
            <input v-model="newQuestion" type="text" class="field" placeholder="Escribe tu pregunta..." />
            <button class="btn-primary shrink-0" :disabled="askingQuestion" @click="submitQuestion">Preguntar</button>
          </div>
          <p v-if="questionError" class="mt-1 text-xs text-rose-500">{{ questionError }}</p>

          <div class="mt-4">
            <QuestionItem v-for="question in questions" :key="question.id" :question="question" />
            <p v-if="!questions.length" class="py-6 text-sm text-muted">Sé la primera persona en preguntar algo.</p>
          </div>
        </div>
      </div>

      <aside class="space-y-4">
        <div class="card p-4">
          <p class="text-sm font-semibold text-ink">Contacto</p>
          <div class="mt-3 space-y-2 text-sm">
            <a v-if="business.whatsapp" :href="`https://wa.me/${business.whatsapp.replace(/\\D/g,'')}`" target="_blank" class="btn-primary w-full">
              <AppIcon name="whatsapp" :size="16" /> Enviar mensaje
            </a>
            <a v-if="business.facebook" :href="business.facebook" target="_blank" class="flex items-center gap-2 text-muted hover:text-gold">
              <AppIcon name="facebook" :size="16" /> Facebook
            </a>
            <a v-if="business.website" :href="business.website" target="_blank" class="flex items-center gap-2 text-muted hover:text-gold">
              <AppIcon name="globe" :size="16" /> Sitio web
            </a>
          </div>
        </div>
        <div class="card p-4">
          <p class="flex items-center gap-2 text-sm font-semibold text-ink">
            <AppIcon name="clock" :size="16" class="text-gold" /> Horario
          </p>
          <p class="mt-2 text-sm text-muted">{{ business.opening_hours || "No especificado" }}</p>
        </div>
      </aside>
    </div>
  </div>
</template>
