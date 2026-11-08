<script setup lang="ts">
import { alimentacionService } from "~/services/alimentacion.service";
import type { CatalogItem } from "~/types/alimentacion";

const emit = defineEmits<{ (e: "changed"): void }>();

const authStore = useAuthStore();
const canAdd = computed(() => authStore.can("alimentacion", "add"));
const canEdit = computed(() => authStore.can("alimentacion", "edit"));
const canDelete = computed(() => authStore.can("alimentacion", "delete"));

const SECTIONS = [
  { kind: "edades", title: "Edades", hint: "Rangos de edad recomendada (ej. 6-8 meses)." },
  { kind: "tipos", title: "Tipos de comida", hint: "Puré, trozos/BLW, desayuno, almuerzo, snack…" },
  { kind: "alergenos", title: "Alérgenos", hint: "Los que se etiquetan en recetas y alimentos." },
];

const data = reactive<Record<string, CatalogItem[]>>({ edades: [], tipos: [], alergenos: [] });
const newName = reactive<Record<string, string>>({ edades: "", tipos: "", alergenos: "" });
const error = ref("");

async function load() {
  for (const { kind } of SECTIONS) data[kind] = (await alimentacionService.admin.list<CatalogItem>(kind)).data;
}
await load();

async function run(fn: () => Promise<unknown>) {
  error.value = "";
  try {
    await fn();
    await load();
    emit("changed");
  } catch (err) {
    error.value = useErrorMessage(err);
  }
}
const add = (kind: string) => run(async () => {
  const name = newName[kind].trim();
  if (!name) return;
  await alimentacionService.admin.create(kind, { name, order: data[kind].length });
  newName[kind] = "";
});
const rename = (kind: string, item: CatalogItem, name: string) => {
  if (name.trim() && name !== item.name) run(() => alimentacionService.admin.update(kind, item.id, { name: name.trim() }));
};
const toggle = (kind: string, item: CatalogItem) => run(() => alimentacionService.admin.update(kind, item.id, { is_active: !item.is_active }));
const remove = (kind: string, item: CatalogItem) => run(() => alimentacionService.admin.remove(kind, item.id));
async function move(kind: string, index: number, delta: number) {
  const list = [...data[kind]];
  const target = index + delta;
  if (target < 0 || target >= list.length) return;
  [list[index], list[target]] = [list[target], list[index]];
  data[kind] = list;
  await run(() => alimentacionService.admin.reorder(kind, list.map((i) => i.id)));
}
</script>

<template>
  <div class="space-y-6">
    <p v-if="error" class="rounded-xl2 bg-rose-50 px-3 py-2 text-sm text-rose-600">{{ error }}</p>
    <section v-for="s in SECTIONS" :key="s.kind" class="card space-y-3 p-5">
      <div>
        <h3 class="font-display text-lg text-ink">{{ s.title }}</h3>
        <p class="text-xs text-muted">{{ s.hint }}</p>
      </div>
      <ul class="space-y-2">
        <li v-for="(item, index) in data[s.kind]" :key="item.id" class="flex flex-wrap items-center gap-2">
          <input
            :value="item.name" class="input !w-56" :disabled="!canEdit" :aria-label="`Nombre: ${item.name}`"
            @change="rename(s.kind, item, ($event.target as HTMLInputElement).value)"
          />
          <span v-if="!item.is_active" class="badge-pending">Inactivo</span>
          <template v-if="canEdit">
            <button type="button" class="btn-ghost !px-2" :disabled="index === 0" aria-label="Subir" @click="move(s.kind, index, -1)">↑</button>
            <button type="button" class="btn-ghost !px-2" :disabled="index === data[s.kind].length - 1" aria-label="Bajar" @click="move(s.kind, index, 1)">↓</button>
            <button type="button" class="btn-ghost !px-3" @click="toggle(s.kind, item)">{{ item.is_active ? "Desactivar" : "Activar" }}</button>
          </template>
          <button v-if="canDelete" type="button" class="btn-ghost !px-3 !text-rose-500" @click="remove(s.kind, item)">Eliminar</button>
        </li>
      </ul>
      <form v-if="canAdd" class="flex gap-2" @submit.prevent="add(s.kind)">
        <input v-model="newName[s.kind]" class="input !w-56" :placeholder="`Nuevo en ${s.title.toLowerCase()}`" maxlength="100" />
        <button class="btn-outline">Agregar</button>
      </form>
    </section>
  </div>
</template>
