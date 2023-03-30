<script setup>
import { computed, onMounted, reactive, ref, watch, toRaw } from "vue";
import { useEventsStore } from "../stores/events";
import { useControlsStore } from "../stores/controls";

const eventsStore = useEventsStore();
const controlsStore = useControlsStore();
const canvasContainer = ref(null);
const canvas = ref(null);
const style = getComputedStyle(document.body);
const MAX_ZOOM = 5;
const MIN_ZOOM = 0.1;
const SCROLL_SENSITIVITY = 0.0005;
const INITIAL_EVENT_OFFSET = 20;
const AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL = 2;
const AGGREGATE_EVENT_MULTIPLIER_VERTICAL = 1.1;
const VERTICAL_AGGREGATE_MARGIN_PERCENTAGE = 0.05;

let drawStack = [];

const state = reactive({
  displayedEvents: [],
  canvas: null,
  context: null,
  x: 0,
  y: 0,
  hasHorizontalAggregate: false,
  hasVerticalAggregate: false,
  hasCombinedAggregate: false,
  canvasWidth: 0,
  canvasHeight: 0,
  isDragging: false,
  dragStart: { x: 0, y: 0 },
  initialPinchDistance: null,
  lastZoom: 1,
  circleRadius: 7,
  sequencesPositions: [],
  eventPositions: [],
  debugging: true,
  aggregateMargin: 0,
});

watch(canvasContainer, () => {
  resizeCanvas();
});

// using https://codepen.io/chengarda/pen/wRxoyB
function draw() {
  canvas.value.width = canvasContainer.value.offsetWidth;
  canvas.value.height = canvasContainer.value.offsetHeight;

  state.context.scale(controlsStore.cameraZoom, controlsStore.cameraZoom);

  state.context.translate(
    controlsStore.cameraOffset.x,
    controlsStore.cameraOffset.y
  );
  state.context.clearRect(0, 0, state.canvasWidth, state.canvasHeight);
  drawSequences();

  requestAnimationFrame(draw);
}

// Gets the relevant location from a mouse or single touch event
function getEventLocation(e) {
  if (e.touches && e.touches.length == 1) {
    return { x: e.touches[0].clientX, y: e.touches[0].clientY };
  } else if (e.clientX && e.clientY) {
    return { x: e.clientX, y: e.clientY };
  }
}

function onPointerDown(e) {
  state.isDragging = true;
  state.dragStart.x =
    getEventLocation(e).x / controlsStore.cameraZoom -
    controlsStore.cameraOffset.x;
  state.dragStart.y =
    getEventLocation(e).y / controlsStore.cameraZoom -
    controlsStore.cameraOffset.y;
}

function onPointerUp(e) {
  state.isDragging = false;
  state.initialPinchDistance = null;
  state.lastZoom = controlsStore.cameraZoom;
}

function onPointerMove(e) {
  if (state.isDragging) {
    controlsStore.setCameraOffset({
      x: getEventLocation(e).x / controlsStore.cameraZoom - state.dragStart.x,
      y: getEventLocation(e).y / controlsStore.cameraZoom - state.dragStart.y,
    });
  }
}

function handleTouch(e, singleTouchHandler) {
  if (e.touches.length == 1) {
    singleTouchHandler(e);
  } else if (e.type == "touchmove" && e.touches.length == 2) {
    state.isDragging = false;
    handlePinch(e);
  }
}

function handlePinch(e) {
  e.preventDefault();

  let touch1 = { x: e.touches[0].clientX, y: e.touches[0].clientY };
  let touch2 = { x: e.touches[1].clientX, y: e.touches[1].clientY };

  // This is distance squared, but no need for an expensive sqrt as it's only used in ratio
  let currentDistance = (touch1.x - touch2.x) ** 2 + (touch1.y - touch2.y) ** 2;

  if (state.initialPinchDistance == null) {
    state.initialPinchDistance = currentDistance;
  } else {
    adjustZoom(null, currentDistance / state.initialPinchDistance);
  }
}

function adjustZoom(zoomAmount, zoomFactor) {
  if (!state.isDragging) {
    if (zoomAmount) {
      controlsStore.setCameraZoom(controlsStore.cameraZoom + zoomAmount);
    } else if (zoomFactor) {
      controlsStore.setCameraZoom(zoomFactor * state.lastZoom);
    }

    controlsStore.setCameraZoom(Math.min(controlsStore.cameraZoom, MAX_ZOOM));
    controlsStore.setCameraZoom(Math.max(controlsStore.cameraZoom, MIN_ZOOM));
  }
}

