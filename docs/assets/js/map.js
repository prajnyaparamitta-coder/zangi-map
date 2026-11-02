/* 地図（Leaflet + OpenStreetMap）と、トップの動画の切り替えだけを受け持つ */
(function () {
  "use strict";
  var mapEl = document.getElementById("map");
  var dataEl = document.getElementById("shops-data");
  if (!mapEl || !dataEl || !window.L) return;

  var shops = JSON.parse(dataEl.textContent);
  var root = mapEl.getAttribute("data-root") || "./";
  var isTop = document.body.classList.contains("is-top");

  var map = L.map(mapEl, { scrollWheelZoom: isTop, tap: true });
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  function icon(active) {
    return L.divIcon({ className: "pin" + (active ? " is-active" : ""), html: "<span></span>", iconSize: [22, 22], iconAnchor: [11, 11] });
  }

  var markers = {};
  shops.forEach(function (s) {
    var m = L.marker([s.lat, s.lon], { icon: icon(false), title: s.name, keyboard: true }).addTo(map);
    markers[s.id] = m;
    if (isTop) {
      m.on("click", function () { select(s, false); });
    } else if (shops.length > 1) {
      m.bindPopup('<a href="' + root + s.path + '">' + escapeHtml(s.name) + "</a>");
    }
  });

  if (shops.length === 1) {
    map.setView([shops[0].lat, shops[0].lon], 17);
    markers[shops[0].id].setIcon(icon(true));
  } else {
    map.fitBounds(L.latLngBounds(shops.map(function (s) { return [s.lat, s.lon]; })), { padding: [24, 24], maxZoom: 15 });
  }

  if (!isTop) return;

  /* ここからトップページだけ：動画の切り替えとランダム再生 */
  var current = null, random = false, player = null, apiReady = false;
  var el = {
    town: document.getElementById("now-town"), name: document.getElementById("now-name"),
    addr: document.getElementById("now-addr"), link: document.getElementById("now-link"),
    random: document.getElementById("btn-random"), next: document.getElementById("btn-next"),
    mode: document.getElementById("now-mode"), slot: document.getElementById("player")
  };


  function embedUrl(id, autoplay) {
    return "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(id) +
      "?enablejsapi=1&playsinline=1&rel=0" + (autoplay ? "&autoplay=1" : "") +
      "&origin=" + encodeURIComponent(location.origin);
  }

  function setVideo(id, autoplay) {
    if (player && apiReady && player.loadVideoById) {
      if (autoplay) player.loadVideoById(id); else player.cueVideoById(id);
      return;
    }
    var iframe = document.createElement("iframe");
    iframe.id = "player";
    iframe.title = "YouTube の動画プレーヤー";
    iframe.allow = "accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture";
    iframe.allowFullscreen = true;
    iframe.referrerPolicy = "strict-origin-when-cross-origin";
    iframe.src = embedUrl(id, autoplay);
    el.slot.replaceWith(iframe);
    el.slot = iframe;
    if (window.YT && window.YT.Player) attachPlayer();
  }

  function attachPlayer() {
    player = new YT.Player(el.slot, {
      events: {
        onReady: function () { apiReady = true; },
        onStateChange: function (e) { if (random && e.data === 0) pickRandom(); }  /* 0 = 再生終了 */
      }
    });
  }

  function select(s, autoplay) {
    if (current) markers[current.id].setIcon(icon(false));
    current = s;
    markers[s.id].setIcon(icon(true));
    el.town.textContent = s.sub + "・" + s.town;
    el.name.textContent = s.name;
    el.addr.textContent = s.addr;
    el.link.href = root + s.path;
    el.link.hidden = false;
    setVideo(s.video, autoplay);
    map.panTo([s.lat, s.lon]);
  }

  function pickRandom() {
    var pool = shops.filter(function (s) { return !current || s.id !== current.id; });
    select(pool[Math.floor(Math.random() * pool.length)], true);
  }

  el.random.addEventListener("click", function () {
    random = !random;
    el.random.setAttribute("aria-pressed", String(random));
    el.next.hidden = !random;
    el.mode.textContent = random ? "ランダム再生中：動画が終わると次の店へ移ります" : "";
    if (random) pickRandom();
  });
  el.next.addEventListener("click", pickRandom);

  /* YouTube の IFrame API は、動画の終わりを知るためだけに読み込む */
  window.onYouTubeIframeAPIReady = function () { if (el.slot.tagName === "IFRAME") attachPlayer(); };
  var tag = document.createElement("script");
  tag.src = "https://www.youtube.com/iframe_api";
  document.head.appendChild(tag);

  /* 開いたときに1店を選んでおく（自動では再生しない） */
  select(shops[Math.floor(Math.random() * shops.length)], false);
  el.mode.textContent = "地図のピンを押すと、店が切り替わります";

  function escapeHtml(t) {
    return String(t).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; });
  }
})();
