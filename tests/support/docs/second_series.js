() => {
  const head = [...document.querySelectorAll('h2')]
    .find((h) => h.textContent.trim().startsWith('📸'));
  let node = head, found = 0;
  while ((node = node.nextElementSibling) && node.tagName !== 'H2') {
    if (node.tagName === 'DETAILS') node.open = true;  // the series sit in a folded list
    const shots = node.classList.contains('shots') ? [node] : [...node.querySelectorAll('.shots')];
    for (const shot of shots) {
      if (++found === 2) return shot.getBoundingClientRect().bottom + window.scrollY + 12;
    }
  }
  return null;
}