function resizeCanvas() {
  state.canvasWidth = canvasContainer.value.clientWidth;
  state.canvasHeight = canvasContainer.value.clientHeight;
}

function getEventColor(event) {
  const eventNumber = event
  let color = null;

  if (typeof eventNumber == 'string') {

    const label = eventsStore.eventTypesLookup.get(eventNumber).label;
    color = eventsStore.eventTypes.get(label);
  }

  if (color) {
    if (eventsStore.selectedEvent.length === 0 || eventsStore.selectedEvent.includes(eventNumber)) {
      // return normal color
      return color.color.split("(").pop().split(")")[0]
    } else {
      // return dimmed color
      return color.color.split("(").pop().split(")")[0].replace('events', 'events-dimmed')
    }
  } else {
    return "--clr-events-10"
  }
}

function drawCommonEvent(event, highlighted = true, yCoord = state.y) {
  let color = getEventColor(event);

  // Highlight event if the sequence should be highlighted
  if (eventsStore.selectedEvent.length > 0 && highlighted) {
    if (highlighted && color.includes('events-dimmed')) {
      color = color.replace("events-dimmed", "events")
    } else if (!highlighted && !color.includes('events-dimmed')) {
      color = color.replace("events", "events-dimmed")
    }
  } else if (eventsStore.selectedSequence.length > 0 && !highlighted) {
    if (!color.includes('events-dimmed')) {
      color = color.replace("events", "events-dimmed")
    }
  }

  state.context.fillStyle = style.getPropertyValue(color);
  state.context.fillRect(
    state.x,
    yCoord,
    controlsStore.eventWidth,
    controlsStore.eventWidth
  );
  state.x += controlsStore.eventWidth;
}

// Draw simple aggregate event when dragging (no extra context)
function drawAggregateEventDragging(horizontalAggregate, verticalAggregate) {
  let color = style.getPropertyValue("--clr-ice-600");
  state.context.fillStyle = color;

  if (horizontalAggregate && !verticalAggregate) {
    state.context.fillRect(
      state.x,
      state.y,
      controlsStore.eventWidth,
      controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL
    );
    state.x += controlsStore.eventWidth;

  } else if (!horizontalAggregate && verticalAggregate) {
    state.x += state.aggregateMargin

    state.context.fillRect(
      state.x,
      state.y,
      (controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL - (2 * state.aggregateMargin)),
      controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_VERTICAL,
    );
    state.x += state.aggregateMargin + controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL - (2 * state.aggregateMargin)
  }
  else {
    state.x += state.aggregateMargin

    state.context.fillRect(
      state.x,
      state.y,
      (controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL - (2 * state.aggregateMargin)),
      controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL
    );
    state.x += state.aggregateMargin + controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL - (2 * state.aggregateMargin)
  }
}

function getCountsEventsFromAggregate(eventsList) {
  let numOccurrences = eventsList.reduce(
    (acc, e) => acc.set(e, (acc.get(e) || 0) + 1),
    new Map()
  );
  numOccurrences = new Map([...numOccurrences.entries()].sort((a, b) => b[1] - a[1]));


  // Get top 3 events
  const displayedEvents = [...numOccurrences.keys()].slice(
    0,
    Math.min(eventsList.length, 3)
  );

  // get counts of top 3 events
  let counts = [];
  for (let event of displayedEvents) {
    counts.push(numOccurrences.get(event));
  }

  // check if there are other events which are not in top 3
  const countOthers = [...numOccurrences.keys()].length - 3;
  const totalCount = counts.reduce((a, b) => a + b, 0);

  return {
    displayedEvents, counts, countOthers, totalCount, numOccurrences
  }
}

