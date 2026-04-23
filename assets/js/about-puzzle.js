(function () {
  function intersects(rectA, rectB) {
    const centerX = rectA.left + rectA.width / 2;
    const centerY = rectA.top + rectA.height / 2;
    return centerX >= rectB.left && centerX <= rectB.right && centerY >= rectB.top && centerY <= rectB.bottom;
  }

  function init() {
    const puzzle = document.querySelector("[data-about-puzzle]");
    if (!puzzle) return;

    const header = document.querySelector(".site-header");
    const footer = document.querySelector(".site-footer");
    const sceneWrap = puzzle.querySelector(".about-puzzle__scene");
    const scene = puzzle.querySelector("[data-puzzle-scene]");
    const source = puzzle.querySelector("[data-puzzle-source]");
    const stone = puzzle.querySelector("[data-puzzle-stone]");
    const target = puzzle.querySelector("[data-puzzle-target]");
    const successUrl = puzzle.getAttribute("data-success-url") || "/aboutme/profile/";
    const emptyScene = puzzle.getAttribute("data-scene-empty") || scene.getAttribute("src") || "";
    const pickedScene = puzzle.getAttribute("data-scene-picked") || emptyScene;
    const sceneRatio = 1536 / 1024;

    let dragging = false;
    let pointerId = null;
    let offsetX = 0;
    let offsetY = 0;
    let solved = false;

    function layoutScene() {
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      const headerHeight = header ? header.offsetHeight : 0;
      const footerHeight = footer ? footer.offsetHeight : 0;
      const availableHeight = Math.max(280, viewportHeight - headerHeight - footerHeight);

      let width = viewportWidth;
      let height = width / sceneRatio;

      if (height > availableHeight) {
        height = availableHeight;
        width = height * sceneRatio;
      }

      sceneWrap.style.width = `${Math.floor(width)}px`;
      sceneWrap.style.height = `${Math.floor(height)}px`;
    }

    function resetStone() {
      dragging = false;
      pointerId = null;
      stone.hidden = true;
      stone.classList.remove("is-dragging");
      stone.style.left = "";
      stone.style.top = "";
      stone.style.width = "";
      scene.setAttribute("src", emptyScene);
      puzzle.classList.remove("is-picked");
      source.disabled = false;
    }

    function solve() {
      if (solved) return;
      solved = true;
      stone.hidden = true;
      stone.classList.remove("is-dragging");
      puzzle.classList.add("is-solved");
      source.disabled = true;
      window.setTimeout(() => {
        window.location.href = successUrl;
      }, 1600);
    }

    function onPointerMove(event) {
      if (!dragging || event.pointerId !== pointerId || solved) return;
      stone.style.left = `${event.clientX - offsetX}px`;
      stone.style.top = `${event.clientY - offsetY}px`;
    }

    function teardownPointerListeners() {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("pointercancel", onPointerUp);
    }

    function onPointerUp(event) {
      if (!dragging || event.pointerId !== pointerId) return;

      const stoneRect = stone.getBoundingClientRect();
      const targetRect = target.getBoundingClientRect();

      teardownPointerListeners();

      if (intersects(stoneRect, targetRect)) {
        solve();
      } else {
        resetStone();
      }
    }

    source.addEventListener("pointerdown", (event) => {
      if (solved) return;
      event.preventDefault();

      const rect = source.getBoundingClientRect();
      dragging = true;
      pointerId = event.pointerId;
      offsetX = event.clientX - rect.left;
      offsetY = event.clientY - rect.top;

      scene.setAttribute("src", pickedScene);
      puzzle.classList.add("is-picked");
      source.disabled = true;

      stone.hidden = false;
      stone.classList.add("is-dragging");
      stone.style.width = `${rect.width}px`;
      stone.style.left = `${rect.left}px`;
      stone.style.top = `${rect.top}px`;

      window.addEventListener("pointermove", onPointerMove);
      window.addEventListener("pointerup", onPointerUp);
      window.addEventListener("pointercancel", onPointerUp);
    });

    layoutScene();
    window.addEventListener("resize", layoutScene);
  }

  window.addEventListener("DOMContentLoaded", init);
})();
