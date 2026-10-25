const nodes = new WeakMap();
let previous;

function rect(element) {
  const box = element.getBoundingClientRect();
  return {
    left: box.left,
    top: box.top,
    width: box.width,
    height: box.height,
    clientWidth: element.clientWidth,
    scrollWidth: element.scrollWidth,
  };
}

function axes(layout) {
  return Object.fromEntries(
    Object.entries(layout)
      .filter(([key]) => /^[xy]axis\d*$/.test(key))
      .map(([key, axis]) => [
        key,
        {
          range: axis.range,
          autorange: axis.autorange,
          rangemode: axis.rangemode,
          title: axis.title,
          domain: axis.domain,
        },
      ])
  );
}

function observedGraph(target) {
  const graph = typeof target === 'string' ? document.querySelector(target) : target;
  if (!graph || !Array.isArray(graph.data) || !graph.layout || !graph._fullLayout) {
    throw new Error(`Plotly graph has no completed layout: ${target}`);
  }
  const svg = graph.querySelector('svg.main-svg');
  if (!svg) throw new Error(`Plotly graph has no SVG: ${target}`);
  if (!nodes.has(graph)) nodes.set(graph, crypto.randomUUID());
  return { graph, svg };
}

function snapshot(target) {
  const { graph, svg } = observedGraph(target);
  const bounds = rect(graph);
  const svgBounds = rect(svg);
  return {
    node: nodes.get(graph),
    container: rect(graph.parentElement),
    graph: bounds,
    svg: svgBounds,
    width: graph._fullLayout.width,
    height: graph._fullLayout.height,
    axes: axes(graph._fullLayout),
    inputAxes: axes(graph.layout),
    traces: graph.data,
    annotations: graph.layout.annotations,
    legend: graph.layout.legend,
    showlegend: graph.layout.showlegend,
    outsideViewport: svgBounds.left < 0 || svgBounds.left + svgBounds.width > innerWidth,
    viewport: { width: innerWidth, height: innerHeight },
    profile: document.querySelector('[title^="Profile: "]')?.getAttribute('title'),
  };
}

function canObserve() {
  return (
    document.fonts.status === 'loaded' &&
    !document.querySelector('.collapsing') &&
    !document.querySelector('[data-dash-is-loading="true"]')
  );
}

function settleGraphs(graphs, ready) {
  if (!ready || !canObserve()) {
    previous = undefined;
    return false;
  }
  let value;
  try {
    value = JSON.stringify(graphs.map(snapshot));
  } catch (error) {
    if (error.message.startsWith('Plotly graph has no')) {
      previous = undefined;
      return false;
    }
    throw error;
  }
  if (!previous || previous.value !== value) {
    previous = { value, since: performance.now() };
    return false;
  }
  return performance.now() - previous.since >= 500;
}

function settled(selectors) {
  const groups = selectors.map((selector) =>
    [...document.querySelectorAll(selector)].filter((graph) => graph.offsetParent !== null)
  );
  return settleGraphs(
    groups.flat(),
    groups.every((group) => group.length > 0)
  );
}

function pageSettled(rootSelector) {
  const root = document.querySelector(rootSelector);
  const graphs = root
    ? [...root.querySelectorAll('.js-plotly-plot')].filter((graph) => graph.offsetParent !== null)
    : [];
  return settleGraphs(graphs, Boolean(root));
}

window.burndownPlotlyProbe = {
  snapshot,
  settled,
  pageSettled,
  reset: () => {
    previous = undefined;
  },
};
