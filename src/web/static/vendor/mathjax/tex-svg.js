(function () {
  function shouldSkipNode(node) {
    const parent = node.parentElement;
    if (!parent) {
      return true;
    }
    return Boolean(parent.closest("pre, code, script, style, .math-render"));
  }

  function renderTextNode(node) {
    if (shouldSkipNode(node)) {
      return;
    }

    const text = node.nodeValue || "";
    const pattern = /\\\[((?:.|\n)*?)\\\]|\\\(((?:.|\n)*?)\\\)/g;
    if (!pattern.test(text)) {
      return;
    }

    pattern.lastIndex = 0;
    const fragment = document.createDocumentFragment();
    let lastIndex = 0;
    let match;

    while ((match = pattern.exec(text)) !== null) {
      if (match.index > lastIndex) {
        fragment.append(document.createTextNode(text.slice(lastIndex, match.index)));
      }

      const isDisplay = match[1] !== undefined;
      const math = document.createElement("span");
      math.className = isDisplay
        ? "math-render math-display"
        : "math-render math-inline";
      math.textContent = (isDisplay ? match[1] : match[2]).trim();
      fragment.append(math);
      lastIndex = pattern.lastIndex;
    }

    if (lastIndex < text.length) {
      fragment.append(document.createTextNode(text.slice(lastIndex)));
    }

    node.replaceWith(fragment);
  }

  function typesetElement(root) {
    const target = root || document.body;
    const walker = document.createTreeWalker(
      target,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode(node) {
          return shouldSkipNode(node)
            ? NodeFilter.FILTER_REJECT
            : NodeFilter.FILTER_ACCEPT;
        },
      }
    );

    const nodes = [];
    while (walker.nextNode()) {
      nodes.push(walker.currentNode);
    }
    nodes.forEach(renderTextNode);
  }

  window.MathJax = window.MathJax || {};
  window.MathJax.typesetPromise = function (elements) {
    return new Promise((resolve) => {
      (elements && elements.length ? elements : [document.body]).forEach(typesetElement);
      resolve();
    });
  };
})();
