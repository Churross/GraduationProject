<script setup>
import { reactive } from "vue";
import ControlBar from "./components/ControlBar.vue";
import Events from "./components/Events.vue";
import TopBar from "./components/TopBar.vue";
import EventDetails from "./components/EventDetails.vue";

const state = reactive({ data: null });
</script>

<template>
  <ControlBar />
  <Events />
  <TopBar />
  <EventDetails />
</template>

<style lang="scss">
@import "./assets/base.css";
@import "./assets/scss/style.scss";

#app {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 300px auto;
  grid-template-rows: 50px auto;
  width: 100vw;
  grid-template-areas: " sidebar topbar" "sidebar events";
}
</style>
