<script setup lang="ts">
import { festejosService } from "~/services/festejos.service";
import { userService } from "~/services/user.service";
import type { Festejo, User } from "~/types";

const authStore = useAuthStore();
const isAdmin = computed(() => authStore.isAdmin);

type Tab = "children" | "mothers";
const tab = ref<Tab>("children");

// ---- fecha de referencia (lunes a domingo). Los admins pueden moverse de semana.
function toIso(d: Date) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}
function parseIso(iso: string) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}
const refDate = ref(toIso(new Date()));

function shiftWeek(delta: number) {
  const d = parseIso(refDate.value);
  d.setDate(d.getDate() + delta * 7);
  refDate.value = toIso(d);
}

const week = ref<{ start: string; end: string; items: Festejo[] }>({ start: "", end: "", items: [] });
const month = ref<{ start: string; items: Festejo[] }>({ start: "", items: [] });
const loading = ref(false);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [w, m] = await Promise.all([
      festejosService.list({ scope: "week", date: refDate.value }),
      festejosService.list({ scope: "month", date: refDate.value }),
    ]);
    week.value = { start: w.data.start, end: w.data.end, items: w.data.results };
    month.value = { start: m.data.start, items: m.data.results };
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}
await load();
watch(refDate, load);

const childrenItems = computed(() => week.value.items.filter((f) => f.kind !== "mother_birthday"));
const mothersItems = computed(() => week.value.items.filter((f) => f.kind === "mother_birthday"));
const shown = computed(() => (tab.value === "children" ? childrenItems.value : mothersItems.value));

// Cumpleaños del mes: cumpleaños de hijos y de mamás (los mesversarios van en la semana).
const monthBirthdays = computed(() => month.value.items.filter((f) => f.kind !== "monthiversary"));

function fmt(iso: string, opts: Intl.DateTimeFormatOptions) {
  return new Intl.DateTimeFormat("es-CO", opts).format(parseIso(iso));
}
const weekLabel = computed(() =>
  week.value.start
    ? `Del lunes ${fmt(week.value.start, { day: "numeric", month: "long" })} al domingo ${fmt(week.value.end, { day: "numeric", month: "long" })}`
    : ""
);
const monthLabel = computed(() => (month.value.start ? fmt(month.value.start, { month: "long", year: "numeric" }) : ""));
const isCurrentWeek = computed(() => {
  const today = toIso(new Date());
  return today >= week.value.start && today <= week.value.end;
});

// ---- acciones de admin
const pendingCount = computed(() => week.value.items.filter((f) => f.status === "pending").length);

