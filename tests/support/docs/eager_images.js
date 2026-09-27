async () => {
  const images = [...document.querySelectorAll('img')];
  images.forEach((image) => { image.loading = 'eager'; });
  await Promise.all(images.map((image) => image.decode().catch(() => null)));
}
