<script setup lang="ts">
import { portalService } from "~/services/portal.service";
import type { PortalFAQ } from "~/types";

definePageMeta({ layout: "portal", middleware: "portal", ownerOnly: true });

const faqs = ref<PortalFAQ[]>([]);
const form = reactive({ question: "", answer: "" });
const editing = ref<number | null>(null);
const error = ref("");
const toDelete = ref<PortalFAQ | null>(null);

const { businessId } = usePortalBusiness(load);

async function load() {
  faqs.value = (await portalService.faqs(businessId.value)).data;
}

function edit(faq: PortalFAQ) {
  editing.value = faq.id;
  form.question = faq.question;
  form.answer = faq.answer;
}

function cancel() {
  editing.value = null;
  form.question = form.answer = "";
}

async function save() {
  error.value = "";
  try {
    if (editing.value) await portalService.updateFaq(businessId.value, editing.value, { ...form });
    else await portalService.createFaq(businessId.value, { ...form });
    cancel();
    await load();
  } catch (err) {
    error.value = useErrorMessage(err);
  }
}

async function move(index: number, delta: number) {
  const ids = faqs.value.map((f) => f.id);
  const target = index + delta;
  if (target < 0 || target >= ids.length) return;
  [ids[index], ids[target]] = [ids[target], ids[index]];
  faqs.value = (await portalService.reorderFaqs(businessId.value, ids)).data;
}

async function remove() {
  if (!toDelete.value) return;
  await portalService.deleteFaq(businessId.value, toDelete.value.id);
  toDelete.value = null;
  await load();
}
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-5">
    <header>
      <h1 class="text-2xl font-bold text-ink">Preguntas frecuentes</h1>
      <p class="text-sm text-muted">Respuestas que ven las usuarias en tu página. Puedes ordenarlas, editarlas y borrarlas.</p>
    </header>

    <form class="card space-y-3 p-5" @submit.prevent="save">
      <input v-model="form.question" required maxlength="255" class="field" placeholder="Pregunta, ej. ¿Hacen envíos?" />
      <textarea v-model="form.answer" required rows="3" class="field" placeholder="Respuesta" />
      <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
      <div class="flex gap-2">
        <button class="btn-primary">{{ editing ? "Guardar cambios" : "Agregar pregunta" }}</button>
        <button v-if="editing" type="button" class="btn-ghost" @click="cancel">Cancelar</button>
      </div>
    </form>

    <EmptyState v-if="!faqs.length" icon="file-text" title="Aún no tienes preguntas frecuentes" />
    <ul class="space-y-3">
      <li v-for="(faq, index) in faqs" :key="faq.id" class="card p-4">
        <p class="font-medium text-ink">{{ faq.question }}</p>
        <p class="mt-1 whitespace-pre-line text-sm text-muted">{{ faq.answer }}</p>
        <div class="mt-2 flex items-center gap-1">
          <button class="btn-ghost !px-2 !py-1" :disabled="index === 0" aria-label="Subir" @click="move(index, -1)"><AppIcon name="arrow" :size="14" class="-rotate-90" /></button>
          <button class="btn-ghost !px-2 !py-1" :disabled="index === faqs.length - 1" aria-label="Bajar" @click="move(index, 1)"><AppIcon name="arrow" :size="14" class="rotate-90" /></button>
          <button class="btn-ghost !px-2 !py-1 text-xs" @click="edit(faq)">Editar</button>
          <button class="btn-ghost ml-auto !px-2 !py-1 text-xs !text-rose-500" @click="toDelete = faq">Eliminar</button>
        </div>
      </li>
    </ul>

    <ConfirmDialog
      :open="Boolean(toDelete)"
      title="¿Eliminar esta pregunta?"
      description="Deja de mostrarse en tu página. El cambio queda en el historial."
      confirm-label="Eliminar"
      danger
      @confirm="remove"
      @cancel="toDelete = null"
    />
  </div>
</template>
