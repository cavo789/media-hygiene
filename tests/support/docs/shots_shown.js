() => [...document.querySelectorAll("#shots img")].every((image) => image.complete && image.naturalWidth > 0)
