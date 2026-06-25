fetch("../poshmark_data.json")
  .then(response => response.json())
  .then(data => {

    const grid = document.getElementById("grid");

    data.forEach(item => {

      const image =
        item.images &&
        item.images.length > 0
          ? item.images[0]
          : "";

      const card = document.createElement("div");

      card.className = "card";

      card.innerHTML = `
        <a href="${item.url}" target="_blank">

          <img src="${image}" alt="">

          <div class="content">

            <div class="title">
              ${item.title || ""}
            </div>

            <div class="price">
              ${item.price || ""}
            </div>

            <div class="date">
              First seen:
              ${item.first_seen || ""}
            </div>

          </div>

        </a>
      `;

      grid.appendChild(card);

    });

  });
