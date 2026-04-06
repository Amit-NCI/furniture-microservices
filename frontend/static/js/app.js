console.log("✅ app.js loaded");

// ================= REGISTER =================
function registerUser() {
    fetch("http://localhost:8001/api/auth/register/", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            username: document.getElementById("username").value,
            password: document.getElementById("password").value,
            role: document.getElementById("role").value
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) alert(data.error);
        else {
            alert(data.message);
            window.location.href = "/login/";
        }
    });
}

// ================= LOGIN =================
function loginUser() {
    fetch("http://localhost:8001/api/auth/login/", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            username: document.getElementById("username").value,
            password: document.getElementById("password").value
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) alert(data.error);
        else {
            // 🔥 FIX: ensure id exists
            data.id = data.id || 1;

            localStorage.setItem("user", JSON.stringify(data));
            alert("Login successful");
            window.location.href = "/dashboard/";
        }
    });
}

// ================= LOGOUT =================
function logoutUser() {
    localStorage.removeItem("user");
    window.location.href = "/login/";
}

// ================= ADD TO CART =================
function addToCart(productId) {
    let user = JSON.parse(localStorage.getItem("user"));

    if (!user) {
        alert("Please login first");
        return;
    }

    fetch("http://127.0.0.1:8003/api/orders/", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            user_id: user.id,
            product_id: productId,
            quantity: 1,
            status: "cart"
        })
    })
    .then(() => alert("Added to cart 🛒"));
}

// ================= BUY NOW =================
async function buyNow(productId) {
    let user = JSON.parse(localStorage.getItem("user"));

    if (!user) {
        alert("Please login first");
        return;
    }

    await fetch("http://127.0.0.1:8003/api/orders/", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            user_id: user.id,
            product_id: productId,
            quantity: 1,
            status: "placed"
        })
    });

    alert("Order placed ⚡");
    window.location.href = "/orders/";
}

// ================= LOAD PRODUCTS =================
async function loadProducts() {
    const res = await fetch("http://127.0.0.1:8002/api/products/");
    const products = await res.json();

    let container = document.getElementById("product-list");
    container.innerHTML = "";

    products.forEach(p => {
        container.innerHTML += `
            <div class="product-card">
                <img src="${p.image_url}" width="200"/>
                <h3>${p.name}</h3>
                <p>${p.description}</p>
                <h4>€${p.price}</h4>

                <button onclick="addToCart(${p.id})">Add to Cart 🛒</button>
                <button onclick="buyNow(${p.id})">Buy Now ⚡</button>
            </div>
        `;
    });
}

// ================= CHECKOUT =================
async function checkout() {
    let user = JSON.parse(localStorage.getItem("user"));

    if (!user) {
        alert("Please login first");
        return;
    }

    let selectedItems = [];

    document.querySelectorAll(".select-item").forEach(cb => {
        if (cb.checked) {
            selectedItems.push(cb.dataset.id);
        }
    });

    if (selectedItems.length === 0) {
        alert("Please select at least one item");
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:8003/api/checkout/${user.id || 1}/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                items: selectedItems   // 👈 IMPORTANT
            })
        });

        const data = await response.json();

        if (data.error) {
            alert(data.error);
        } else {
            alert(data.message);

            // reload cart → remaining items still there
            window.location.href = "/orders/";
        }

    } catch (error) {
        console.error("Checkout error:", error);
    }
}

// ================= PLACE ORDER (BUY PAGE) =================
async function placeOrder() {
    let user = JSON.parse(localStorage.getItem("user"));

    const params = new URLSearchParams(window.location.search);
    const productId = params.get("product_id");

    if (!productId) {
        alert("No product selected");
        return;
    }

    await fetch("http://127.0.0.1:8003/api/orders/", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            user_id: user.id,
            product_id: productId,
            quantity: 1,
            status: "placed"
        })
    });

    alert("Order placed 🎉");
    window.location.href = "/orders/";
}

// ================= REMOVE FROM CART =================
async function removeFromCart(orderId) {
    console.log("Removing item:", orderId);

    try {
        const response = await fetch(`http://127.0.0.1:8003/api/cart/${orderId}/`, {
            method: "DELETE"
        });

        const data = await response.json();

        alert(data.message || "Item removed");

        if (typeof loadCart === "function") {
            loadCart();
        }

    } catch (error) {
        console.error("Remove error:", error);
    }
}

// ================= INIT =================
document.addEventListener("DOMContentLoaded", function () {

    if (typeof loadNavbar === "function") loadNavbar();

    if (window.location.pathname === "/dashboard/") {
        loadProducts();

        let user = JSON.parse(localStorage.getItem("user"));
        if (user) {
            let el = document.getElementById("welcome-user");
            if (el) el.innerText = "Hello, " + user.username;
        }
    }
});
// ================= UPDATE QUANTITY =================
async function updateQuantity(orderId, action) {
    try {
        const response = await fetch(`http://127.0.0.1:8003/api/cart/update/${orderId}/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ action: action })
        });

        const data = await response.json();

        if (data.error) {
            alert(data.error);
        } else {
            // 🔥 reload cart to update UI + total
            loadCart();
        }

    } catch (error) {
        console.error("Quantity update error:", error);
    }
}