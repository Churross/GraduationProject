<script setup>
import { reactive, onMounted, ref, onBeforeUpdate, computed } from "vue";
import { api } from "../api";
import { useEventsStore } from "../stores/events";
import { useControlsStore } from "../stores/controls";
import Dendrogram from "./Dendrogram.vue";

const eventTypes = ref([]);

// reactive state
const state = reactive({
  eventSearch: "",
  eventColors: [
    { value: "var(--clr-events-1)", name: "Color 1" },
    { value: "var(--clr-events-2)", name: "Color 2" },
    { value: "var(--clr-events-3)", name: "Color 3" },
    { value: "var(--clr-events-4)", name: "Color 4" },
    { value: "var(--clr-events-5)", name: "Color 5" },
    { value: "var(--clr-events-6)", name: "Color 6" },
    { value: "var(--clr-events-7)", name: "Color 7" },
    { value: "var(--clr-events-8)", name: "Color 8" },
    { value: "var(--clr-events-9)", name: "Color 9" },
    { value: "var(--clr-events-10)", name: "Color 10" },
    { value: "var(--clr-events-11)", name: "Color 11" },
    { value: "var(--clr-events-12)", name: "Color 12" },
  ],
});

const store = useEventsStore();
const controlsStore = useControlsStore()

const filteredEvents = computed(() => {
  if (state.eventSearch.length > 0) {
    return [...store.eventTypes].filter(([key, value]) =>
      key.toLowerCase().includes(state.eventSearch.toLowerCase())
    );
  } else {
    return store.eventTypes;
  }
});

async function openEventValues(event) {
  return
  // Disable collapsing event details
  if (store.eventTypes.get(event).values.size === 0) {
    await store.fetchEventType(event);
  }

  // Toggle panel
  const panel = eventTypes.value[event].nextElementSibling;
  if (panel.style.maxHeight) {
    panel.style.maxHeight = null;
  } else {
    panel.style.maxHeight = panel.scrollHeight + "px";
  }
}


function updateLevel() {
  store.setLevel(state.level);
  store.fetchEvents(controlsStore.minimumSupport);
}

function resetColors() {
  [...store.eventTypes.keys()].forEach((key) => {
    const values = store.eventTypes.get(key)
    values.color = "var(--clr-events-12)"
    store.eventTypes.set(key, values)
  })
  return;
}

function defaultColors() {
  let color = 1;
  for (let key of [...store.eventTypes.keys()]) {
    const values = store.eventTypes.get(key)
    values.color = `var(--clr-events-${color})`
    if (color < 12) {
      color++;
    }
    store.eventTypes.set(key, values)
  }

}

onMounted(() => {

  store.fetchEventTypes();
});

onBeforeUpdate(() => {
  eventTypes.value = [];
});
</script>

<template>
  <div class="controls">
    <h1>Conventi</h1>
    <div class="controls__tree">
      <Dendrogram />
    </div>
    <!-- <div class="controls__level"></div> -->
    <!-- <div class="controls__level">
            <input type="range" min="-1" :max="state.maxLevel" step="0.1" v-model="state.level" @mouseup="updateLevel()"
              :disabled="store.loadingSequences" />
            <div class="controls__form-field">
              <label for="levelInput">Selected level</label>
              <input class="controls__level-input" type="number" id="levelInput" min="0" :max="state.maxLevel" step="0.1"
                v-model="state.level" :disabled="store.eventTypes.size === 0 || store.loadingSequences"
                @change="updateLevel()" />
            </div>
          </div> -->
    <div class="controls__event-types">
      <div class="controls__heading">
        <h3>Events</h3>
        <div class="controls__buttons">
          <button @click="resetColors()">Mono</button>
          <button @click="defaultColors()">Default</button>
        </div>
      </div>
      <input type="text" v-model="state.eventSearch" placeholder="Filter event types" class="controls__search" />
      <ul>
        <li v-for="[key, eventType] in filteredEvents" :key="key">
          <div class="controls__color-item" :ref="(el) => (eventTypes[key] = el)" @click="openEventValues(key)">
            {{ key }} ({{ eventType.eventDetails.code }})
            <div class="controls__general-color">
              <svg viewbox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" :style="`fill: ${eventType.color}`">
                <rect x="0" y="0" width="100%" height="100%" rx="4" />
              </svg>
              <select name="EventColor" v-model="eventType.color">
                <option :value="color.value" v-for="(color, index) in state.eventColors" :key="index">
                  {{ color.name }}
                </option>
              </select>
            </div>
          </div>
          <div class="controls__color-item-panel">
            Event details
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<style lang="scss" scoped>
@use "@/assets/scss/abstracts" as *;

.controls {
  background-color: var(--clr-ice-300);
  color: var(--clr-white-500);
  height: 100vh;
  padding: 20px;
  grid-area: sidebar;

  &__tree {
    margin-top: 16px;
    transform-origin: 0 0;
    z-index: 2;
    border-radius: 6px;

    img {
      border-radius: 6px;
    }
  }

  &__search {
    margin-bottom: 15px;
    border-radius: 6px;
    box-shadow: 0 6px 8px 0 var(--clr-white-500h);
  }

  &__form-field {
    width: 100%;
    display: flex;
    justify-content: space-between;
  }

  &__heading {
    margin-top: 20px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
  }

  &__general-color {
    display: flex;
    width: 100%;
    padding-left: 5px;
    align-items: center;
  }

  &__event-types {
    font-size: var(--fs-300);
    line-height: var(--lh-300);
    margin-top: 10px;

    svg {
      width: 14px;
      height: 14px;
      fill: var(--fill-color);
    }

    ul {
      padding-left: 0.5em;
      max-height: 500px;
      overflow: scroll;
    }

    li {
      list-style: none;

      +li {
        border-top: 1px solid var(--clr-white-500);
      }
    }
  }

  &__buttons {
    button+button {
      margin-left: 5px;
    }
  }

  &__color-item {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    flex-grow: 0;
    cursor: pointer;

    @include transition();

    &-panel {
      max-height: 0;
      overflow: hidden;
      margin: 0.5em 0;

      @include transition("max-height");

      &--open {
        display: block;
      }

      li+li {
        border-top: none;
        padding: initial;
      }
    }
  }

  input[type="number"] {
    width: unset;
    margin-left: auto;
  }

  input[type="range"] {
    background-color: transparent;
  }

  select {
    margin: 0 4px 0 2px;
  }

  &__level-input {
    max-width: 100px
  }
}
</style>