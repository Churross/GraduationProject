<script setup>
import { useControlsStore } from "../stores/controls";
import { useEventsStore } from "../stores/events";
import { reactive } from "vue";

const controlsStore = useControlsStore();
const eventsStore = useEventsStore();

const state = reactive({
  eventMarginRange: { min: 0, max: 10, step: 1 },
  sequenceMarginRange: { min: 0, max: 10, step: 1 },
  eventWidthRange: { min: 6, max: 32, step: 1 },
});
function resetZoom() {
  controlsStore.setCameraZoom(1);
}
function resetPosition() {
  controlsStore.setCameraOffset({ x: 0, y: 0 });
}
function changeMinimumSupport(value) {
  controlsStore.setMinimumSupport(value)
  eventsStore.fetchEvents(controlsStore.minimumSupport)
}
</script>

<template>
  <div class="topbar">
    <div class="topbar__event-controls">
      <button @click="resetPosition" class="button--icon">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
          <path
            d="M288 82.74L297.4 73.37C309.9 60.88 330.1 60.88 342.6 73.37C355.1 85.87 355.1 106.1 342.6 118.6L278.6 182.6C266.1 195.1 245.9 195.1 233.4 182.6L169.4 118.6C156.9 106.1 156.9 85.87 169.4 73.37C181.9 60.88 202.1 60.88 214.6 73.37L223.1 82.75V32C223.1 14.33 238.3 0 255.1 0C273.7 0 288 14.33 288 32L288 82.74zM438.6 342.6C426.1 355.1 405.9 355.1 393.4 342.6L329.4 278.6C316.9 266.1 316.9 245.9 329.4 233.4L393.4 169.4C405.9 156.9 426.1 156.9 438.6 169.4C451.1 181.9 451.1 202.1 438.6 214.6L429.3 223.1H480C497.7 223.1 512 238.3 512 255.1C512 273.7 497.7 287.1 480 287.1H429.3L438.6 297.4C451.1 309.9 451.1 330.1 438.6 342.6V342.6zM288 256C288 273.7 273.7 288 256 288C238.3 288 224 273.7 224 256C224 238.3 238.3 224 256 224C273.7 224 288 238.3 288 256zM182.6 233.4C195.1 245.9 195.1 266.1 182.6 278.6L118.6 342.6C106.1 355.1 85.87 355.1 73.37 342.6C60.88 330.1 60.88 309.9 73.37 297.4L82.75 288H32C14.33 288 0 273.7 0 256C0 238.3 14.33 224 32 224H82.74L73.37 214.6C60.88 202.1 60.88 181.9 73.37 169.4C85.87 156.9 106.1 156.9 118.6 169.4L182.6 233.4zM169.4 438.6C156.9 426.1 156.9 405.9 169.4 393.4L233.4 329.4C245.9 316.9 266.1 316.9 278.6 329.4L342.6 393.4C355.1 405.9 355.1 426.1 342.6 438.6C330.1 451.1 309.9 451.1 297.4 438.6L288 429.3V480C288 497.7 273.7 512 256 512C238.3 512 224 497.7 224 480V429.3L214.6 438.6C202.1 451.1 181.9 451.1 169.4 438.6H169.4z" />
        </svg>
      </button>
      <button @click="resetZoom" class="button--icon">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
          <path
            d="M500.3 443.7l-119.7-119.7c27.22-40.41 40.65-90.9 33.46-144.7C401.8 87.79 326.8 13.32 235.2 1.723C99.01-15.51-15.51 99.01 1.724 235.2c11.6 91.64 86.08 166.7 177.6 178.9c53.8 7.189 104.3-6.236 144.7-33.46l119.7 119.7c15.62 15.62 40.95 15.62 56.57 0C515.9 484.7 515.9 459.3 500.3 443.7zM79.1 208c0-70.58 57.42-128 128-128s128 57.42 128 128c0 70.58-57.42 128-128 128S79.1 278.6 79.1 208z" />
        </svg>
      </button>
      <div>
        <div class="range-input">
          <input type="range" id="patterns" :value="controlsStore.minimumSupport" step="0.1" min="0" :max="1"
            @change="(val) => changeMinimumSupport(val.target.value)" :disabled="eventsStore.loadingSequences" />
        </div>
      </div>
      <label for="patterns">
        Minimum support:
        {{ controlsStore.minimumSupport * 100 }}%</label>
    </div>
    <div class="dropdown button">
      <span>Settings</span>
      <div class="dropdown__content dropdown__content--right">
        <div class="range-input">
          <label for="eventMargin:">Event margin:</label>
          <input type="range" id="eventMargin" :min="state.eventMarginRange.min" :max="state.eventMarginRange.max"
            :step="state.eventMarginRange.step" :value="controlsStore.eventMargin"
            @change="(val) => controlsStore.setEventMargin(val.target.value)" />
        </div>
        <div class="range-input">
          <label for="seqMargin">Sequence margin:</label>
          <input type="range" id="seqMargin" :min="state.sequenceMarginRange.min" :max="state.sequenceMarginRange.max"
            :step="state.sequenceMarginRange.step" :value="controlsStore.sequenceMargin"
            @change="(val) => controlsStore.setSequenceMargin(val.target.value)" />
        </div>
        <div class="range-input">
          <label for="eventWidth">Event width:</label>
          <input type="range" id="eventWidth" :min="state.eventWidthRange.min" :max="state.eventWidthRange.max"
            :step="state.eventWidthRange.step" :value="controlsStore.eventWidthRange"
            @change="(val) => controlsStore.setEventWidth(val.target.value)" />
        </div>
        <div>
          <label for="showGaps">Show gaps in aggregates</label>
          <input type="checkbox" name="showGaps" id="showGaps" v-model="controlsStore.showAggregateGaps" />
        </div>
      </div>
    </div>
</div>
</template>

<style lang="scss" scoped>
@use "@/assets/scss/abstracts" as *;

.topbar {
  background-color: var(--clr-ice-300);
  width: 100%;
  grid-area: topbar;
  padding: 5px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--clr-white-500);

  &__event-controls {
    display: flex;
    align-items: center;

    button {
      margin-right: 5px;
    }
  }

  .range-input {
    display: flex;
    flex-direction: column;
    white-space: nowrap;

    +.range-input {
      margin-top: 16px;
    }
  }

  .dropdown {
    color: var(--clr-black-500);
    font-size: var(--fs-300);

    span {}
  }

  .dropdown__content {
    color: var(--clr-black-500);
  }

  svg {
    width: 100%;
    height: auto;
  }

  #patterns {
    direction: rtl;
  }
}
</style>