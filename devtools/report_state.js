let previous;
const properties = ['x', 'y', 'base', 'width', 'height'];

function rect(element) {
  const box = element.getBoundingClientRect();
  return { left: box.left, top: box.top, width: box.width, height: box.height };
}

function position(element, final) {
  const values = element.getProps(properties, final);
  return Object.fromEntries(properties.map((name) => [name, values[name]]));
}

function dataset(chart, index) {
  const input = chart.data.datasets[index];
  const meta = chart.getDatasetMeta(index);
  return {
    label: input.label,
    type: meta.type,
    input: input.data,
    xAxisID: meta.xAxisID,
    yAxisID: meta.yAxisID,
    elements: meta.data.map((element, point) => ({
      point,
      current: position(element, false),
      target: position(element, true),
    })),
  };
}

function chartState(chart) {
  return {
    id: chart.canvas.id,
    canvas: rect(chart.canvas),
    container: rect(chart.canvas.parentElement),
    width: chart.width,
    height: chart.height,
    labels: chart.data.labels,
    datasets: chart.data.datasets.map((value, index) => dataset(chart, index)),
    scales: Object.fromEntries(
      Object.entries(chart.scales).map(([id, scale]) => [
        id,
        {
          axis: scale.axis,
          type: scale.type,
          min: scale.min,
          max: scale.max,
          zeroPixel: scale.axis === 'y' ? scale.getPixelForValue(0) : undefined,
          ticks: scale.ticks.map((tick) => ({ value: tick.value, label: tick.label })),
        },
      ])
    ),
  };
}

function snapshot() {
  if (!window.Chart || !Object.keys(Chart.instances).length) {
    throw new Error('Report has no Chart.js instances');
  }
  return Object.values(Chart.instances).map(chartState);
}

function settled() {
  if (document.fonts.status !== 'loaded') {
    previous = undefined;
    return false;
  }
  const state = snapshot();
  if (
    state.some((chart) =>
      chart.datasets.some((series) =>
        series.elements.some(
          (element) => JSON.stringify(element.current) !== JSON.stringify(element.target)
        )
      )
    )
  ) {
    previous = undefined;
    return false;
  }
  const value = JSON.stringify(state);
  if (!previous || previous.value !== value) {
    previous = { value, since: performance.now() };
    return false;
  }
  return performance.now() - previous.since >= 500;
}

window.burndownReportProbe = {
  snapshot,
  settled,
  reset: () => {
    previous = undefined;
  },
};
