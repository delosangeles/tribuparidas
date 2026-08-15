<script setup lang="ts">
import { productService } from "~/services/product.service";
import type { Product } from "~/types";

definePageMeta({ layout: "dashboard", middleware: "auth" });

const businessStore = useBusinessStore();
await businessStore.fetchMyBusinesses();
const business = computed(() => businessStore.primaryBusiness);

const products = ref<Product[]>([]);
const loading = ref(false);
const showForm = ref(false);
const editingProduct = ref<Product | null>(null);
const confirmDeleteId = ref<number | null>(null);

async function loadProducts() {
  if (!business.value) return;
  loading.value = true;
  try {
    const { data } = await productService.myList(business.value.id);
    products.value = Array.isArray(data) ? data : data.results;
  } finally {
    loading.value = false;
  }
}
await loadProducts();

const formLoading = ref(false);
async function handleSubmit(payload: any) {
  if (!business.value) return;
  formLoading.value = true;
  try {
    if (editingProduct.value) {
      await productService.update(editingProduct.value.id, payload);
    } else {
      await productService.create(business.value.id, payload);
    }
    showForm.value = false;
    editingProduct.value = null;
    await loadProducts();
  } finally {
    formLoading.value = false;
  }
}

function openEdit(product: Product) {
  editingProduct.value = product;
  showForm.value = true;
}

function openCreate() {
  editingProduct.value = null;
  showForm.value = true;
}

async function confirmDelete() {
  if (!confirmDeleteId.value) return;
  await productService.remove(confirmDeleteId.value);
  confirmDeleteId.value = null;
  await loadProducts();
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-ink">Productos</h1>
        <p class="mt-1 text-sm text-muted">Administra el catálogo que ven tus visitantes.</p>
      </div>
      <button v-if="business" class="btn-primary" @click="openCreate">
        <AppIcon name="plus" :size="16" /> Nuevo producto
      </button>
    </div>

    <EmptyState v-if="!business" icon="briefcase" title="Primero crea tu emprendimiento" class="mt-8">
      <NuxtLink to="/dashboard/business" class="btn-primary mt-2">Crear emprendimiento</NuxtLink>
    </EmptyState>

    <template v-else>
      <div v-if="showForm" class="card mt-6 p-6">
        <p class="mb-4 font-semibold text-ink">{{ editingProduct ? "Editar producto" : "Nuevo producto" }}</p>
        <ProductForm :initial="editingProduct" :loading="formLoading" @submit="handleSubmit" @cancel="showForm = false" />
      </div>

      <LoadingSpinner v-if="loading" />
      <div v-else-if="products.length" class="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        <div v-for="product in products" :key="product.id" class="relative">
          <ProductCard :product="product" />
          <div class="mt-2 flex gap-2">
            <button class="btn-outline flex-1 !py-1.5 text-xs" @click="openEdit(product)">
              <AppIcon name="edit" :size="14" /> Editar
            </button>
            <button class="btn-outline flex-1 !py-1.5 text-xs !text-rose-500" @click="confirmDeleteId = product.id">
              <AppIcon name="trash" :size="14" /> Borrar
            </button>
          </div>
        </div>
      </div>
      <EmptyState v-else icon="box" title="Sin productos aún" description="Agrega tu primer producto para mostrarlo en tu perfil." class="mt-6" />
    </template>

    <ConfirmDialog
      :open="confirmDeleteId !== null"
      title="¿Eliminar producto?"
      description="Esta acción no se puede deshacer."
      confirm-label="Eliminar"
      danger
      @confirm="confirmDelete"
      @cancel="confirmDeleteId = null"
    />
  </div>
</template>
