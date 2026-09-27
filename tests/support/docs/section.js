([marker, endMarker]) => {
  const heads = [...document.querySelectorAll('h2')];
  const start = heads.find((h) => h.textContent.trim().startsWith(marker));
  let end = null;
  if (endMarker === 'NEXT') {
    const next = heads[heads.indexOf(start) + 1];
    end = next ? next.getBoundingClientRect().top + window.scrollY - 16 : null;
  } else if (endMarker) {
    const other = heads.find((h) => h.textContent.trim().startsWith(endMarker));
    end = other.getBoundingClientRect().top + window.scrollY - 16;
  }
  const main = document.querySelector('main').getBoundingClientRect();
  const top = start.getBoundingClientRect().top + window.scrollY - 12;
  if (end === null) end = document.body.scrollHeight - 40;
  return {x: main.left - 16, y: top, width: main.width + 32, height: end - top};
}
