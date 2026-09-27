() => {
  const head = [...document.querySelectorAll('h2')]
    .find((h) => h.textContent.trim().startsWith('📸'));
  let node = head, found = 0;
  while ((node = node.nextElementSibling)) {
    if (node.classList.contains('shots') && ++found === 2) {
      return node.getBoundingClientRect().bottom + window.scrollY + 12;
    }
  }
  return null;
}