function drawAggregateEvent(sequenceIndex, eventIndex, horizontalAggregate, verticalAggregate) {
  if (state.isDragging) {
    if ((horizontalAggregate && verticalAggregate && !eventsStore.events[sequenceIndex].sequence[eventIndex].length > 0)) {
      state.y += 0.45 * controlsStore.eventWidth
      drawAggregateEventDragging(false, true)
      state.y -= 0.45 * controlsStore.eventWidth
    } else {
      drawAggregateEventDragging(horizontalAggregate, verticalAggregate)
    }
  } else {

    if (horizontalAggregate && !verticalAggregate) {
      // Case horizontal aggregate
      let events = []
      let fullEvents = []
      let indexCorrection = 0

      if (eventsStore.events[sequenceIndex].sequence.slice(0, eventIndex + 1).some((event) => typeof event === "number" || typeof event === "object" && typeof event[0] === "number")) {
        // Sequence contains frequent patterns, so adjust the event search index
        for (let e of eventsStore.events[sequenceIndex].sequence.slice(0, eventIndex)) {
          if (typeof e === 'number') {
            indexCorrection += eventsStore.patterns.get(e).pattern.length - 1
          } else if (typeof e === 'object' && typeof e[0] === 'number') {
            indexCorrection += eventsStore.patterns.get(e[0]).pattern.length - 1
          }
        }
      }

      eventIndex += indexCorrection

      // Filter gaps if needed for
      for (let sequence of eventsStore.events[sequenceIndex].alignment) {
        if (
          (sequence.sequence[eventIndex] === "-" &&
            controlsStore.showAggregateGaps) ||
          sequence.sequence[eventIndex] !== "-"
        ) {
          events.push(sequence.sequence[eventIndex]);
        }
        fullEvents.push(sequence.sequence[eventIndex].replace('x', '-'));
      }

      events.sort();
      fullEvents.sort()

      const event = getCountsEventsFromAggregate(events)

      let highlightSequence = true

      if (eventsStore.selectedSequence.length > 0 && !eventsStore.selectedSequence.includes(sequenceIndex)) {
        highlightSequence = false
      } else {
        if (eventsStore.selectedEvent.length > 0) {
          if (typeof eventsStore.selectedEvent === 'object') {
            const fullEventsCopy = [...new Set(fullEvents)].sort()

            highlightSequence = false

            for (let selected of eventsStore.selectedEvent) {
              if (typeof selected === 'object' && fullEventsCopy.every((el) => selected.includes(el))) {
                highlightSequence = true
                break;
              }
            }

          } else {
            highlightSequence = false
          }
        }
      }

      drawHorizontalAggregate(event.displayedEvents, event.counts, event.countOthers, event.totalCount, controlsStore.eventWidth, highlightSequence)

      state.x += controlsStore.eventWidth
    } else if ((!horizontalAggregate && verticalAggregate) || (horizontalAggregate && verticalAggregate && !eventsStore.events[sequenceIndex].sequence[eventIndex].length > 0)) {
      // Case horizontal aggregate
      let events = eventsStore.events[sequenceIndex].sequence[eventIndex]
      let pattern = eventsStore.patterns.get(events)
      pattern = toRaw(pattern.pattern)

      const event = getCountsEventsFromAggregate(pattern)
      const highlighted = eventsStore.selectedEvent.includes(events) || (eventsStore.selectedEvent.length === 0 && eventsStore.selectedSequence.includes(sequenceIndex))

      let heightCorrection = 0;
      if (horizontalAggregate && verticalAggregate && !eventsStore.events[sequenceIndex].sequence[eventIndex].length > 0) {
        // Correction case fp is inserted and both fp and hor aggregate is present
        heightCorrection = 0.45 * controlsStore.eventWidth
      }

      state.y += heightCorrection
      drawVerticalAggregate(event.displayedEvents, event.counts, event.countOthers, event.totalCount, highlighted)
      state.y -= heightCorrection


    }
    else {
      // Case combined aggregate
      let events = toRaw(eventsStore.events[sequenceIndex].sequence[eventIndex])
      let pattern = toRaw(eventsStore.patterns.get(events[0])).pattern
      state.x += state.aggregateMargin

      let pat = getCountsEventsFromAggregate(pattern);
      let highlighted = true

      if (eventsStore.selectedSequence.length > 0 && !eventsStore.selectedSequence.includes(sequenceIndex)) {
        highlighted = false
      } else {
        highlighted = eventsStore.selectedEvent.includes(events) || (eventsStore.selectedEvent.length === 0 && eventsStore.selectedSequence.includes(sequenceIndex))

      }

      if (pattern.length <= 3) {
        // Display all events
        for (let [index, aggregate] of pat.displayedEvents.entries()) {
          let event = aggregate.split('')
          let eventData = getCountsEventsFromAggregate(event)
          const partialWidth = pat.counts[index] / pat.totalCount
          const width = partialWidth * (controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL - (2 * state.aggregateMargin));

          drawHorizontalAggregate(eventData.displayedEvents, eventData.counts, eventData.countOthers, eventData.totalCount, width, highlighted)
          state.x += width
        }


      } else {
        if (pat.counts[0] == 1) {
          // All events are equally frequent, display events based on composing event frequencies
          let patternEvents = [...new Set(pattern.join('').split(''))]

          let eventData = getCountsEventsFromAggregate(patternEvents)
          for (let index = 0; index < eventData.displayedEvents.length; index++) {
            const width = (1 / 3) * (controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL - 2 * state.aggregateMargin);
            drawHorizontalAggregate([eventData.displayedEvents[index]], [eventData.counts[index]], index === 2 ? eventData.countOthers : 0, 1, width, highlighted)
            state.x += width
          }

        } else {
          // Display first 3 events
          for (let [index, aggregate] of pat.displayedEvents.slice(0, 3).entries()) {
            let event = aggregate.split('')
            let eventData = getCountsEventsFromAggregate(event)
            const partialWidth = pat.counts[index] / pat.totalCount
            const width = partialWidth * (controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL - 2 * state.aggregateMargin);

            drawHorizontalAggregate(eventData.displayedEvents, eventData.counts, eventData.countOthers, eventData.totalCount, width, highlighted)

            state.x += width

          }
        }
      }
      state.x += state.aggregateMargin

    }

  }

  function drawHorizontalAggregate(displayedEvents, eventCounts, countOthers, totalCount, aggregateWidth, highlighted = false) {
    const yTop = state.y
    let yTemp = yTop;

    if (eventsStore.selectedEvent.length === 0 && eventsStore.selectedSequence.length === 0) {
      highlighted = true
    }

    for (let [index, event] of displayedEvents.entries()) {
      let eventColor = event === "-" || event === "x" ? "--clr-ice-200" : getEventColor(event)

      if (!highlighted && !eventColor.includes('dimmed')) {
        eventColor = eventColor.replace("events", "events-dimmed")
      }

      if (!highlighted && eventColor.includes("ice")) {
        eventColor = eventColor.replace("ice", "ice-dimmed")
      }
      // Undo dimming
      if (highlighted && !eventColor.includes("ice")) {
        eventColor = eventColor.replace("events-dimmed", "events")
      }



      let color = style.getPropertyValue(eventColor);

      const partialHeight = eventCounts[index] / totalCount;
      const x = state.x;
      const y = yTemp;
      const width = aggregateWidth;
      const height =
        partialHeight * controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL;
      drawBorder(x, y, width, height);

      state.context.fillStyle = color;
      state.context.fillRect(x, y, width, height);

      yTemp += height;
    }
    if (countOthers > 0) {
      state.context.beginPath();
      state.context.moveTo(state.x, yTop);
      state.context.lineTo(state.x + aggregateWidth, yTop);
      state.context.lineTo(
        state.x + aggregateWidth,
        yTop + 0.75 * controlsStore.eventWidth
      );
      state.context.closePath();

      state.context.fillStyle = `hsla(0, 100%, 50%,${highlighted ? 1 : 0.3})`;
      state.context.fill();
    }
  }
}

