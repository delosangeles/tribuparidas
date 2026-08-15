<script setup lang="ts">
import type { BusinessStatus } from "~/types";

const props = defineProps<{ status: BusinessStatus }>();

const labels: Record<BusinessStatus, string> = {
  approved: "Aprobado",
  pending: "Pendiente",
  rejected: "Rechazado",
};

const classes: Record<BusinessStatus, string> = {
  approved: "badge-approved",
  pending: "badge-pending",
  rejected: "badge-rejected",
};
</script>

<template>
  <span :class="classes[props.status]">{{ labels[props.status] }}</span>
</template>
