<script setup>
import { reactive, onMounted, computed, watch, toRaw } from "vue";
import { useEventsStore } from "../stores/events";
import { useControlsStore } from "../stores/controls";
import { api } from "../api";
import Sunburst from "sunburst-chart";
import * as d3 from "d3";

const state = reactive({
    currenLevelIndex: 60,
    allLevels: [],
    sequences: [],
    height: 220,
    sunburst: Sunburst(),
    tree: {},
    loaded: false,
    seqIndices: new Map()

});
const eventsStore = useEventsStore();
const controlsStore = useControlsStore();

function computePartialTree() {
    let tree = {
        name: `level-${state.currenLevelIndex}`,
        children: [],
    };

    if (state.currenLevelIndex === 0) {
        // Top level

        const current = state.allLevels[state.currenLevelIndex + 1].cluster;
        const uniqueClusters = [...new Set(current)];

        for (let cluster of uniqueClusters) {
            let childObject = {
                name: cluster,
                color: 1,
                sequences: getClusterSequencesIDS(state.currenLevelIndex + 1, cluster),
                children: getChildren(cluster, state.currenLevelIndex + 1, true, 2),
            };

            tree.children.push(childObject);
        }
    } else if (state.currenLevelIndex === state.allLevels.length - 1) {
        // Bottom level

        const current = state.allLevels[state.currenLevelIndex].cluster;
        const uniqueClusters = [...new Set(current)];

        for (let cluster of uniqueClusters) {
            let childObject = {
                name: cluster,
                color: 2,
                sequences: getClusterSequencesIDS(state.currenLevelIndex, cluster),
                children: getChildren(cluster, state.currenLevelIndex, true, 3),
            };

            tree.children.push(childObject);
        }
    } else {
        // Levels in between
        const previous = state.allLevels[state.currenLevelIndex + 1].cluster;
        let uniqueClusters = [...new Set(previous)];

        for (let cluster of uniqueClusters) {
            let childObject = {
                name: cluster,
                color: 1,
                sequences: getClusterSequencesIDS(state.currenLevelIndex + 1, cluster),
                children: getChildren(cluster, state.currenLevelIndex + 1, false, 2),
            };

            for (let [i, child] of childObject.children.entries()) {

                childObject.children[i].children = getChildren(
                    child.name,
                    state.currenLevelIndex,
                    true, 3
                );
            }

            tree.children.push(childObject);
        }
    }

    state.tree = tree;
    state.sunburst.data(state.tree).sort((a, b) => sortDendrogramSlices(a, b))
}

function getClusterSequencesIDS(clusterLevel, clusterIndex) {
    const indices = state.allLevels[clusterLevel].cluster.reduce(function (a, e, i) {
        if (e === parseInt(clusterIndex)) a.push(i);
        return a;
    }, []);

    let seqs = []
    for (let idx of indices) {
        seqs.push(state.sequences[idx])
    }

    return seqs.sort((a, b) => eventsStore.sequenceIndices.get(a) - eventsStore.sequenceIndices.get(b))
}

function getChildren(currentCluster, level, bottomLevel = true, color) {
    // Get the cluster on input, return a list of children
    let childrenTree = [];
    let clusters = [];
    const parents = state.allLevels[level].cluster;
    const children = state.allLevels[level - 1].cluster;

    // Get indices of all sequences in the cluster
    let indices = parents.reduce(function (a, e, i) {
        if (e === parseInt(currentCluster)) a.push(i);
        return a;
    }, []);

    // Calculate children clusters
    for (let idx of indices) {
        clusters.push(children[idx]);
    }

    // count number of sequences per cluster
    const childrenOccurrences = clusters.reduce(function (acc, curr) {
        return acc[curr] ? ++acc[curr] : (acc[curr] = 1), acc;
    }, {});

    for (let idx of Object.keys(childrenOccurrences)) {
        if (bottomLevel) {
            childrenTree.push({
                name: idx,
                color,
                sequences: getClusterSequencesIDS(level - 1, idx),
                size: childrenOccurrences[idx],
            });
        } else {
            childrenTree.push({
                name: idx,
                color,
                sequences: getClusterSequencesIDS(level - 1, idx),
                children: [],
            });
        }
    }
    return childrenTree;
}


