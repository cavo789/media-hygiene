() => {
  const group = document.querySelector('.group');
  return group.getBoundingClientRect().bottom + window.scrollY + 16;
}
