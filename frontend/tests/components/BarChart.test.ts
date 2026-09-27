import { describe, expect, it } from "vitest";
import { mountSuspended } from "@nuxt/test-utils/runtime";
import BarChart from "~/components/ui/BarChart.vue";

describe("BarChart", () => {
  it("renders horizontal items with href as real, clickable links", async () => {
    const wrapper = await mountSuspended(BarChart, {
      props: {
        orientation: "horizontal",
        items: [{ label: "/emprendimientos", value: 5, href: "/emprendimientos" }],
      },
    });

    const link = wrapper.find("a[href='/emprendimientos']");
    expect(link.exists()).toBe(true);
  });

  it("renders horizontal items without href as plain, non-link rows", async () => {
    const wrapper = await mountSuspended(BarChart, {
      props: {
        orientation: "horizontal",
        items: [{ label: "12h", value: 3 }],
      },
    });

    expect(wrapper.find("a").exists()).toBe(false);
    expect(wrapper.text()).toContain("12h");
  });
});
