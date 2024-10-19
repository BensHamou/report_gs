var bootstrap5 = (function (t, e) {
    "use strict";
    class s {
      static getInstance(t) {
        return this.map.get(t);
      }
      static getOrCreateInstance(t) {
        let e = this.map.get(t);
        return e || ((e = new s(t)), this.map.set(t, e)), e;
      }
      constructor(t) {
        (this.mutable = !1),
          (this.count = 0),
          (this.getValue = () => (0 === this.count ? "" : this.count.toString())),
          (this.onClick = () => {
            this.input.focus();
          }),
          (this.onKeyDown = (t) => {
            switch (t.key) {
              case "Enter":
                0 !== this.input.value.length &&
                  (t.preventDefault(), this.addItem());
                break;
              case "Backspace":
                0 === this.input.value.length && this.removeItem();
                break;
              case "ArrowDown":
                this.nextItem();
                break;
              case "ArrowUp":
                this.nextItem(!0);
            }
          }),
          (this.onFocusIn = () => {
            this.element.classList.add("focus");
          }),
          (this.onFocusOut = () => {
            this.element.classList.remove("focus");
          }),
          (this.onInput = (t) => {
            const e = [],
              s = this.normalize(this.input.value),
              i = this.list ? this.list.options : this.select.options;
            if (s.length > 0)
              for (const t of i)
                if (!t.selected) {
                  if (this.normalize(t.label).includes(s)) {
                    const s = document.createElement("button");
                    (s.type = "button"),
                      (s.innerText = t.label),
                      (s.dataset.value = t.value),
                      (s.dataset.label = t.label),
                      s.classList.add("dropdown-item"),
                      s.addEventListener("click", this.onItemClick),
                      e.push(s);
                  }
                }
            0 === e.length
              ? (this.dropdown.hide(), this.menu.replaceChildren())
              : (e.sort((t, e) => t.dataset.label.localeCompare(e.dataset.label)),
                this.menu.replaceChildren(...e),
                this.dropdown.show());
          }),
          (this.onShowBsDropdown = (t) => {
            0 === this.menu.children.length && t.preventDefault();
          }),
          (this.onShownBsDropdown = (t) => {
            this.menu.scroll(0, 0);
          }),
          (this.onItemClick = (t) => {
            const e = t.target,
              s = e.dataset.label,
              i = e.dataset.value;
            this.setSelected(i),
              this.addTag(s, i),
              this.resetInput(),
              this.dispatchChanged();
          }),
          (this.element = t),
          (this.input = this.element.querySelector("input")),
          (this.select = this.element.querySelector("select")),
          (this.menu = this.element.querySelector(".dropdown-menu")),
          (this.dropdown = e.Dropdown.getOrCreateInstance(this.input)),
          (this.input.autocomplete = "off"),
          (this.mutable =
            "" === this.element.dataset.mutable ||
            "true" === this.element.dataset.mutable);
        const i = this.element.dataset.list;
        i && (this.list = document.getElementById(i)),
          Object.defineProperty(this.element, "value", { get: this.getValue }),
          this.input.addEventListener("input", this.debounce(this.onInput.bind(this)));
          this.input.addEventListener("click", this.onClick.bind(this));
          this.input.addEventListener("keydown", this.onKeyDown.bind(this));
          this.input.addEventListener("focusin", this.onFocusIn.bind(this));
          this.input.addEventListener("focusout", this.onFocusOut.bind(this));
          this.input.addEventListener("show.bs.dropdown", this.onShowBsDropdown.bind(this));
          this.input.addEventListener("shown.bs.dropdown", this.onShownBsDropdown.bind(this));
          
          this.input.addEventListener(
            "shown.bs.dropdown",
            this.onShownBsDropdown
          ),
          this.element.addEventListener("click", this.onClick),
          s.map.set(this.element, this),
          this.update();
      }
      update() {
        this.element
          .querySelectorAll(".option")
          .forEach((t) => this.removeTag(t));
        for (const t of this.select.selectedOptions)
          this.addTag(t.label, t.value);
      }

      addTag(t, e = "") {
        const tagSpan = document.createElement("span");
        tagSpan.classList.add("option");
        tagSpan.dataset.label = t;
        tagSpan.dataset.value = e || t;
    
        const closeButtonContainer = document.createElement("span");
        closeButtonContainer.classList.add("position-absolute", "top-0", "start-100", "translate-middle", "badge", "rounded-pill");
        closeButtonContainer.style.backgroundColor = "#d80000";
        closeButtonContainer.style.cursor = "pointer"; // Set the cursor to pointer on hover
    
        const closeButton = document.createElement("span");
        closeButton.innerHTML = "x";
        closeButton.style.color = "white";
        closeButton.style.fontSize = "10px";
    
        closeButton.addEventListener("click", () => this.removeItem(tagSpan));
    
        closeButtonContainer.appendChild(closeButton);
    
        const tagTextSpan = document.createElement("span");
        tagTextSpan.innerText = t;
    
        tagSpan.appendChild(tagTextSpan);
        tagSpan.appendChild(closeButtonContainer);
    
        this.count++;
        this.element.insertBefore(tagSpan, this.input);
      }
    

      
      removeTag(t) {
        this.count--, t.remove();
      }
      resetInput() {
        (this.input.value = ""), this.menu.replaceChildren();
      }
      dispatchChanged() {
        this.element.dispatchEvent(new CustomEvent("changed.bs5.select")),
          this.element.dispatchEvent(new CustomEvent("input"));
      }
      normalize(t) {
        return t
          .trim()
          .toUpperCase()
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "");
      }
      setSelected(t, e = !0) {
        let s = Array.from(this.select.options).find((e) => e.value === t);
        if (!s && this.list) {
          const e = Array.from(this.list.options).find((e) => e.value === t);
          (s = e.cloneNode(!0)), this.select.options.add(s);
        }
        s.selected = e;
      }
      addItem() {
        const t = this.getActive();
        if (t) {
          const e = t.dataset.label,
            s = t.dataset.value;
          this.addTag(e, s), this.setSelected(s);
        } else if (this.mutable) {
          const t = this.input.value,
            e = Array.from(this.select.options).find(
              (e) => e.value.trim() === t.trim()
            );
          if (e) e.selected || (this.addTag(t), this.setSelected(t));
          else {
            const e = document.createElement("option");
            (e.value = t),
              (e.label = t),
              this.select.options.add(e),
              this.addTag(t),
              this.setSelected(t);
          }
        }
        this.dispatchChanged(), this.resetInput(), this.dropdown.hide();
      }
      removeItem() {
        const clickedTag = event.target.closest('.option');
        if (clickedTag) {
            this.removeTag(clickedTag);
            this.setSelected(clickedTag.dataset.value, false);
            this.dispatchChanged();
        }
      }
      nextItem(t = !1) {
        const e = this.getActive();
        if (e) {
          e.classList.remove("active");
          const s = t ? e.previousElementSibling : e.nextElementSibling;
          if (s)
            return (
              s.classList.add("active"),
              void s.scrollIntoView({ block: "nearest" })
            );
        }
        const s = t ? this.menu.lastElementChild : this.menu.firstElementChild;
        s && (s.classList.add("active"), s.scrollIntoView({ block: "nearest" }));
      }
      getActive() {
        return this.menu.querySelector(".active");
      }
      debounce(t, e = 250) {
        let s;
        return (...i) => {
          clearTimeout(s), (s = setTimeout(() => t(...i), e));
        };
      }
    }
    return (s.map = new WeakMap()), (t.Select = s), t;
  })({}, bootstrap);
  //# sourceMappingURL=select.js.map
  