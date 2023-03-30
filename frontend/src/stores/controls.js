import { defineStore } from "pinia";
import { useEventsStore } from "./events";

export const useControlsStore = defineStore("controls", {
  id: "controls",
  state: () => ({
    x: 0,
    y: 0,
    cameraZoom: 1,
    sequenceMargin: 2,
    eventMargin: 3,
    eventWidth: 12,
    cameraOffset: { x: 0, y: 0 },
    showAggregateGaps: true,
    minimumSupport: 0,
  }),
  actions: {
    setCameraZoom(zoom) {
      this.cameraZoom = zoom;
    },

    setSequenceMargin(margin) {
      this.sequenceMargin = parseInt(margin);
    },

    setEventMargin(margin) {
      this.eventMargin = parseInt(margin);
    },

    setEventWidth(width) {
      this.eventWidth = parseInt(width);
    },

    setCameraOffset(offset) {
      this.cameraOffset = offset;
    },
    setShowAggregateGaps(value) {
      this.showAggregateGaps = value;
    },
    setMinimumSupport(value) {
      this.minimumSupport = parseFloat(value);
    },
  },
});
