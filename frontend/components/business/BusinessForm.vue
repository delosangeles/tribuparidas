<script setup lang="ts">
import type { Business, BusinessFormPayload } from "~/types";

const props = withDefaults(
  defineProps<{ initial?: Business | null; submitLabel: string; loading?: boolean; showStatus?: boolean; requireAll?: boolean }>(),
  { showStatus: false, requireAll: false }
);
const emit = defineEmits<{ (e: "submit", payload: BusinessFormPayload & { status?: string }): void }>();

const categoriesStore = useCategoriesStore();
await categoriesStore.fetchAll();

const BENEFIT_TYPES = [
  { value: "descuento", label: "Descuento" },
  { value: "envio_gratis", label: "Envío gratis" },
  { value: "promocion", label: "Promoción" },
  { value: "precio_especial", label: "Precio especial" },
  { value: "beneficio_exclusivo", label: "Beneficio exclusivo" },
  { value: "otro", label: "Otro" },
];

const STATUS_OPTIONS = [
  { value: "approved", label: "Aprobado" },
  { value: "pending", label: "Pendiente" },
  { value: "rejected", label: "Rechazado" },
];

const form = reactive({
  name: props.initial?.name || "",
  description: props.initial?.description || "",
  category: props.initial?.category?.id || (categoriesStore.items[0]?.id ?? 0),
  city: props.initial?.city || "",
  department: props.initial?.department || "",
  address: props.initial?.address || "",
  whatsapp: props.initial?.whatsapp || "",
  instagram: props.initial?.instagram || "",
  facebook: props.initial?.facebook || "",
  website: props.initial?.website || "",
  opening_hours: props.initial?.opening_hours || "",
  home_delivery: props.initial?.home_delivery ?? false,
  tribe_benefit: props.initial?.tribe_benefit ?? false,
  benefit_type: props.initial?.benefit_type || "",
  benefit_detail: props.initial?.benefit_detail || "",
  is_mama_tribu: props.initial?.is_mama_tribu ?? false,
  responsible_name: props.initial?.responsible_name || "",
  tribe_recommended: props.initial?.tribe_recommended ?? false,
  status: props.initial?.status || "approved",
});

watch(
  () => form.tribe_benefit,
  (enabled) => {
    if (!enabled) {
      form.benefit_type = "";
      form.benefit_detail = "";
    }
  }
);

const citiesForDepartment = computed(() => COLOMBIA_DEPARTMENTS.find((d) => d.name === form.department)?.cities || []);
watch(
  () => form.department,
  () => {
    if (!citiesForDepartment.value.includes(form.city)) form.city = "";
  }
);

const logoFile = ref<File | null>(null);
const logoError = ref("");

function handleSubmit() {
  if (props.requireAll && !logoFile.value && !props.initial?.logo) {
    logoError.value = "El logo es obligatorio.";
    return;
  }
  logoError.value = "";
  emit("submit", {
    ...form,
    category: Number(form.category),
    logo: logoFile.value,
  });
}
</script>