function setClusteringLevel(level) {
    eventsStore.setLevel(state.allLevels[level].level);
    eventsStore.fetchEvents(controlsStore.minimumSupport);
    state.currenLevelIndex = level;
    state.sunburst.data({});
    computePartialTree();
    eventsStore.selectedEvent = []
    eventsStore.selectedSequence = []
}

function sortDendrogramSlices(a, b) {
    return eventsStore.sequenceIndices.get(a.data.sequences[0]) - eventsStore.sequenceIndices.get(b.data.sequences[0])
}

function getCounts(index) {
    return state.allLevels[index].cluster.reduce(
        (acc, e) => acc.set(e, (acc.get(e) || 0) + 1),
        new Map()
    );
}

function clickNode(node) {
    if (node) {
        let sequenceIndices = []
        for (let seq of node.sequences) {
            sequenceIndices.push(eventsStore.sequenceIndices.get(seq))
        }
        sequenceIndices = [...new Set(sequenceIndices)]

        eventsStore.selectedEvent = []
        eventsStore.selectedSequence = sequenceIndices
    } else {
        eventsStore.selectedSequence = []
        eventsStore.selectedEvent = []
    }
}

onMounted(() => {
    api.get("/levels").then((data) => {
        state.allLevels = data.data.levels;
        state.sequences = data.data.sequences;
        state.currenLevelIndex = state.allLevels.length - 2;
        setClusteringLevel(2)

        const color = d3.interpolateCividis

        // Configure sunburst visualization
        state.sunburst
            .excludeRoot(true)
            .showLabels(false)
            .centerRadius(0.4)
            .height(state.height - 20)
            .width(state.height - 20)
            .sort((a, b) => sortDendrogramSlices(a, b))
            .size("size")
            .color((d) => color(d.color / 4))
            .radiusScaleExponent(1)
            .onClick(clickNode)
            .transitionDuration(0)(document.getElementById("dendrogram"));
        state.loaded = true
    });
});

const cluster = computed(() => {
    if (state.allLevels.length === 0) {
        return [100];
    } else {
        return [...getCounts(state.currenLevelIndex).values()];
    }
});

watch(eventsStore.dendrogramKey, () => {
    if (state.loaded) {
        state.seqIndices = eventsStore.sequenceIndices
        computePartialTree()
    }
})

watch(eventsStore.sequenceIndices, (newValue, oldValue) => {
})


</script>

<template>
    <div class="dendrogram">
        <div class="dendrogram__clusters" :style="{ height: state.height + 'px' }">
            <svg :id="`level-${index}`" viewBox="0 0 50 60" xmlns="http://www.w3.org/2000/svg"
                v-for="(cluster, index) in state.allLevels" @click="setClusteringLevel(index)" class="dendrogram__cluster">
                <circle cx="25" cy="25" r="25" :fill="
                    index === state.currenLevelIndex
                        ? 'var(--clr-ice-500)'
                        : 'var(--clr-white-500)'
                " />
                <text x="50%" y="27" dominant-baseline="middle" text-anchor="middle">
                    {{ [...new Set(cluster.cluster)].length }}
                </text>
                <line x1="25" y1="50" x2="25" y2="60" style="stroke: var(--clr-black-500); stroke-width: 2"
                    v-if="index + 1 !== state.allLevels.length" />
            </svg>
        </div>
        <div id="dendrogram"></div>
    </div>
    <!-- <div class="dendrogram">
        
                                                                                                                        <div>
                                                                                                                            <div id="chart" class="dendrogram__donut-chart">
                                                                                                                                <apexchart id="donut-chart" type="donut" :options="state.chartOptions" :series="cluster"
                                                                                                                                    @dataPointSelection="clickHandler">
                                                                                                                                </apexchart>
                                                                                                                            </div>
                                                                                                                        </div>
                                                                                                                    </div> -->
</template>

<style lang="scss" scoped>
@use "@/assets/scss/abstracts" as *;

.dendrogram {
    display: flex;

    &__clusters {
        width: 60px;
        overflow-y: scroll;
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;

        svg {
            width: 35px;
            height: 35px;
            cursor: pointer;
        }
    }

    &__donut-chart {}
}
</style>
