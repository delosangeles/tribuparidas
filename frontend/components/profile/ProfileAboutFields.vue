<script setup lang="ts">
import type { ProfileAboutState } from "~/composables/useProfileQuestions";

// "Cuéntanos de ti": las preguntas abiertas del formulario de inscripción.
// Todo es opcional. Las cortas van en tres columnas; las largas ocupan la fila.
const about = defineModel<ProfileAboutState>({ required: true });

const groups = PROFILE_QUESTION_GROUPS.map((group) => ({
  title: group.title,
  questions: group.questions.filter((q) => q.editable !== false),
})).filter((group) => group.questions.length);
</script>

<template>
  <div class="space-y-5">
    <p class="text-xs text-muted">
      Nos ayuda a conocerte y a conectarte con la tribu. Puedes dejarlo en blanco y completarlo después desde tu perfil.
    </p>

    <section v-for="group in groups" :key="group.title">
      <h3 class="mb-2 text-sm font-semibold text-ink">{{ group.title }}</h3>
      <div class="grid gap-3 sm:grid-cols-3">
        <div v-for="q in group.questions" :key="q.key" :class="q.long ? 'sm:col-span-3' : ''">
          <label class="mb-1 block text-xs font-medium text-muted">{{ q.label }}</label>
          <textarea v-if="q.long" v-model="about[q.key]" rows="2" maxlength="2000" class="field" />
          <input v-else v-model="about[q.key]" type="text" maxlength="255" class="field" />
        </div>
      </div>
    </section>
  </div>
</template>
