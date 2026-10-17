const maximize = document.querySelector(".maximize");
if (maximize) {
  maximize.hidden = false;
  maximize.addEventListener("click", () => {
    const expanded = document.body.classList.toggle("window-maximized");
    maximize.setAttribute("aria-pressed", String(expanded));
    maximize.setAttribute("aria-label", expanded ? "Restore window" : "Maximize window");
  });
}

const search = document.querySelector("#publication-search");
if (search) {
  search.closest(".search-control").hidden = false;
  const papers = [...document.querySelectorAll(".publication")];
  const groups = [...document.querySelectorAll(".publication-group")];
  const count = document.querySelector("#publication-count");
  search.addEventListener("input", () => {
    const terms = search.value.toLocaleLowerCase().trim().split(/\s+/);
    let visible = 0;
    for (const paper of papers) {
      const text = paper.textContent.toLocaleLowerCase();
      paper.hidden = !terms.every((term) => text.includes(term));
      if (!paper.hidden) visible += 1;
    }
    for (const group of groups) {
      group.hidden = ![...group.querySelectorAll(".publication")].some((paper) => !paper.hidden);
    }
    count.textContent = `${visible} ${visible === 1 ? "publication" : "publications"}`;
    document.querySelector("#no-results").hidden = visible !== 0;
  });
}
