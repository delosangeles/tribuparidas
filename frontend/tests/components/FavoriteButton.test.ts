import { beforeEach, describe, expect, it, vi } from "vitest";
import { mountSuspended, mockNuxtImport } from "@nuxt/test-utils/runtime";
import FavoriteButton from "~/components/alimentacion/FavoriteButton.vue";
import { alimentacionService } from "~/services/alimentacion.service";

vi.mock("~/services/alimentacion.service", () => ({
  alimentacionService: {
    addFavorite: vi.fn(async () => ({})),
    removeFavorite: vi.fn(async () => ({})),
  },
}));

const { navigateToMock, authState } = vi.hoisted(() => ({
  navigateToMock: vi.fn(),
  authState: { isAuthenticated: true },
}));

mockNuxtImport("navigateTo", () => navigateToMock);
mockNuxtImport("useAuthStore", () => () => authState);

describe("FavoriteButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authState.isAuthenticated = true;
  });

  it("sin sesión lleva al login y no guarda nada", async () => {
    authState.isAuthenticated = false;
    const wrapper = await mountSuspended(FavoriteButton, { props: { slug: "pure", modelValue: false } });
    await wrapper.find("button").trigger("click");
    expect(navigateToMock).toHaveBeenCalled();
    expect(alimentacionService.addFavorite).not.toHaveBeenCalled();
    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
  });

  it("con sesión guarda la receta como favorita", async () => {
    const wrapper = await mountSuspended(FavoriteButton, { props: { slug: "pure", modelValue: false } });
    await wrapper.find("button").trigger("click");
    await vi.waitFor(() => expect(alimentacionService.addFavorite).toHaveBeenCalledWith("pure"));
    expect(wrapper.emitted("update:modelValue")![0]).toEqual([true]);
  });

  it("si ya era favorita la quita", async () => {
    const wrapper = await mountSuspended(FavoriteButton, { props: { slug: "pure", modelValue: true } });
    await wrapper.find("button").trigger("click");
    await vi.waitFor(() => expect(alimentacionService.removeFavorite).toHaveBeenCalledWith("pure"));
    expect(wrapper.emitted("update:modelValue")![0]).toEqual([false]);
  });

  it("si el servidor falla revierte el corazón", async () => {
    vi.mocked(alimentacionService.addFavorite).mockRejectedValueOnce(new Error("boom"));
    const wrapper = await mountSuspended(FavoriteButton, { props: { slug: "pure", modelValue: false } });
    await wrapper.find("button").trigger("click");
    await vi.waitFor(() => expect(wrapper.emitted("update:modelValue")).toHaveLength(2));
    expect(wrapper.emitted("update:modelValue")).toEqual([[true], [false]]);
  });
});