function drawVerticalAggregate(displayedEvents, eventCounts, countOthers, totalCount, highlighted = false) {
  state.x += state.aggregateMargin
  const yTop = state.y
  let xTemp = state.x

  if (!highlighted && eventsStore.selectedEvent.length === 0 && eventsStore.selectedSequence.length === 0) {
    highlighted = true
  }

  for (let [index, event] of displayedEvents.entries()) {
    let eventColor = event === "-" || event === "x" ? "--clr-ice-200" : getEventColor(event)

    if (highlighted) {
      eventColor = eventColor.replace('events-dimmed', 'events')
    }

    // Only highlight if the current event is also selected. Remove to show events which are in the fp
    if (!highlighted && !eventColor.includes('events-dimmed')) {
      eventColor = eventColor.replace('events', 'events-dimmed')
    }

    let color = style.getPropertyValue(eventColor);
    const partialWidth = eventCounts[index] / totalCount
    const x = xTemp;
    const y = yTop;
    const width = partialWidth * (controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL - (2 * state.aggregateMargin));
    const height = controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_VERTICAL

    drawBorder(x, y, width, height);
    state.context.fillStyle = color;
    state.context.fillRect(x, y, width, height);
    xTemp += width
  }
  state.x += state.aggregateMargin
  state.x += controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL - (2 * state.aggregateMargin);
}

function drawBorder(x, y, width, height, thickness = 1) {
  state.context.fillStyle = "#000";
  state.context.fillRect(
    x - thickness,
    y - thickness,
    width + thickness * 2,
    height + thickness * 2
  );
}

