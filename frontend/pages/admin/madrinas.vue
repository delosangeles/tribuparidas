<script setup lang="ts">
import { blogService } from "~/services/blog.service";
import { madrinaService, type Madrina, type MadrinaAccessPayload } from "~/services/madrina.service";
import { userService } from "~/services/user.service";
import type { AdminAction, AdminModule, BlogCategory, User } from "~/types";

definePageMeta({ layout: "admin", middleware: "superadmin" });

// Madrinas: usuarias (no administradoras) con acceso a módulos puntuales del panel.
// Ej.: madrina de Lecturas = puede aprobar blogs de esa categoría y eliminar sus comentarios.
const MODULES: { key: AdminModule; label: string; hint: string; icon: string }[] = [
  { key: "blog", label: "Blog", hint: "Aprobar, editar y eliminar blogs y comentarios, por categoría.", icon: "file-text" },
  { key: "usuarios", label: "Usuarios", hint: "Aprobar (activar) y editar usuarias. No toca cuentas de administradoras.", icon: "users" },
  { key: "festejos", label: "Festejos", hint: "Aprobar, agregar, editar y eliminar festejos.", icon: "gift" },
];
const ACTIONS: { key: AdminAction; label: string }[] = [
  { key: "add", label: "Agregar" },
  { key: "approve", label: "Aprobar" },
  { key: "edit", label: "Editar" },
  { key: "delete", label: "Eliminar" },
];

const madrinas = ref<Madrina[]>([]);
const categories = ref<BlogCategory[]>([]);
const loading = ref(false);
const error = ref("");

