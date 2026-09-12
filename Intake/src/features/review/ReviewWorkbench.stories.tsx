import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, userEvent, within } from "storybook/test";
import { ReviewWorkbench } from "./ReviewWorkbench";

const meta = {
  title: "Intake/Review surface",
  component: ReviewWorkbench,
  parameters: {
    layout: "fullscreen",
    a11y: { test: "todo" },
  },
} satisfies Meta<typeof ReviewWorkbench>;

export default meta;
type Story = StoryObj<typeof meta>;

export const GridReview: Story = {};

export const GalleryReview: Story = {
  args: { initialMode: "gallery" },
};

export const SwitchToGallery: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await userEvent.click(canvas.getByRole("button", { name: "Gallery" }));
    await expect(canvas.getByTestId("gallery-frame")).toBeInTheDocument();
  },
};