function drawSequences() {
  if (state.context) {
    state.x = controlsStore.eventMargin + INITIAL_EVENT_OFFSET;
    state.y = controlsStore.sequenceMargin + INITIAL_EVENT_OFFSET;
    state.sequencesPositions = [];
    state.eventPositions = [];
    state.aggregateMargin = VERTICAL_AGGREGATE_MARGIN_PERCENTAGE * controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL
  }


  const viewportWidth =
    controlsStore.cameraZoom > 1
      ? canvasContainer.value.offsetWidth
      : canvasContainer.value.offsetWidth / controlsStore.cameraZoom;
  const viewportHeight =
    controlsStore.cameraZoom > 1
      ? canvasContainer.value.offsetHeight
      : canvasContainer.value.offsetHeight / controlsStore.cameraZoom;


  for (let [s, sequence] of eventsStore.events.entries()) {
    state.hasHorizontalAggregate = sequence.aggregated
    state.hasVerticalAggregate = sequence.sequence.some((event) => typeof event === 'number')
    state.hasCombinedAggregate = state.hasHorizontalAggregate && state.hasVerticalAggregate

    if (state.y < -controlsStore.cameraOffset.y - viewportHeight) {
      state.y += controlsStore.sequenceMargin + controlsStore.eventWidth;
      continue;
    } else if (state.y > viewportHeight + -controlsStore.cameraOffset.y) {
      break;
    } else {


      if (state.hasVerticalAggregate && s > 0 && !eventsStore.events[s - 1].sequence.some((event) => typeof event === 'number') && !eventsStore.events[s - 1].aggregated) {
        // Add extra top margin if previous sequence did not contain any aggregate event, but the current does contain a fp event
        state.y += ((controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_VERTICAL) / 2) - 0.5 * controlsStore.eventWidth + 1;
      }

      state.sequencesPositions.push(state.y);
      let currentSequenceEventPositions = []

      for (let [i, event] of toRaw(sequence.sequence).entries()) {
        if (state.x < -controlsStore.cameraOffset.x - viewportWidth) {
          state.x += controlsStore.eventMargin + controlsStore.eventWidth;
          continue;
        } else if (state.x > viewportWidth + -controlsStore.cameraOffset.x) {
          break;
        } else {

          currentSequenceEventPositions.push(state.x)

          if (typeof event !== "string" || (typeof event === "string" && parseInt(event) > 300)) {
            // Event is aggregate, so always draw immediately
            const horizontalAggregate = typeof event !== 'string' && sequence.aggregated
            const verticalAggregate = (typeof event === 'object' && event.some(e => typeof (e) === "number")) || (typeof event === "number")

            drawAggregateEvent(s, i, horizontalAggregate, verticalAggregate);
          } else {
            const highlighted = (eventsStore.selectedSequence.includes(s) && eventsStore.selectedEvent.length === 0) || eventsStore.selectedEvent.includes(event)
            if (state.hasHorizontalAggregate || state.hasCombinedAggregate) {
              drawCommonEvent(event, highlighted, state.y + ((controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL) / 2) - 0.5 * controlsStore.eventWidth);
            } else if (state.hasVerticalAggregate) {
              drawCommonEvent(event, highlighted, state.y + ((controlsStore.eventWidth * AGGREGATE_EVENT_MULTIPLIER_VERTICAL) / 2) - 0.5 * controlsStore.eventWidth);
            } else {
              drawCommonEvent(event, highlighted,);
            }
          }

        }
        state.x += controlsStore.eventMargin
      }
      state.eventPositions.push(currentSequenceEventPositions)
    }
    state.x = controlsStore.eventMargin + INITIAL_EVENT_OFFSET;
    state.y += controlsStore.sequenceMargin + controlsStore.eventWidth * (state.hasHorizontalAggregate || state.hasCombinedAggregate ? AGGREGATE_EVENT_MULTIPLIER_HORIZONTAL : state.hasVerticalAggregate ? AGGREGATE_EVENT_MULTIPLIER_VERTICAL : 1)
    if (state.hasHorizontalAggregate || state.hasCombinedAggregate || state.hasVerticalAggregate) {
      state.y += 2
    }

    state.hasHorizontalAggregate = false;
    state.hasVerticalAggregate = false;
    state.hasCombinedAggregate = false;
  }
}

function hasSameColor(event1, event2) {
  return getEventColor(event1) === getEventColor(event2);
}

