import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useFeatureFlagStore } from "~/stores/featureFlags";
import { featureFlagService } from "~/services/feature-flag.service";

vi.mock("~/services/feature-flag.service", () => ({
  featureFlagService: {
    list: vi.fn(),
  },
}));

describe("feature flags store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("is inactive by default before loading", () => {
    const store = useFeatureFlagStore();
    expect(store.isBlogLive).toBe(false);
  });

  it("reflects an active flag after loading", async () => {
    vi.mocked(featureFlagService.list).mockResolvedValueOnce({
      data: { results: [{ key: "blog_module", label: "Blog", activate_at: null, is_forced_active: true, is_active: true, updated_at: "" }] },
    } as any);

    const store = useFeatureFlagStore();
    await store.load();

    expect(store.isBlogLive).toBe(true);
    expect(store.loaded).toBe(true);
  });

  it("never throws when the request fails (must not block login)", async () => {
    vi.mocked(featureFlagService.list).mockRejectedValueOnce(new Error("network error"));

    const store = useFeatureFlagStore();
    await expect(store.load()).resolves.toBeUndefined();
    expect(store.isBlogLive).toBe(false);
    expect(store.loaded).toBe(true);
  });
});
