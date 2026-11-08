import { alimentacionService } from "~/services/alimentacion.service";

/** CRUD genérico del panel de alimentación complementaria (guías, recetas,
 *  alimentos y catálogos). El servidor vuelve a validar cada permiso. */
export function useAdminCrud<T extends { id: number; status?: string }>(kind: string) {
  const api = alimentacionService.admin;
  const items = ref<T[]>([]) as Ref<T[]>;
  const loading = ref(false);
  const error = ref("");

  async function load(params?: Record<string, string>) {
    loading.value = true;
    error.value = "";
    try {
      items.value = (await api.list<T>(kind, params)).data;
    } catch (err) {
      error.value = useErrorMessage(err);
    } finally {
      loading.value = false;
    }
  }

  /** Crea o edita y, si hay imagen nueva, la sube después (el JSON y el archivo van por separado). */
  async function save(payload: object, id?: number | null, image?: File | null): Promise<T> {
    let saved = (id ? await api.update<T>(kind, id, payload) : await api.create<T>(kind, payload)).data;
    if (image) saved = (await api.uploadImage<T>(kind, saved.id, image)).data;
    await load();
    return saved;
  }

  async function remove(id: number) {
    await api.remove(kind, id);
    await load();
  }

  async function setPublished(item: T, publish: boolean) {
    await (publish ? api.publish<T>(kind, item.id) : api.unpublish<T>(kind, item.id));
    await load();
  }

  /** Sube o baja un lugar y guarda el orden completo. */
  async function move(index: number, delta: number) {
    const target = index + delta;
    if (target < 0 || target >= items.value.length) return;
    const list = [...items.value];
    [list[index], list[target]] = [list[target], list[index]];
    items.value = list;
    await api.reorder(kind, list.map((i) => i.id));
  }

  return { items, loading, error, load, save, remove, setPublished, move };
}
