<script setup>
import { useEventsStore } from "../stores/events";
import dayjs from "dayjs";

const eventsStore = useEventsStore();

function hasDisplayableContent() {
  return this.eventsStore.loadingDetails || this.eventsStore.loadingSequences || eventsStore.eventDetails.length > 0
}
</script>

<template>
  <div class="event-details" v-if="hasDisplayableContent()">
    <b v-if="eventsStore.loadingDetails">Loading event details...</b>
    <b v-if="eventsStore.loadingSequences">Loading sequences...</b>
    <div v-for="(events, eIndex) in eventsStore.eventDetails" :key="eIndex" class="event-detail">
      <b v-if="eventsStore.eventDetails.length > 1">Event {{ eIndex + 1 }} / {{ eventsStore.eventDetails.length }}</b>
      <ul>
        <template v-for="(event, key, index) in events" :key="index">
          <li v-if="
            event &&
            key !== 'charttime' &&
            key !== 'intime' &&
            key !== 'outtime'
          ">
            {{ key }}: {{ event }}
          </li>
          <li v-else-if="event">{{ key }}: {{ dayjs(event) }}</li>
        </template>
      </ul>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.event-details {
  position: absolute;
  bottom: 0;
  right: 0;
  background-color: var(--clr-white-500);
  border: 1px solid var(--clr-black-500);
  padding: 10px 14px;
  max-height: 275px;
  overflow-y: auto;
  border-top-left-radius: 8px;
}

.event-detail+.event-detail {
  margin-top: 10px;
}
</style>