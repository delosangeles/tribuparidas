<script setup lang="ts">
import { festejosService, type FestejosScope } from "~/services/festejos.service";
import { userService } from "~/services/user.service";
import type { Festejo, User } from "~/types";

definePageMeta({ layout: "admin", middleware: "admin", module: "festejos" });

const authStore = useAuthStore();

// ---- período (lunes a domingo / mes completo)
function toIso(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function parseIso(iso: string) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}
const fmt = (iso: string, opts: Intl.DateTimeFormatOptions) => new Intl.DateTimeFormat("es-CO", opts).format(parseIso(iso));

const scope = ref<FestejosScope>("week");
const refDate = ref(toIso(new Date()));
const statusFilter = ref<"" | "pending" | "approved">("");
const kindFilter = ref("");

function shift(delta: number) {
  const d = parseIso(refDate.value);
  if (scope.value === "week") d.setDate(d.getDate() + delta * 7);
  else d.setMonth(d.getMonth() + delta, 1);
  refDate.value = toIso(d);
}

const range = ref({ start: "", end: "" });
const items = ref<Festejo[]>([]);
const loading = ref(false);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const { data } = await festejosService.list({ scope: scope.value, date: refDate.value, kind: kindFilter.value });
    range.value = { start: data.start, end: data.end };
    items.value = data.results;
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}
await load();
watch([scope, refDate, kindFilter], load);

const rangeLabel = computed(() => {
  if (!range.value.start) return "";
  return scope.value === "month"
    ? fmt(range.value.start, { month: "long", year: "numeric" })
    : `Del lunes ${fmt(range.value.start, { day: "numeric", month: "long" })} al domingo ${fmt(range.value.end, { day: "numeric", month: "long" })}`;
});

const shown = computed(() => items.value.filter((f) => !statusFilter.value || f.status === statusFilter.value));
const pendingCount = computed(() => items.value.filter((f) => f.status === "pending").length);

const KIND_LABELS: Record<string, string> = {
  monthiversary: "Mesversario",
  child_birthday: "Cumpleaños de hijo/a",
  mother_birthday: "Cumpleaños de mamá",
  manual: "Manual",
};

// ---- acciones
async function approve(f: Festejo) {
  await festejosService.approve(f.id);
  await load();
}
async function approveAll() {
  await festejosService.approveAll(scope.value, refDate.value);
  await load();
}

const removeTarget = ref<Festejo | null>(null);
async function confirmRemove() {
  if (!removeTarget.value) return;
  await festejosService.remove(removeTarget.value.id);
  removeTarget.value = null;
  await load();
}

const editTarget = ref<Festejo | null>(null);
const editForm = reactive({ title: "", event_date: "", note: "" });
const editImage = ref<File | null>(null);
const editError = ref("");
function openEdit(f: Festejo) {
  editTarget.value = f;
  Object.assign(editForm, { title: f.title, event_date: f.event_date, note: f.note });
  editImage.value = null;
  editError.value = "";
}
async function submitEdit() {
  if (!editTarget.value) return;
  try {
    await festejosService.update(editTarget.value.id, { ...editForm, image: editImage.value });
    editTarget.value = null;
    await load();
  } catch (err) {
    editError.value = useErrorMessage(err);
  }
}

// Agregar festejo manual: se busca a la mamá por nombre o correo.
const showAdd = ref(false);
const addForm = reactive({ title: "", event_date: toIso(new Date()), note: "", childId: "" as string | number });
const addImage = ref<File | null>(null);
const addSearch = ref("");
const addResults = ref<User[]>([]);
const addUser = ref<User | null>(null);
const addError = ref("");
const addLoading = ref(false);

