console.log("✅ app.js loaded");

const AUTH_URL = "";
const PRODUCT_URL = "";
const ORDER_URL = "";

// ================= JWT AUTH HEADERS =================
function authHeaders() {
    const token = localStorage.getItem("access");

    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
    };
}

// ================= REGISTER =================
function registerUser() {
    fetch(`/api/auth/register/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            username: document.getElementById("username").value,
            password: document.getElementById("password").value,
            role: document.getElementById("role").value
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            alert(data.message);
            window.location.href = "/login/";
        }
    });
}

// ================= LOGIN =================
function loginUser() {
    fetch(`/api/auth/login/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            username: document.getElementById("username").value,
            password: document.getElementById("password").value
        })
    })
    .then(res => res.json())
    .then(data => {

        if (data.error) {
            alert(data.error);
            return;
        }

        localStorage.setItem("access", data.access);
        localStorage.setItem("refresh", data.refresh);

        localStorage.setItem("user", JSON.stringify({
            id: data.id,
            username: data.username,
            role: data.role
        }));

        alert("Login successful");
        window.location.href = "/dashboard/";
    })
    .catch(error => {
        console.error(error);
        alert("Login failed");
    });
}

// ================= LOGOUT =================
function logoutUser() {
    localStorage.removeItem("user");
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");

    window.location.href = "/login/";
}

// ================= ADD TO CART =================
function addToCart(productId) {

    let user = JSON.parse(localStorage.getItem("user"));

    if (!user) {
        alert("Please login first");
        return;
    }

    fetch(`/api/orders/`, {
        method: "POST",
        headers: authHeaders(),
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

    await fetch(`/api/orders/`, {
        method: "POST",
        headers: authHeaders(),
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

        const response = await fetch(`/api/checkout/${user.id}/`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({
                items: selectedItems
            })
        });

        const data = await response.json();

        if (data.error) {
            alert(data.error);
        } else {
            alert(data.message);
            window.location.href = "/orders/";
        }

    } catch (error) {
        console.error("Checkout error:", error);
    }
}

// ================= PLACE ORDER =================
async function placeOrder() {

    let user = JSON.parse(localStorage.getItem("user"));

    if (!user) {
        alert("Please login first");
        return;
    }

    const params = new URLSearchParams(window.location.search);
    const productId = params.get("product_id");

    if (!productId) {
        alert("No product selected");
        return;
    }

    await fetch(`/api/orders/`, {
        method: "POST",
        headers: authHeaders(),
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

    try {

        const response = await fetch(`/api/cart/${orderId}/`, {
            method: "DELETE",
            headers: authHeaders()
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

// ================= UPDATE QUANTITY =================
async function updateQuantity(orderId, action) {

    try {

        const response = await fetch(`/api/cart/update/${orderId}/`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({
                action: action
            })
        });

        const data = await response.json();

        if (data.error) {
            alert(data.error);
        } else {
            loadCart();
        }

    } catch (error) {
        console.error("Quantity update error:", error);
    }
}