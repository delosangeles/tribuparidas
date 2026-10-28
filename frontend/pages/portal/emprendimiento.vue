<script setup lang="ts">
import { portalService } from "~/services/portal.service";
import type { PortalBusiness } from "~/types";

definePageMeta({ layout: "portal", middleware: "portal", ownerOnly: true });

const categories = useCategoriesStore();
await categories.fetchAll();

const business = ref<PortalBusiness | null>(null);
const form = reactive({
  name: "", description: "", category: 0, city: "", department: "", address: "", whatsapp: "",
  instagram: "", facebook: "", website: "", opening_hours: "", responsible_name: "", home_delivery: false,
});
const saving = ref(false);
const message = ref("");
const error = ref("");

usePortalBusiness(async (id) => {
  const { data } = await portalService.business(id);
  business.value = data;
  Object.assign(form, {
    name: data.name, description: data.description, category: data.category, city: data.city,
    department: data.department, address: data.address, whatsapp: data.whatsapp, instagram: data.instagram,
    facebook: data.facebook, website: data.website, opening_hours: data.opening_hours,
    responsible_name: data.responsible_name, home_delivery: data.home_delivery,
  });
});

async function save() {
  if (!business.value) return;
  saving.value = true;
  message.value = error.value = "";
  try {
    const { data } = await portalService.updateBusiness(business.value.id, { ...form });
    business.value = data;
    message.value = "Cambios guardados. Quedan registrados en el historial.";
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-5">
    <header class="flex flex-wrap items-end justify-between gap-2">
      <div>
        <h1 class="text-2xl font-bold text-ink">Mi emprendimiento</h1>
        <p class="text-sm text-muted">Edita la información que ven las usuarias en tu tarjeta.</p>
      </div>
      <NuxtLink v-if="business" :to="business.public_path" class="btn-outline">Ver página pública</NuxtLink>
    </header>

    <form v-if="business" class="card grid gap-4 p-5 sm:grid-cols-2" @submit.prevent="save">
      <label class="sm:col-span-2"><span class="text-sm font-medium text-ink">Nombre</span><input v-model="form.name" required class="field mt-1" /></label>
      <label class="sm:col-span-2"><span class="text-sm font-medium text-ink">Descripción</span><textarea v-model="form.description" rows="4" class="field mt-1" /></label>
      <label>
        <span class="text-sm font-medium text-ink">Categoría</span>
        <select v-model.number="form.category" class="field mt-1">
          <option v-for="c in categories.items" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </label>
      <label><span class="text-sm font-medium text-ink">Responsable</span><input v-model="form.responsible_name" class="field mt-1" /></label>
      <label><span class="text-sm font-medium text-ink">Departamento</span><input v-model="form.department" required class="field mt-1" /></label>
      <label><span class="text-sm font-medium text-ink">Ciudad</span><input v-model="form.city" required class="field mt-1" /></label>
      <label class="sm:col-span-2"><span class="text-sm font-medium text-ink">Dirección</span><input v-model="form.address" class="field mt-1" /></label>
      <label><span class="text-sm font-medium text-ink">WhatsApp (con +57)</span><input v-model="form.whatsapp" class="field mt-1" placeholder="+57 300 000 0000" /></label>
      <label><span class="text-sm font-medium text-ink">Horario</span><input v-model="form.opening_hours" class="field mt-1" /></label>
      <label><span class="text-sm font-medium text-ink">Instagram</span><input v-model="form.instagram" class="field mt-1" placeholder="@tuemprendimiento" /></label>
      <label><span class="text-sm font-medium text-ink">Facebook</span><input v-model="form.facebook" class="field mt-1" /></label>
      <label class="sm:col-span-2"><span class="text-sm font-medium text-ink">Sitio web</span><input v-model="form.website" type="url" class="field mt-1" placeholder="https://" /></label>
      <label class="flex items-center gap-2 sm:col-span-2"><input v-model="form.home_delivery" type="checkbox" class="h-4 w-4 accent-gold" /><span class="text-sm text-ink">Ofrezco domicilio</span></label>

      <div class="sm:col-span-2">
        <p v-if="error" class="mb-2 text-sm text-rose-500">{{ error }}</p>
        <p v-if="message" class="mb-2 text-sm text-emerald-600">{{ message }}</p>
        <button class="btn-primary" :disabled="saving">{{ saving ? "Guardando..." : "Guardar cambios" }}</button>
      </div>
    </form>
  </div>
</template>
