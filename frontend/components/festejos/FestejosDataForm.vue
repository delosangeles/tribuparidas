<script setup lang="ts">
import type { FestejosFormState } from "~/composables/useFestejosForm";

// Sección "Para festejar contigo": cumpleaños de la mamá, hijos (con
// agregar/quitar) y embarazo. Se usa en el registro y en la configuración.
const form = defineModel<FestejosFormState>({ required: true });
// En la edición por parte de admins el cumpleaños puede seguir vacío (por completar).
const props = defineProps<{ optionalBirthDate?: boolean }>();

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
      <input v-model="form.birth_date" type="date" :required="!props.optionalBirthDate" :max="today" class="field" />
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
        </div>
      </div>
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