// Calculate the mouse position, and compensate for the initial offset
function getEventHoverLocation(e) {
  const widthOffset =
    document.getElementsByClassName("controls")[0].offsetWidth;
  const heightOffset =
    document.getElementsByClassName("topbar")[0].offsetHeight;
  return {
    x:
      (getEventLocation(e).x - widthOffset) / controlsStore.cameraZoom -
      controlsStore.eventMargin,

    y:
      (getEventLocation(e).y - heightOffset) / controlsStore.cameraZoom -
      controlsStore.sequenceMargin,

  };
}

function undoHighlighting(e) {
  e.preventDefault();
  eventsStore.selectedSequence = []
  eventsStore.selectedEvent = []
  return
}

function getEventDetails(e) {
  if (!(e.shiftKey || e.altKey)) {
    eventsStore.eventDetails = ""
    return
  }
  let mouseLocation = getEventHoverLocation(e);

  let sequence = -1;
  let event = -1;


  // Calculate sequence based on events and mouse position
  for (let [index, seq] of state.sequencesPositions.entries()) {
    if (mouseLocation.y - controlsStore.cameraOffset.y < seq && index === 0) {
      sequence = index;
      break;
    } else if (
      mouseLocation.y - controlsStore.cameraOffset.y <= seq &&
      index > 0 &&
      mouseLocation.y - controlsStore.cameraOffset.y >=
      state.sequencesPositions[index - 1]
    ) {
      sequence = index - 1;
      break;
    }
  }

  if (sequence === -1) {
    // none found, clicked outside the event sequences
    sequence = eventsStore.events.length - 1;
  }

  for (let [index, ev] of state.eventPositions[sequence].entries()) {
    if (mouseLocation.x - controlsStore.cameraOffset.x < ev && index === 0) {
      event = index;
      break;
    } else if (
      mouseLocation.x - controlsStore.cameraOffset.x <= ev && index > 0 &&
      mouseLocation.x - controlsStore.cameraOffset.x > state.eventPositions[sequence][index - 1]
    ) {
      event = index - 1;
      break;
    }
  }

  if (event === -1) {
    // none found, clicked outside the event sequences
    event = eventsStore.events[sequence].sequence.length - 1;
  }

  if (e.altKey) {
    eventsStore.fetchEvent(sequence, event);
  } else if (e.shiftKey) {
    if (eventsStore.selectedEvent.includes(eventsStore.events[sequence].sequence[event])) {
      const eventIndex = eventsStore.selectedEvent.indexOf(eventsStore.events[sequence].sequence[event])
      eventsStore.selectedEvent.splice(eventIndex, 1)

    } else {
      if (typeof eventsStore.events[sequence].sequence[event] === 'object') {
        let tempEvent = eventsStore.events[sequence].sequence[event]
        tempEvent.forEach((event, i) => {
          if (event === 'x') tempEvent[i] = '-'
        })
        eventsStore.selectedEvent.push(eventsStore.events[sequence].sequence[event])
      } else {
        eventsStore.selectedEvent.push(eventsStore.events[sequence].sequence[event])
      }
    }
  }
}


onMounted(() => {
  state.context = canvas.value.getContext("2d");

  canvas.value.addEventListener("mousedown", onPointerDown);
  canvas.value.addEventListener("touchstart", (e) =>
    handleTouch(e, onPointerDown)
  );
  canvas.value.addEventListener("mouseup", onPointerUp);
  canvas.value.addEventListener("touchend", (e) => handleTouch(e, onPointerUp));
  canvas.value.addEventListener("mousemove", onPointerMove);
  canvas.value.addEventListener("click", (e) => getEventDetails(e));
  canvas.value.addEventListener("touchmove", (e) =>
    handleTouch(e, onPointerMove)
  );
  canvas.value.addEventListener("contextmenu", (e) => undoHighlighting(e));
  canvas.value.addEventListener("wheel", (e) =>
    adjustZoom(e.deltaY * SCROLL_SENSITIVITY)
  );

  draw();
});

const events = computed(() => {
});
</script>

<template>
  <div class="events">
    {{ events }}

    <div class="events__canvas" ref="canvasContainer">
      <canvas id="canvas" ref="canvas"></canvas>
    </div>
  </div>
</template>



<style lang="scss" scoped>
@use "@/assets/scss/abstracts" as *;

canvas {
  height: 100%;
  width: 100%;
}

.events {
  display: flex;
  flex-direction: column;
  grid-area: events;
  height: calc(100vh - 50px);

  &__canvas {
    height: 100%;
    max-height: 100%;
    width: 100%;
    overflow: scroll;
    background-color: var(--clr-black-600);
  }
}
</style>