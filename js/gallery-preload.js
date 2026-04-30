/*
  Gallery cache-warmer.

  Included on every page EXCEPT /gallery.html. Fires after the host
  page is fully rendered (window.load) and the browser is idle, then
  silently fetches every photo the gallery uses. Each fetch lands in
  the browser's HTTP cache so when the visitor opens /gallery.html,
  the photos are already there and paint instantly.

  No quality reduction — these are the same full-resolution files the
  gallery itself requests. We just request them earlier.
*/
(function() {
  if (!('addEventListener' in window)) return;
  // Skip preloading on the gallery page itself (defensive, in case the
  // script ends up included there by mistake).
  if (/\/gallery\.html(\?|$|#)/.test(window.location.pathname)) return;

  const galleryUrls = [
    // Interior & Exterior — reading order (top-of-fold first).
    'images/exterior/_DSC0964-twilight.jpg',
    'images/interior/DSC03198.jpg',
    'images/exterior/_DSC1517.jpg',
    'images/interior/_DSC1457.jpg',
    'images/exterior/_DSC1542.jpg',
    'images/interior/_DSC1487.jpg',
    'images/exterior/DSC03249.jpg',
    'images/interior/_DSC1481.jpg',
    'images/interior/DSC05344.jpg',
    'images/interior/_DSC1448.jpg',
    'images/exterior/_DSC1505.jpg',
    'images/exterior/Twilight-1.jpg',
    'images/exterior/_DSC1496.jpg',
    'images/interior/DSC03174.jpg',
    'images/interior/DSC05368.jpg',
    // Drone & Aerial.
    'images/aerial/Bert-Smith-Subaru-Drone-21.png',
    'images/aerial/Bert-Smith-Subaru-Drone-15.png',
    'images/aerial/DJI_0030.jpg',
    'images/aerial/Bert-Smith-Subaru-Drone-17.png',
    'images/aerial/DJI_0974-Enhanced-NR.jpg',
    'images/aerial/DJI_0980-Enhanced-NR.jpg',
    'images/aerial/Bert-Smith-Subaru-Drone-19.png',
    'images/aerial/Bert-Smith-Subaru-Drone-13.png',
    'images/aerial/Bert-Smith-Subaru-Drone-18.png',
    'images/aerial/DJI_0978-Enhanced-NR.jpg',
    'images/aerial/Bert-Smith-Subaru-Drone-20.png',
    'images/aerial/Bert-Smith-Subaru-Drone-14.png',
    'images/aerial/DJI_0976-Enhanced-NR.jpg',
    'images/aerial/Bert-Smith-Subaru-Drone-16.png',
    'images/aerial/Bert-Smith-Subaru-Drone-12.png'
  ];

  function preload() {
    galleryUrls.forEach(function(url) {
      const img = new Image();
      img.decoding = 'async';
      img.src = url;
    });
  }

  function schedule() {
    if ('requestIdleCallback' in window) {
      requestIdleCallback(preload, { timeout: 3000 });
    } else {
      setTimeout(preload, 1200);
    }
  }

  if (document.readyState === 'complete') {
    schedule();
  } else {
    window.addEventListener('load', schedule);
  }
})();
