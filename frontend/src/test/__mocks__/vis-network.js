// Mock for vis-network used in Jest tests
class DataSet {
  constructor(data = []) {
    this.data = Array.isArray(data) ? [...data] : [];
    this.listeners = [];
  }

  get() {
    return this.data;
  }

  getIds() {
    return this.data.map(item => item.id);
  }

  add(data) {
    if (Array.isArray(data)) {
      this.data.push(...data);
    } else {
      this.data.push(data);
    }
    this._triggerEvent('add', { items: Array.isArray(data) ? data.map(d => d.id) : [data.id] });
  }

  update(data) {
    if (Array.isArray(data)) {
      data.forEach(item => {
        const index = this.data.findIndex(d => d.id === item.id);
        if (index >= 0) {
          this.data[index] = { ...this.data[index], ...item };
        }
      });
    } else {
      const index = this.data.findIndex(d => d.id === data.id);
      if (index >= 0) {
        this.data[index] = { ...this.data[index], ...data };
      }
    }
    this._triggerEvent('update', { items: Array.isArray(data) ? data.map(d => d.id) : [data.id] });
  }

  remove(ids) {
    const idsArray = Array.isArray(ids) ? ids : [ids];
    this.data = this.data.filter(item => !idsArray.includes(item.id));
    this._triggerEvent('remove', { items: idsArray });
  }

  clear() {
    this.data = [];
    this._triggerEvent('clear');
  }

  on(event, callback) {
    this.listeners.push({ event, callback });
  }

  off(event, callback) {
    this.listeners = this.listeners.filter(l => l.event !== event || l.callback !== callback);
  }

  _triggerEvent(event, data) {
    this.listeners
      .filter(l => l.event === event)
      .forEach(l => l.callback(data));
  }
}

class Network {
  constructor(container, data, options = {}) {
    this.container = container;
    this.data = data;
    this.options = options;
    this.listeners = [];
    this.destroyed = false;
    
    // Mock the DOM manipulation
    if (container && typeof container.appendChild === 'function') {
      const canvas = document.createElement('canvas');
      canvas.setAttribute('data-testid', 'vis-network-canvas');
      container.appendChild(canvas);
    }
  }

  setData(data) {
    this.data = data;
    this._triggerEvent('stabilized');
  }

  setOptions(options) {
    this.options = { ...this.options, ...options };
  }

  on(event, callback) {
    this.listeners.push({ event, callback });
  }

  off(event, callback) {
    this.listeners = this.listeners.filter(l => l.event !== event || l.callback !== callback);
  }

  once(event, callback) {
    const wrappedCallback = (data) => {
      callback(data);
      this.off(event, wrappedCallback);
    };
    this.on(event, wrappedCallback);
  }

  fit(options = {}) {
    // Mock implementation
  }

  focus(nodeId, options = {}) {
    // Mock implementation
  }

  getScale() {
    return 1.0;
  }

  getViewPosition() {
    return { x: 0, y: 0 };
  }

  moveTo(options) {
    // Mock implementation
  }

  redraw() {
    // Mock implementation
  }

  setSize(width, height) {
    // Mock implementation
  }

  canvasToDOM(position) {
    return position;
  }

  DOMtoCanvas(position) {
    return position;
  }

  selectNodes(nodeIds, highlightEdges = true) {
    this._triggerEvent('selectNode', { 
      nodes: Array.isArray(nodeIds) ? nodeIds : [nodeIds],
      edges: highlightEdges ? [] : []
    });
  }

  selectEdges(edgeIds) {
    this._triggerEvent('selectEdge', { 
      edges: Array.isArray(edgeIds) ? edgeIds : [edgeIds]
    });
  }

  unselectAll() {
    this._triggerEvent('deselectNode', { nodes: [] });
    this._triggerEvent('deselectEdge', { edges: [] });
  }

  getSelectedNodes() {
    return [];
  }

  getSelectedEdges() {
    return [];
  }

  getNodeAt(position) {
    return undefined;
  }

  getEdgeAt(position) {
    return undefined;
  }

  getConnectedNodes(nodeId) {
    return [];
  }

  getConnectedEdges(nodeId) {
    return [];
  }

  destroy() {
    this.destroyed = true;
    this.listeners = [];
    if (this.container && this.container.firstChild) {
      this.container.removeChild(this.container.firstChild);
    }
  }

  _triggerEvent(event, data = {}) {
    this.listeners
      .filter(l => l.event === event)
      .forEach(l => {
        try {
          l.callback(data);
        } catch (error) {
          console.warn('Error in vis-network mock event callback:', error);
        }
      });
  }
}

// CommonJS exports for Jest compatibility
module.exports = {
  Network,
  DataSet,
  Options: {}
};

// Also support named exports
module.exports.Network = Network;
module.exports.DataSet = DataSet;
module.exports.Options = {}; 