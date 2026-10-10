<script setup lang="ts">
// Departamento, ciudad y dirección (tres columnas). Opcional.
interface LocationState {
  department: string;
  city: string;
  address: string;
}

const form = defineModel<LocationState>({ required: true });

const cities = computed(() => COLOMBIA_DEPARTMENTS.find((d) => d.name === form.value.department)?.cities || []);

watch(
  () => form.value.department,
  () => {
    if (form.value.city && !cities.value.includes(form.value.city)) form.value.city = "";
  }
);
</script>

<template>
  <div class="grid gap-3 sm:grid-cols-3">
    <div>
      <label class="mb-1 block text-sm font-medium text-ink">Departamento</label>
      <select v-model="form.department" class="field">
        <option value="">Selecciona</option>
        <option v-for="d in COLOMBIA_DEPARTMENTS" :key="d.name" :value="d.name">{{ d.name }}</option>
      </select>
    </div>
    <div>
      <label class="mb-1 block text-sm font-medium text-ink">Ciudad</label>
      <select v-model="form.city" class="field" :disabled="!form.department">
        <option value="">Selecciona</option>
        <option v-for="c in cities" :key="c" :value="c">{{ c }}</option>
      </select>
    </div>
    <div>
      <label class="mb-1 block text-sm font-medium text-ink">Dirección</label>
      <input v-model="form.address" type="text" maxlength="255" class="field" placeholder="Barrio, calle, número" />
    </div>
  </div>
</template>
