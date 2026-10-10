<script setup lang="ts">
import { authService } from "~/services/auth.service";
import type { FestejosFormState } from "~/composables/useFestejosForm";
import type { Child } from "~/types";

// Sección "Para festejar contigo": cumpleaños de la mamá, hijos (con
// agregar/quitar) y embarazo. Se usa en el registro y en la configuración.
const form = defineModel<FestejosFormState>({ required: true });
// En la edición por parte de admins el cumpleaños puede seguir vacío (por completar).
// `photos`: permite subir la foto de cada hijo/a ya guardado (solo en el perfil
// de la propia usuaria; el admin ve las fotos pero no las cambia).
const props = defineProps<{ optionalBirthDate?: boolean; photos?: boolean }>();

const photoBusy = ref<number | null>(null);
const photoError = ref("");

async function changeChildPhoto(child: Child, event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file || !child.id) return;
  photoBusy.value = child.id;
  photoError.value = "";
  try {
    const { data } = await authService.uploadChildPhoto(child.id, file);
    child.photo = data.photo;
  } catch (err) {
    photoError.value = useErrorMessage(err);
  } finally {
    photoBusy.value = null;
  }
}

async function dropChildPhoto(child: Child) {
  if (!child.id) return;
  photoBusy.value = child.id;
  photoError.value = "";
  try {
    await authService.removeChildPhoto(child.id);
    child.photo = null;
  } catch (err) {
    photoError.value = useErrorMessage(err);
  } finally {
    photoBusy.value = null;
  }
}

const today = new Date().toISOString().slice(0, 10);
const inTenMonths = new Date(Date.now() + 300 * 86400000).toISOString().slice(0, 10);

function addChild() {
  form.value.children.push({ name: "", birth_date: "" });
}

function removeChild(index: number) {
  form.value.children.splice(index, 1);
}
</script>

<template>
  <fieldset class="space-y-4 rounded-xl2 border border-line bg-vanilla/60 p-4">
    <legend class="px-2 text-sm font-semibold text-ink">Para festejar contigo</legend>
    <p class="text-xs text-muted">
      Usamos estas fechas para celebrar los cumpleaños y mesversarios de la tribu. Los festejos aprobados muestran el nombre y la edad (meses o años) a toda la tribu; la fecha de nacimiento solo la ves tú y el equipo admin.
    </p>

    <div>
      <label class="mb-1 block text-sm font-medium text-ink">Tu fecha de cumpleaños</label>
      <input v-model="form.birth_date" type="date" :max="today" class="field" />
    </div>

    <div class="space-y-3">
      <div class="flex items-center justify-between">
        <p class="text-sm font-medium text-ink">Tus hijos</p>
        <button type="button" class="btn-outline !px-3 !py-1 text-xs" @click="addChild">
          <AppIcon name="plus" :size="14" /> Agregar hijo/a
        </button>
      </div>

      <div v-for="(child, index) in form.children" :key="child.id ?? `new-${index}`" class="rounded-xl2 border border-line bg-white p-3">
        <div class="grid gap-3 sm:grid-cols-[1fr_auto]">
          <div class="grid gap-3 sm:grid-cols-2">
            <div>
              <label class="mb-1 block text-xs font-medium text-muted">Nombre</label>
              <input v-model="child.name" type="text" required maxlength="150" class="field" placeholder="Nombre de tu hijo/a" />
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-muted">Fecha de nacimiento</label>
              <input v-model="child.birth_date" type="date" required :max="today" class="field" />
            </div>
          </div>
          <button
            type="button"
            class="btn-ghost self-end !px-2 !py-2 text-rose-500"
            :aria-label="`Quitar a ${child.name || 'hijo/a'}`"
            @click="removeChild(index)"
          >
            <AppIcon name="trash" :size="16" />
          </button>
          <div v-if="child.photo || (photos && child.id)" class="flex items-center gap-3 sm:col-span-2">
            <UserAvatar :src="child.photo" :name="child.name" size="lg" />
            <div v-if="photos && child.id" class="flex flex-wrap items-center gap-2">
              <label class="btn-outline cursor-pointer !px-2 !py-1 text-xs" :class="photoBusy === child.id && 'pointer-events-none opacity-60'">
                {{ child.photo ? "Cambiar foto" : "Subir foto" }}
                <input type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="changeChildPhoto(child, $event)" />
              </label>
              <button v-if="child.photo" type="button" class="btn-ghost !px-2 !py-1 text-xs text-rose-500" @click="dropChildPhoto(child)">Quitar</button>
              <span class="text-xs text-muted">Se verá en sus festejos.</span>
            </div>
          </div>
        </div>
      </div>
      <p v-if="photoError" class="text-xs text-rose-500">{{ photoError }}</p>
      <p v-if="!form.children.length" class="text-xs text-muted">Aún no agregas hijos. Si estás embarazada, marca la casilla de abajo.</p>
    </div>

    <div>
      <label class="flex items-center gap-2 text-sm text-ink">
        <input v-model="form.pregnant" type="checkbox" class="h-4 w-4 rounded border-line" />
        Estoy embarazada
      </label>
      <div v-if="form.pregnant" class="mt-2">
        <label class="mb-1 block text-xs font-medium text-muted">Fecha probable de parto</label>
        <input v-model="form.due_date" type="date" required :min="today" :max="inTenMonths" class="field sm:max-w-xs" />
      </div>
    </div>
  </fieldset>
</template>