async function approve(f: Festejo) {
  await festejosService.approve(f.id);
  await load();
}
async function approveAll() {
  await festejosService.approveAll("week", refDate.value);
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
const editError = ref("");
function openEdit(f: Festejo) {
  editTarget.value = f;
  editForm.title = f.title;
  editForm.event_date = f.event_date;
  editForm.note = f.note;
  editError.value = "";
}
async function submitEdit() {
  if (!editTarget.value) return;
  try {
    await festejosService.update(editTarget.value.id, { ...editForm });
    editTarget.value = null;
    await load();
  } catch (err) {
    editError.value = useErrorMessage(err);
  }
}

// Agregar festejo manual: se busca a la mamá por nombre/correo.
const showAdd = ref(false);
const addForm = reactive({ title: "", event_date: refDate.value, note: "", childId: "" as string | number });
const addSearch = ref("");
const addResults = ref<User[]>([]);
const addUser = ref<User | null>(null);
const addError = ref("");

function openAdd() {
  Object.assign(addForm, { title: "", event_date: refDate.value, note: "", childId: "" });
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
  try {
    await festejosService.create({
      user: addUser.value.id,
      child: addForm.childId ? Number(addForm.childId) : null,
      event_date: addForm.event_date,
      title: addForm.title,
      note: addForm.note,
    });
    showAdd.value = false;
    await load();
  } catch (err) {
    addError.value = useErrorMessage(err);
  }
}
</script>

<template>
  <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-ink">Festejos de la tribu</h1>
        <p class="mt-1 text-sm text-muted">Mesversarios y cumpleaños de la semana. De lunes a domingo.</p>
      </div>
      <button v-if="isAdmin" class="btn-primary" @click="openAdd">
        <AppIcon name="plus" :size="16" /> Agregar festejo
      </button>
    </div>

    <!-- Semana -->
    <div class="mt-6 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <button v-if="isAdmin" class="btn-outline !px-2 !py-1" aria-label="Semana anterior" @click="shiftWeek(-1)">
          <AppIcon name="chevron" :size="16" class="rotate-90" />
        </button>
        <p class="text-sm font-semibold capitalize text-gold-dark">{{ weekLabel }}</p>
        <button v-if="isAdmin" class="btn-outline !px-2 !py-1" aria-label="Semana siguiente" @click="shiftWeek(1)">
          <AppIcon name="chevron" :size="16" class="-rotate-90" />
        </button>
        <button v-if="isAdmin && !isCurrentWeek" class="btn-ghost text-xs" @click="refDate = toIso(new Date())">Ir a esta semana</button>
      </div>
      <button v-if="isAdmin && pendingCount" class="btn-outline text-sm" @click="approveAll">
        Aprobar {{ pendingCount }} pendiente{{ pendingCount === 1 ? "" : "s" }} de la semana
      </button>
    </div>

    <!-- Tabs -->
    <div class="mt-4 flex gap-2 border-b border-line">
      <button
        class="-mb-px border-b-2 px-4 py-2 text-sm font-semibold transition"
        :class="tab === 'children' ? 'border-gold text-gold' : 'border-transparent text-muted hover:text-gold'"
        @click="tab = 'children'"
      >
        Mesversarios y cumpleaños ({{ childrenItems.length }})
      </button>
      <button
        class="-mb-px border-b-2 px-4 py-2 text-sm font-semibold transition"
        :class="tab === 'mothers' ? 'border-gold text-gold' : 'border-transparent text-muted hover:text-gold'"
        @click="tab = 'mothers'"
      >
        Mamás cumpleañeras ({{ mothersItems.length }})
      </button>
    </div>

    <p v-if="error" class="mt-4 text-sm text-rose-500">{{ error }}</p>
    <LoadingSpinner v-if="loading" />
    <template v-else>
      <div v-if="shown.length" class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <FestejoCard
          v-for="f in shown"
          :key="f.id"
          :festejo="f"
          :admin="isAdmin"
          @approve="approve"
          @edit="openEdit"
          @remove="removeTarget = $event"
        />
      </div>
      <EmptyState
        v-else
        icon="heart"
        :title="tab === 'children' ? 'Esta semana no hay mesversarios ni cumpleaños' : 'Esta semana no hay mamás cumpleañeras'"
        :description="isAdmin ? 'Si hay festejos pendientes de aprobar, aparecerán aquí con un borde amarillo.' : 'Vuelve la próxima semana.'"
        class="mt-6"
      />

      <!-- Cumpleaños del mes -->
      <section class="mt-12">
        <h2 class="text-xl font-bold capitalize text-ink">Cumpleaños de {{ monthLabel }}</h2>
        <p class="mt-1 text-sm text-muted">Todos los cumpleaños del mes, de las mamás y de sus hijos.</p>
        <div v-if="monthBirthdays.length" class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <FestejoCard
            v-for="f in monthBirthdays"
            :key="`m-${f.id}`"
            :festejo="f"
            :admin="isAdmin"
            compact
            @approve="approve"
            @edit="openEdit"
            @remove="removeTarget = $event"
          />
        </div>
        <p v-else class="mt-4 text-sm text-muted">No hay cumpleaños registrados este mes.</p>
      </section>
    </template>

    <!-- Confirmar eliminación -->
    <Teleport to="body">
      <div v-if="removeTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4">
        <div class="card w-full max-w-sm p-6">
          <p class="text-lg font-semibold text-ink">¿Eliminar este festejo?</p>
          <p class="mt-1 text-sm text-muted">{{ removeTarget.headline }}. Si es automático, volverá a generarse al consultar la semana.</p>
          <div class="mt-6 flex justify-end gap-2">
            <button class="btn-ghost" @click="removeTarget = null">Cancelar</button>
            <button class="btn-primary" @click="confirmRemove">Eliminar</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Editar -->
    <Teleport to="body">
      <div v-if="editTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4">
        <div class="card w-full max-w-sm p-6">
          <p class="text-lg font-semibold text-ink">Editar festejo</p>
          <form class="mt-4 space-y-3" @submit.prevent="submitEdit">
            <div>
              <label class="mb-1 block text-sm font-medium text-ink">Título (opcional en festejos automáticos)</label>
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
            <p v-if="editError" class="text-sm text-rose-500">{{ editError }}</p>
            <div class="flex justify-end gap-2 pt-2">
              <button type="button" class="btn-ghost" @click="editTarget = null">Cancelar</button>
              <button type="submit" class="btn-primary">Guardar</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Agregar manual -->
    <Teleport to="body">
      <div v-if="showAdd" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4">
        <div class="card w-full max-w-md p-6">
          <p class="text-lg font-semibold text-ink">Agregar festejo manual</p>
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
            <p v-if="addError" class="text-sm text-rose-500">{{ addError }}</p>
            <div class="flex justify-end gap-2 pt-2">
              <button type="button" class="btn-ghost" @click="showAdd = false">Cancelar</button>
              <button type="submit" class="btn-primary">Agregar</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>
