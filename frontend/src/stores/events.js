import { defineStore, mapActions } from "pinia";
import { toRaw } from "vue";
import { api } from "../api";

export const useEventsStore = defineStore({
  id: "events",
  state: () => ({
    level: 0,
    events: [],
    eventTypes: new Map(),
    eventTypesLookup: new Map(),
    eventDetails: {},
    loadingDetails: false,
    loadingSequences: false,
    patterns: new Map(),
    sequenceIndices: new Map(),
    selectedEvent: [],
    selectedSequence: [],
    dendrogramKey: 0,
  }),
  getters: {
    getEvents: (state) => state.events,
    getLevel: (state) => state.level,
    getEventTypes: (state) => state.eventTypes,
  },
  actions: {
    fetchEvents(support) {
      this.loadingSequences = true;
      this.eventDetails = [];
      this.events = [];
      this.patterns = new Map();
      this.sequenceIndices = new Map();
      this.selectedEvent = [];
      this.selectedSequence = [];

      const request =
        `/cluster/${this.getLevel}/events` +
        (support === 0 ? "" : `?min_sup=${support}`);

      api.get(request).then((data) => {
        console.log("[INFO] Data loaded");
        api
          .get("/patterns")
          .then((patternData) => {
            console.log("[INFO] Patterns loaded");

            for (let pattern of patternData.data) {
              this.patterns.set(pattern.encoding, { pattern: pattern.pattern });
            }
            console.log("[INFO] Patterns set");
            this.events = data.data;
            for (let [idx, event] of toRaw(this.events).entries()) {
              if (typeof event.sequence === "string") {
                // Cast sequence string to list
                event.sequence = event.sequence.split("");
              }
              for (let seq of event.stays) {
                this.sequenceIndices.set(seq, idx);
              }
            }
            this.dendrogramKey++;
            console.log("[INFO] Patterns ready");

            this.loadingSequences = false;
          })
          .catch((error) => {
            console.error(error);
            this.loadingSequences = false;
          });
      });
    },
    setLevel(level) {
      this.level = level;
    },
    fetchEventTypes() {
      this.eventTypes = new Map();
      api
        .get("/events/types")
        .then((data) => {
          let color = 1;
          for (let eventType of data.data) {
            let eventValues = new Map();
            let eventDetails = {
              code: eventType.code,
              type: eventType.type,
              unit: eventType.type === "ICU" ? eventType.unit : -1,
            };

            for (let value of eventType.values) {
              eventValues.set(value, { color: `var(--clr-events-${color})` });
            }

            this.eventTypes.set(eventType.label, {
              values: eventValues,
              eventDetails,
              color: `var(--clr-events-${color})`,
            });

            if (color < 12) {
              color++;
            }
            this.eventTypesLookup.set(eventType.code, {
              label: eventType.label,
            });
          }
        })
        .catch((error) => {
          console.error(error);
        });
    },

    async fetchEventType(type) {
      let values = new Map();

      try {
        const data = await api.get(`/events/types?type=${type}`);
        const color = this.eventTypes.get(type).color;
        for (let value of data.data.values) {
          values.set(value.value_enc, {
            value: value.value,
            unit: value.value_unit,
            color,
          });
        }
        this.eventTypes.set(type, {
          values,
          color,
        });
      } catch (e) {
        console.error(e);
      }
    },

    async fetchEvent(sequence, event) {
      this.loadingDetails = true;
      this.eventDetails = [];
      let sequenceData = this.events[sequence];

      if (sequence >= sequenceData.length) {
        sequence = sequenceData.length - 1;
      }

      if (event >= sequenceData.sequence.length) {
        event = sequenceData.sequence.length - 1;
      }

      const hasVerticalAggregate = sequenceData.sequence.some(
        (event) =>
          typeof event === "number" ||
          (typeof event === "object" && typeof event[0] === "number")
      );

      sequenceData = this.events[sequence];
      let fullSequence = sequenceData.sequence.slice(0, event + 1);

      if (hasVerticalAggregate) {
        fullSequence = getFullSequence(fullSequence, this.patterns);
      }

      // If data is aggregated, all events are by definition at least an aggregate
      if (sequenceData.aggregated) {
        if (
          typeof sequenceData.sequence[event] === "string" ||
          typeof sequenceData.sequence[event][0] === "string"
        ) {
          // get aggregate event
          console.log("[INFO] aggregate event");

          let indexCorrection = 0;

          if (
            sequenceData.sequence
              .slice(0, event + 1)
              .some(
                (e) =>
                  typeof e === "number" ||
                  (typeof e === "object" && typeof e[0] === "number")
              )
          ) {
            // Sequence contains frequent patterns, so adjust the event search index
            for (let e of sequenceData.sequence.slice(0, event)) {
              if (typeof e === "number") {
                indexCorrection += this.patterns.get(e).pattern.length - 1;
              } else if (typeof e === "object" && typeof e[0] === "number") {
                indexCorrection += this.patterns.get(e[0]).pattern.length - 1;
              }
            }
          }

          event += indexCorrection;

          let eventQuery = "";
          for (let seq of sequenceData.alignment) {
            const alignedEvent = seq.sequence.split("")[event];
            if (alignedEvent !== "x" && alignedEvent !== "-") {
              // Change all gap signs to - and count gaps
              const gapReplaceToken = new RegExp("x", "g");
              const numberOfGaps = (
                seq.sequence
                  .slice(0, event + 1)
                  .replace(gapReplaceToken, "-")
                  .match(/-/g) || []
              ).length;
              eventQuery = eventQuery.concat(
                seq.hadm_id,
                ":",
                event - numberOfGaps,
                ","
              );
            }
          }
          await api
            .get(`/sequence/aggregate?sequences=${eventQuery.slice(0, -1)}`)
            .then((response) => {
              this.eventDetails = response.data;
            })
            .catch((e) => console.error(e));
        } else {
          // combined aggregate event
          console.log("[INFO] combined aggregate event");
          const patternLength = this.patterns.get(
            sequenceData.sequence[event][0]
          ).pattern.length;
          const bidx = fullSequence.length - patternLength;

          let eventQuery = "";
          for (let [idx, seq] of sequenceData.alignment.entries()) {
            const sequenceAsList = seq.sequence.split("");
            let lengthIndex = 0;
            for (let i = 0; i < patternLength; i++) {
              const alignedEvent = sequenceAsList[bidx + i];
              if (alignedEvent !== "x" && alignedEvent !== "-") {
                // Change all gap signs to - and count gaps
                lengthIndex++;
              }
            }
            const gapReplaceToken = new RegExp("x", "g");
            const numberOfGaps = (
              seq.sequence
                .slice(0, event + 1)
                .replace(gapReplaceToken, "-")
                .match(/-/g) || []
            ).length;
            eventQuery = eventQuery.concat(
              seq.hadm_id,
              ":",
              Math.max(0, bidx - numberOfGaps),
              ":",
              lengthIndex,
              ","
            );
          }
          await api
            .get(
              `/sequence/aggregate/pattern?sequences=${eventQuery.slice(0, -1)}`
            )
            .then((response) => {
              this.eventDetails = response.data;
            })
            .catch((e) => console.error(e));
        }
      } else {
        if (typeof sequenceData.sequence[event] === "number") {
          // frequent pattern event
          console.log("[INFO] frequent pattern event");
          const patternLength = this.patterns.get(sequenceData.sequence[event])
            .pattern.length;
          const bidx = fullSequence.length - patternLength;
          await api
            .get(
              `/sequence/pattern/${sequenceData.stays[0]}?index=${bidx}&num_events=${patternLength}`
            )
            .then((response) => {
              this.eventDetails = response.data;
            })
            .catch((e) => console.error(e));
        } else {
          //  common event
          console.log("[INFO] common event");
          const eidx = fullSequence.length - 1;
          await api
            .get(`/sequence/${sequenceData.stays[0]}?index=${eidx}`)
            .then((response) => {
              this.eventDetails.push(response.data[0]);
            })
            .catch((e) => console.error(e));
        }
      }
      this.loadingDetails = false;
    },
    fetchPatterns() {
      api
        .get("/patterns")
        .then((data) => {
          for (let pattern of data.data) {
            this.patterns.set(pattern.encoding, { pattern: pattern.pattern });
          }
          console.log("[INFO] fetched patterns");
        })
        .catch((error) => {
          console.error(error);
        });
    },
  },
});

function getFullSequence(fullSequence, patterns) {
  for (let [idx, event] of fullSequence.entries()) {
    if (typeof event === "number") {
      const patternSequence = patterns.get(event);
      fullSequence = fullSequence
        .slice(0, idx)
        .concat(patternSequence.pattern, fullSequence.slice(idx + 1));
    } else if (typeof event === "object" && typeof event[0] === "number") {
      const patternSequence = patterns.get(event[0]);
      fullSequence = fullSequence
        .slice(0, idx)
        .concat(patternSequence.pattern, fullSequence.slice(idx + 1));
    }
  }
  return fullSequence;
}