<template>
  <form class="space-y-5" @submit.prevent="handleSubmit">
    <div>
      <p class="mb-2 text-sm font-medium text-ink">Logo</p>
      <ImageUploader :model-value="initial?.logo" shape="circle" label="Logo" @select="(f) => (logoFile = f)" />
      <p v-if="logoError" class="mt-1 text-xs text-rose-500">{{ logoError }}</p>
    </div>

    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div>
        <label class="mb-1 block text-sm font-medium text-ink">Nombre del emprendimiento</label>
        <input v-model="form.name" type="text" required class="field" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-ink">Categoría</label>
        <select v-model="form.category" required class="field">
          <template v-for="c in categoriesStore.items" :key="c.id">
            <optgroup v-if="c.subcategories?.length" :label="c.name">
              <option :value="c.id">{{ c.name }} (general)</option>
              <option v-for="sub in c.subcategories" :key="sub.id" :value="sub.id">{{ sub.name }}</option>
            </optgroup>
            <option v-else :value="c.id">{{ c.name }}</option>
          </template>
        </select>
      </div>
      <div v-if="showStatus">
        <label class="mb-1 block text-sm font-medium text-ink">Estado</label>
        <select v-model="form.status" class="field">
          <option v-for="opt in STATUS_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-ink">Departamento</label>
        <select v-model="form.department" required class="field">
          <option value="" disabled>Selecciona un departamento</option>
          <option v-for="d in COLOMBIA_DEPARTMENTS" :key="d.name" :value="d.name">{{ d.name }}</option>
        </select>
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-ink">Ciudad</label>
        <select v-model="form.city" required class="field" :disabled="!form.department">
          <option value="" disabled>Selecciona una ciudad</option>
          <option v-for="c in citiesForDepartment" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-ink">Dirección</label>
        <input v-model="form.address" type="text" :required="requireAll" class="field" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-ink">WhatsApp</label>
        <input v-model="form.whatsapp" type="text" placeholder="+57 300 000 0000" :required="requireAll" class="field" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-ink">Instagram</label>
        <input v-model="form.instagram" type="text" placeholder="@usuario" :required="requireAll" class="field" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-ink">Facebook</label>
        <input v-model="form.facebook" type="text" :required="requireAll" class="field" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-ink">Sitio web{{ requireAll ? "" : " (opcional)" }}</label>
        <input v-model="form.website" type="url" placeholder="https://" :required="requireAll" class="field" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-ink">Horario de atención</label>
        <input v-model="form.opening_hours" type="text" placeholder="Lun-Sáb 9am-6pm" :required="requireAll" class="field" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-ink">¿Ofrece domicilio?</label>
        <select v-model="form.home_delivery" class="field">
          <option :value="true">Sí</option>
          <option :value="false">No</option>
        </select>
      </div>
      <div class="sm:col-span-2 lg:col-span-3">
        <label class="mb-1 block text-sm font-medium text-ink">Descripción</label>
        <textarea v-model="form.description" rows="4" :required="requireAll" class="field" placeholder="Cuéntale a la comunidad qué haces..." />
      </div>
    </div>

    <div class="rounded-xl2 border border-line p-4">
      <p class="mb-3 text-sm font-semibold text-ink">Comunidad Tribu</p>
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">¿Emprendimiento de mamá tribu?</label>
          <select v-model="form.is_mama_tribu" class="field">
            <option :value="true">Sí</option>
            <option :value="false">No</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">¿Recomendado por la tribu?</label>
          <select v-model="form.tribe_recommended" class="field">
            <option :value="true">Sí</option>
            <option :value="false">No</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Responsable</label>
          <input v-model="form.responsible_name" type="text" placeholder="Nombre de la persona de contacto" :required="requireAll" class="field" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">¿Tiene beneficio tribu?</label>
          <select v-model="form.tribe_benefit" class="field">
            <option :value="true">Sí</option>
            <option :value="false">No</option>
          </select>
        </div>
        <template v-if="form.tribe_benefit">
          <div>
            <label class="mb-1 block text-sm font-medium text-ink">Tipo de beneficio</label>
            <select v-model="form.benefit_type" required class="field">
              <option value="" disabled>Selecciona una opción</option>
              <option v-for="opt in BENEFIT_TYPES" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <div class="sm:col-span-2 lg:col-span-3">
            <label class="mb-1 block text-sm font-medium text-ink">Detalle del beneficio</label>
            <textarea v-model="form.benefit_detail" rows="2" class="field" placeholder="Ej: 10% de descuento para mamás de la tribu" />
          </div>
        </template>
      </div>
    </div>

    <button type="submit" class="btn-primary" :disabled="loading">
      {{ loading ? "Guardando..." : submitLabel }}
    </button>
  </form>
</template>