async function load() {
  loading.value = true;
  try {
    const [m, c] = await Promise.all([madrinaService.list(), blogService.categories({ is_active: true })]);
    madrinas.value = m.data;
    categories.value = c.data.results;
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}
await load();

const name = (m: { first_name: string; last_name: string; email: string }) => `${m.first_name} ${m.last_name}`.trim() || m.email;
const moduleLabel = (key: string) => MODULES.find((m) => m.key === key)?.label ?? key;

function summarize(access: Madrina["access"][number]) {
  const actions = ACTIONS.filter((a) => access[`can_${a.key}` as const]).map((a) => a.label.toLowerCase()).join(", ");
  const scope = access.module === "blog" ? (access.categories.length ? ` · ${access.categories.map((c) => c.name).join(", ")}` : " · todas las categorías") : "";
  return `${moduleLabel(access.module)}: ${actions}${scope}`;
}

// ---- editor (crear o editar)
type ModuleForm = { enabled: boolean; can_add: boolean; can_approve: boolean; can_edit: boolean; can_delete: boolean; categories: number[] };
const emptyModuleForm = (): ModuleForm => ({ enabled: false, can_add: false, can_approve: false, can_edit: false, can_delete: false, categories: [] });

const showEditor = ref(false);
const target = ref<{ id: number; label: string } | null>(null);
const form = reactive<Record<AdminModule, ModuleForm>>({ blog: emptyModuleForm(), usuarios: emptyModuleForm(), festejos: emptyModuleForm() });
const saving = ref(false);
const editorError = ref("");

const search = ref("");
const results = ref<User[]>([]);
let timer: ReturnType<typeof setTimeout> | null = null;
watch(search, (value) => {
  if (timer) clearTimeout(timer);
  if (value.trim().length < 2) {
    results.value = [];
    return;
  }
  timer = setTimeout(async () => {
    const { data } = await userService.adminList({ search: value.trim(), is_approved: true });
    // Las administradoras ya tienen acceso a todo: no se listan.
    results.value = data.results.filter((u) => !u.is_staff && !u.is_superuser);
  }, 300);
});

function resetForm(m?: Madrina) {
  for (const { key } of MODULES) {
    const access = m?.access.find((a) => a.module === key);
    form[key] = access
      ? {
          enabled: true,
          can_add: access.can_add,
          can_approve: access.can_approve,
          can_edit: access.can_edit,
          can_delete: access.can_delete,
          categories: access.categories.map((c) => c.id),
        }
      : emptyModuleForm();
  }
}

function openNew() {
  resetForm();
  target.value = null;
  search.value = "";
  results.value = [];
  editorError.value = "";
  showEditor.value = true;
}
function openEdit(m: Madrina) {
  resetForm(m);
  target.value = { id: m.id, label: name(m) };
  editorError.value = "";
  showEditor.value = true;
}
function pick(u: User) {
  target.value = { id: u.id, label: `${name(u)} (${u.email})` };
  results.value = [];
  search.value = "";
}

function toggleCategory(id: number) {
  const list = form.blog.categories;
  const index = list.indexOf(id);
  if (index === -1) list.push(id);
  else list.splice(index, 1);
}

async function save() {
  if (!target.value) {
    editorError.value = "Elige a la persona que será madrina.";
    return;
  }
  const access: MadrinaAccessPayload[] = MODULES.filter((m) => form[m.key].enabled).map((m) => ({
    module: m.key,
    can_add: form[m.key].can_add,
    can_approve: form[m.key].can_approve,
    can_edit: form[m.key].can_edit,
    can_delete: form[m.key].can_delete,
    categories: m.key === "blog" ? form.blog.categories : [],
  }));
  if (!access.length) {
    editorError.value = "Activa al menos un módulo.";
    return;
  }
  saving.value = true;
  editorError.value = "";
  try {
    await madrinaService.save(target.value.id, access);
    showEditor.value = false;
    await load();
  } catch (err) {
    editorError.value = useErrorMessage(err);
  } finally {
    saving.value = false;
  }
}

const removeTarget = ref<Madrina | null>(null);
async function confirmRemove() {
  if (!removeTarget.value) return;
  await madrinaService.remove(removeTarget.value.id);
  removeTarget.value = null;
  await load();
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-ink">Madrinas</h1>
        <p class="mt-1 max-w-2xl text-sm text-muted">
          Madrinas son usuarias con acceso a información específica del panel, sin ser administradoras. Por ejemplo, la madrina de
          «Lecturas» aprueba los blogs de esa categoría y elimina sus comentarios. Puedes darles también Usuarios o Festejos.
        </p>
      </div>
      <button class="btn-primary" @click="openNew"><AppIcon name="plus" :size="16" /> Agregar madrina</button>
    </div>

    <p v-if="error" class="mt-4 text-sm text-rose-500">{{ error }}</p>
    <LoadingSpinner v-if="loading" />
    <EmptyState
      v-else-if="!madrinas.length"
      icon="shield"
      title="Aún no hay madrinas"
      description="Agrega una usuaria y elige qué módulos y acciones puede administrar."
      class="mt-8"
    />
    <div v-else class="mt-6 grid gap-4 md:grid-cols-2">
      <article v-for="m in madrinas" :key="m.id" class="card p-5">
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-center gap-3">
            <span class="flex h-10 w-10 items-center justify-center rounded-full bg-gold-light text-gold"><AppIcon name="shield" :size="18" /></span>
            <div>
              <p class="font-semibold text-ink">{{ name(m) }}</p>
              <p class="text-xs text-muted">{{ m.email }}</p>
            </div>
          </div>
          <span v-if="!m.is_active" class="badge-rejected">Inactiva</span>
        </div>
        <ul class="mt-4 space-y-1.5 text-sm text-ink">
          <li v-for="a in m.access" :key="a.module" class="flex gap-2"><AppIcon name="check" :size="16" class="mt-0.5 shrink-0 text-emerald-500" />{{ summarize(a) }}</li>
        </ul>
        <div class="mt-4 flex gap-2">
          <button class="btn-outline !px-3 !py-1 text-xs" @click="openEdit(m)">Editar accesos</button>
          <button class="btn-outline !px-3 !py-1 text-xs text-rose-500" @click="removeTarget = m">Quitar madrina</button>
        </div>
      </article>
    </div>

    <!-- Editor -->
    <Teleport to="body">
      <div v-if="showEditor" class="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-ink/40 px-4 py-8">
        <div class="card max-h-[90vh] w-full max-w-2xl overflow-y-auto p-6">
          <p class="text-lg font-semibold text-ink">{{ target && madrinas.some((m) => m.id === target?.id) ? "Editar accesos" : "Agregar madrina" }}</p>

          <div class="mt-4">
            <label class="mb-1 block text-sm font-medium text-ink">Persona</label>
            <p v-if="target" class="flex items-center justify-between rounded-xl2 border border-line px-3 py-2 text-sm">
              {{ target.label }}
              <button v-if="!madrinas.some((m) => m.id === target?.id)" type="button" class="text-xs text-gold" @click="target = null">Cambiar</button>
            </p>
            <template v-else>
              <input v-model="search" type="text" class="field" placeholder="Busca por nombre o correo (cuenta activa)..." />
              <ul v-if="results.length" class="mt-1 max-h-40 overflow-y-auto rounded-xl2 border border-line bg-white text-sm">
                <li v-for="u in results" :key="u.id">
                  <button type="button" class="w-full px-3 py-2 text-left hover:bg-gold-light" @click="pick(u)">
                    {{ name(u) }} <span class="text-xs text-muted">{{ u.email }}</span>
                  </button>
                </li>
              </ul>
            </template>
          </div>

          <div class="mt-5 space-y-4">
            <fieldset v-for="m in MODULES" :key="m.key" class="rounded-xl2 border p-4" :class="form[m.key].enabled ? 'border-gold bg-gold-light/30' : 'border-line'">
              <label class="flex cursor-pointer items-start gap-3">
                <input v-model="form[m.key].enabled" type="checkbox" class="mt-1 h-4 w-4 rounded border-line" />
                <span>
                  <span class="flex items-center gap-2 font-semibold text-ink"><AppIcon :name="m.icon" :size="16" /> {{ m.label }}</span>
                  <span class="block text-xs text-muted">{{ m.hint }}</span>
                </span>
              </label>

              <div v-if="form[m.key].enabled" class="mt-3 pl-7">
                <p class="text-xs font-semibold uppercase tracking-wide text-muted">Puede</p>
                <div class="mt-1 flex flex-wrap gap-x-5 gap-y-1">
                  <label v-for="a in ACTIONS" :key="a.key" class="flex items-center gap-2 text-sm text-ink">
                    <input v-model="form[m.key][`can_${a.key}` as 'can_add']" type="checkbox" class="h-4 w-4 rounded border-line" /> {{ a.label }}
                  </label>
                </div>

                <template v-if="m.key === 'blog'">
                  <p class="mt-3 text-xs font-semibold uppercase tracking-wide text-muted">Categorías del blog</p>
                  <p class="text-xs text-muted">Sin marcar ninguna, aplica a todas las categorías.</p>
                  <div class="mt-1 grid gap-x-4 gap-y-1 sm:grid-cols-2">
                    <label v-for="c in categories" :key="c.id" class="flex items-center gap-2 text-sm text-ink">
                      <input type="checkbox" class="h-4 w-4 rounded border-line" :checked="form.blog.categories.includes(c.id)" @change="toggleCategory(c.id)" />
                      {{ c.name }}
                    </label>
                  </div>
                </template>
              </div>
            </fieldset>
          </div>

          <p v-if="editorError" class="mt-4 text-sm text-rose-500">{{ editorError }}</p>
          <div class="mt-6 flex justify-end gap-2">
            <button type="button" class="btn-ghost" @click="showEditor = false">Cancelar</button>
            <button type="button" class="btn-primary" :disabled="saving" @click="save">{{ saving ? "Guardando..." : "Guardar" }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Quitar -->
    <Teleport to="body">
      <div v-if="removeTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4">
        <div class="card w-full max-w-sm p-6">
          <p class="text-lg font-semibold text-ink">¿Quitar a {{ name(removeTarget) }} como madrina?</p>
          <p class="mt-1 text-sm text-muted">Pierde el acceso a todos los módulos del panel. Su cuenta y sus publicaciones no se borran.</p>
          <div class="mt-6 flex justify-end gap-2">
            <button class="btn-ghost" @click="removeTarget = null">Cancelar</button>
            <button class="btn-primary" @click="confirmRemove">Quitar</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
