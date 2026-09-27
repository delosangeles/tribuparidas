import { describe, expect, it } from "vitest";
import { mountSuspended } from "@nuxt/test-utils/runtime";
import SearchableSelect from "~/components/ui/SearchableSelect.vue";

const OPTIONS = [
  { id: 1, label: "María González (maria@example.com)" },
  { id: 2, label: "Laura Ramírez (laura@example.com)" },
];

describe("SearchableSelect", () => {
  it("shows the selected option's label by default", async () => {
    const wrapper = await mountSuspended(SearchableSelect, {
      props: { modelValue: 1, options: OPTIONS },
    });

    const input = wrapper.find("input");
    expect((input.element as HTMLInputElement).value).toBe(OPTIONS[0].label);
  });

  it("filters options as the user types and emits the picked id", async () => {
    const wrapper = await mountSuspended(SearchableSelect, {
      props: { modelValue: "", options: OPTIONS },
    });

    const input = wrapper.find("input");
    await input.trigger("focus");
    await input.setValue("laura");

    const buttons = wrapper.findAll("button");
    expect(buttons).toHaveLength(1);
    expect(buttons[0].text()).toContain("Laura");

    await buttons[0].trigger("click");
    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual([2]);
  });
});