function openAdd() {
  Object.assign(addForm, { title: "", event_date: refDate.value, note: "", childId: "" });
  addImage.value = null;
  addSearch.value = "";
  addResults.value = [];
  addUser.value = null;
  addError.value = "";
  showAdd.value = true;
}
let searchTimer: ReturnType<typeof setTimeout> | null = null;
watch(addSearch, (value) => {
  if (searchTimer) clearTimeout(searchTimer);
  if (value.trim().length < 2) {
    addResults.value = [];
    return;
  }
  searchTimer = setTimeout(async () => {
    const { data } = await userService.adminList({ search: value.trim(), is_active: true });
    addResults.value = data.results;
  }, 300);
});
async function submitAdd() {
  if (!addUser.value) {
    addError.value = "Elige a la mamá del festejo.";
    return;
  }
  addLoading.value = true;
  addError.value = "";
  try {
    await festejosService.create({
      user: addUser.value.id,
      child: addForm.childId ? Number(addForm.childId) : null,
      event_date: addForm.event_date,
      title: addForm.title,
      note: addForm.note,
      image: addImage.value,
    });
    showAdd.value = false;
    await load();
  } catch (err) {
    addError.value = useErrorMessage(err);
  } finally {
    addLoading.value = false;
  }
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-ink">Festejos</h1>
        <p class="mt-1 text-sm text-muted">
          Aprueba, edita, elimina o agrega festejos. Las usuarias solo ven los aprobados en
          <NuxtLink to="/festejos" class="text-gold underline">la página de festejos</NuxtLink>.
        </p>
      </div>
      <button v-if="authStore.can('festejos', 'add')" class="btn-primary" @click="openAdd"><AppIcon name="plus" :size="16" /> Agregar festejo</button>
    </div>

    <!-- Período y filtros -->
    <div class="mt-5 flex flex-wrap items-center gap-3">
      <div class="flex gap-2">
        <button class="btn-outline !px-3 !py-1 text-xs" :class="scope === 'week' && '!border-gold !text-gold'" @click="scope = 'week'">Semana</button>
        <button class="btn-outline !px-3 !py-1 text-xs" :class="scope === 'month' && '!border-gold !text-gold'" @click="scope = 'month'">Mes</button>
      </div>
      <div class="flex items-center gap-2">
        <button class="btn-outline !px-2 !py-1" aria-label="Anterior" @click="shift(-1)"><AppIcon name="chevron" :size="16" class="rotate-180" /></button>
        <p class="min-w-[14rem] text-center text-sm font-semibold capitalize text-gold-dark">{{ rangeLabel }}</p>
        <button class="btn-outline !px-2 !py-1" aria-label="Siguiente" @click="shift(1)"><AppIcon name="chevron" :size="16" /></button>
        <button class="btn-ghost text-xs" @click="refDate = toIso(new Date())">Hoy</button>
      </div>
      <select v-model="kindFilter" class="field sm:w-52" aria-label="Tipo de festejo">
        <option value="">Todos los tipos</option>
        <option value="monthiversary">Mesversarios</option>
        <option value="child_birthday">Cumpleaños de hijos</option>
        <option value="mother_birthday">Cumpleaños de mamás</option>
        <option value="manual">Manuales</option>
      </select>
    </div>

    <div class="mt-3 flex flex-wrap items-center gap-2">
      <button class="btn-outline !px-3 !py-1 text-xs" :class="statusFilter === '' && '!border-gold !text-gold'" @click="statusFilter = ''">Todos ({{ items.length }})</button>
      <button class="btn-outline !px-3 !py-1 text-xs" :class="statusFilter === 'pending' && '!border-gold !text-gold'" @click="statusFilter = 'pending'">Pendientes ({{ pendingCount }})</button>
      <button class="btn-outline !px-3 !py-1 text-xs" :class="statusFilter === 'approved' && '!border-gold !text-gold'" @click="statusFilter = 'approved'">Aprobados ({{ items.length - pendingCount }})</button>
      <button v-if="pendingCount && authStore.can('festejos', 'approve')" class="btn-primary ml-auto !px-3 !py-1 text-xs" @click="approveAll">
        Aprobar {{ pendingCount }} pendiente{{ pendingCount === 1 ? "" : "s" }}
      </button>
    </div>

    <p v-if="error" class="mt-4 text-sm text-rose-500">{{ error }}</p>
    <LoadingSpinner v-if="loading" />
    <div v-else class="mt-4 overflow-x-auto rounded-xl2 border border-line bg-white">
      <table class="w-full text-left text-sm">
        <thead class="border-b border-line text-xs uppercase text-muted">
          <tr>
            <th class="px-4 py-3">Festejo</th>
            <th class="px-4 py-3">Fecha</th>
            <th class="px-4 py-3">Tipo</th>
            <th class="px-4 py-3">Estado</th>
            <th class="px-4 py-3">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-line">
          <tr v-for="f in shown" :key="f.id">
            <td class="px-4 py-3">
              <div class="flex items-center gap-3">
                <img v-if="f.photo" :src="f.photo" :alt="f.headline" class="h-10 w-10 shrink-0 rounded-full object-cover" />
                <span v-else class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gold-light text-gold"><AppIcon name="gift" :size="18" /></span>
                <div>
                  <p class="font-medium text-ink">{{ f.headline }}</p>
                  <p class="text-xs text-muted">Mamá: {{ f.mother_name }}</p>
                </div>
              </div>
            </td>
            <td class="px-4 py-3 capitalize text-muted">{{ fmt(f.event_date, { weekday: "short", day: "numeric", month: "short" }) }}</td>
            <td class="px-4 py-3 text-muted">{{ KIND_LABELS[f.kind] }}</td>
            <td class="px-4 py-3">
              <span :class="f.status === 'approved' ? 'badge-approved' : 'badge-pending'">{{ f.status === "approved" ? "Aprobado" : "Pendiente" }}</span>
            </td>
            <td class="px-4 py-3">
              <div class="flex flex-wrap gap-2">
                <button v-if="f.status === 'pending' && authStore.can('festejos', 'approve')" class="btn-outline !px-2 !py-1 text-xs" @click="approve(f)">Aprobar</button>
                <button v-if="authStore.can('festejos', 'edit')" class="btn-outline !px-2 !py-1 text-xs" @click="openEdit(f)">Editar</button>
                <button v-if="authStore.can('festejos', 'delete')" class="btn-outline !px-2 !py-1 text-xs text-rose-500" @click="removeTarget = f">Eliminar</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!shown.length" class="py-8 text-center text-sm text-muted">No hay festejos en este período con ese filtro.</p>
    </div>

    <!-- Confirmar eliminación -->
    <Teleport to="body">
      <div v-if="removeTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4">
        <div class="card w-full max-w-sm p-6">
          <p class="text-lg font-semibold text-ink">¿Eliminar este festejo?</p>
          <p class="mt-1 text-sm text-muted">{{ removeTarget.headline }}. Si es automático, volverá a generarse al consultar el período.</p>
          <div class="mt-6 flex justify-end gap-2">
            <button class="btn-ghost" @click="removeTarget = null">Cancelar</button>
            <button class="btn-primary" @click="confirmRemove">Eliminar</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Editar -->
    <Teleport to="body">
      <div v-if="editTarget" class="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-ink/40 px-4 py-8">
        <div class="card w-full max-w-sm p-6">
          <p class="text-lg font-semibold text-ink">Editar festejo</p>
          <form class="mt-4 space-y-3" @submit.prevent="submitEdit">
            <div>
              <label class="mb-1 block text-sm font-medium text-ink">Título</label>
              <input v-model="editForm.title" type="text" class="field" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-ink">Fecha</label>
              <input v-model="editForm.event_date" type="date" required class="field" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-ink">Nota</label>
              <textarea v-model="editForm.note" rows="2" class="field"></textarea>
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-ink">Imagen del festejo</label>
              <ImageUploader :model-value="editTarget.photo" label="Cambiar imagen" @select="editImage = $event" />
            </div>
            <p v-if="editError" class="text-sm text-rose-500">{{ editError }}</p>
            <div class="flex justify-end gap-2 pt-2">
              <button type="button" class="btn-ghost" @click="editTarget = null">Cancelar</button>
              <button type="submit" class="btn-primary">Guardar</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Agregar festejo manual -->
    <Teleport to="body">
      <div v-if="showAdd" class="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-ink/40 px-4 py-8">
        <div class="card max-h-[90vh] w-full max-w-md overflow-y-auto p-6">
          <p class="text-lg font-semibold text-ink">Agregar festejo</p>
          <form class="mt-4 space-y-3" @submit.prevent="submitAdd">
            <div>
              <label class="mb-1 block text-sm font-medium text-ink">Mamá</label>
              <p v-if="addUser" class="flex items-center justify-between rounded-xl2 border border-line px-3 py-2 text-sm">
                {{ addUser.first_name }} {{ addUser.last_name }}
                <button type="button" class="text-xs text-gold" @click="addUser = null; addForm.childId = ''">Cambiar</button>
              </p>
              <template v-else>
                <input v-model="addSearch" type="text" class="field" placeholder="Busca por nombre o correo..." />
                <ul v-if="addResults.length" class="mt-1 max-h-40 overflow-y-auto rounded-xl2 border border-line bg-white text-sm">
                  <li v-for="u in addResults" :key="u.id">
                    <button type="button" class="w-full px-3 py-2 text-left hover:bg-gold-light" @click="addUser = u; addResults = []">
                      {{ u.first_name }} {{ u.last_name }} <span class="text-xs text-muted">{{ u.email }}</span>
                    </button>
                  </li>
                </ul>
              </template>
            </div>
            <div v-if="addUser?.children?.length">
              <label class="mb-1 block text-sm font-medium text-ink">Hijo/a (opcional)</label>
              <select v-model="addForm.childId" class="field">
                <option value="">Ninguno</option>
                <option v-for="c in addUser.children" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-ink">Título</label>
              <input v-model="addForm.title" type="text" required maxlength="200" class="field" placeholder="Ej: Baby shower de Ana" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-ink">Fecha</label>
              <input v-model="addForm.event_date" type="date" required class="field" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-ink">Nota (opcional)</label>
              <textarea v-model="addForm.note" rows="2" class="field"></textarea>
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-ink">Imagen (opcional)</label>
              <ImageUploader label="Subir imagen" shape="wide" @select="addImage = $event" />
              <p class="mt-1 text-xs text-muted">Si no subes una, se usa la foto del hijo/a o de la mamá.</p>
            </div>
            <p v-if="addError" class="text-sm text-rose-500">{{ addError }}</p>
            <div class="flex justify-end gap-2 pt-2">
              <button type="button" class="btn-ghost" @click="showAdd = false">Cancelar</button>
              <button type="submit" class="btn-primary" :disabled="addLoading">{{ addLoading ? "Guardando..." : "Agregar" }}</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>
