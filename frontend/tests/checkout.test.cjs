const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const template = fs.readFileSync(
    path.join(__dirname, "../templates/checkout.html"),
    "utf8"
);

const match = template.match(/<script>([\s\S]*?)<\/script>/);

if (!match) {
    throw new Error("Checkout inline JavaScript not found.");
}

const checkoutScript = match[1];

test("checkout refuses submission without JWT", async () => {
    const alerts = [];
    const requests = [];

    const button = { disabled: false };

    const context = {
        URLSearchParams,
        window: {
            location: {
                search: "",
                href: "/checkout/"
            }
        },
        document: {
            getElementById(id) {
                if (id === "place-order-btn") {
                    return button;
                }

                return {};
            },
            addEventListener() {},
        },
        localStorage: {
            getItem(key) {
                if (key === "access") {
                    return null;
                }

                return null;
            }
        },
        sessionStorage: {
            getItem() {
                return null;
            },
            removeItem() {}
        },
        alert(message) {
            alerts.push(message);
        },
        async fetch(...args) {
            requests.push(args);
            throw new Error("Unexpected API request");
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    await vm.runInContext("handleCheckout()", context);

    assert.equal(requests.length, 0);
    assert.equal(alerts.length, 1);
    assert.equal(
        alerts[0],
        "Please log in before placing an order."
    );
});


test("checkout refuses submission with empty selected order IDs", async () => {
    const alerts = [];
    const requests = [];

    const button = { disabled: false };

    const context = {
        URLSearchParams,
        window: {
            location: {
                search: "",
                href: "/checkout/"
            }
        },
        document: {
            getElementById(id) {
                if (id === "place-order-btn") {
                    return button;
                }

                return {};
            },
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") {
                    return "mock-jwt-token";
                }

                if (key === "user") {
                    return JSON.stringify({ id: 1 });
                }

                return null;
            }
        },
        sessionStorage: {
            getItem() {
                return null;
            },
            removeItem() {}
        },
        alert(message) {
            alerts.push(message);
        },
        async fetch(...args) {
            requests.push(args);
            throw new Error("Unexpected API request");
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    // Simulate an empty cart selection.
    vm.runInContext("selectedOrderIds = []", context);

    await vm.runInContext("handleCheckout()", context);

    assert.equal(requests.length, 0);

    assert.deepEqual(alerts, [
        "No valid items selected for checkout."
    ]);
});

test("checkout sends selected order IDs with JWT authentication", async () => {
    const requests = [];
    const alerts = [];
    const removedKeys = [];
    const button = { disabled: false };

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                Authorization: "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "",
                href: "/checkout/"
            }
        },
        document: {
            getElementById(id) {
                if (id === "place-order-btn") {
                    return button;
                }
                return {};
            },
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") {
                    return "mock-jwt-token";
                }
                if (key === "user") {
                    return JSON.stringify({ id: 1 });
                }
                return null;
            }
        },
        sessionStorage: {
            getItem() {
                return null;
            },
            removeItem(key) {
                removedKeys.push(key);
            }
        },
        alert(message) {
            alerts.push(message);
        },
        async fetch(url, options) {
            requests.push({ url, options });

            return {
                ok: true,
                status: 200,
                async json() {
                    return {
                        message: "Order placed successfully."
                    };
                }
            };
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    // These are cart order IDs, not product IDs.
    vm.runInContext("selectedOrderIds = [12, 15]", context);

    await vm.runInContext("handleCheckout()", context);

    assert.equal(requests.length, 1);

    const request = requests[0];

    assert.equal(request.url, "/api/checkout/1/");
    assert.equal(request.options.method, "POST");

    assert.equal(
        request.options.headers.Authorization,
        "Bearer mock-jwt-token"
    );

    assert.equal(
        request.options.headers["Content-Type"],
        "application/json"
    );

    assert.deepEqual(
        JSON.parse(request.options.body),
        { items: [12, 15] }
    );

    assert.deepEqual(
        removedKeys,
        ["checkoutSelectedItems"]
    );

    assert.deepEqual(
        alerts,
        ["Order placed successfully."]
    );

    assert.equal(
        context.window.location.href,
        "/orders/"
    );

    assert.equal(button.disabled, true);
});

test("checkout handles backend HTTP errors without reporting success", async () => {
    const requests = [];
    const alerts = [];
    const removedKeys = [];
    const button = { disabled: false };

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                Authorization: "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "",
                href: "/checkout/"
            }
        },
        document: {
            getElementById(id) {
                if (id === "place-order-btn") {
                    return button;
                }
                return {};
            },
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") {
                    return "mock-jwt-token";
                }
                if (key === "user") {
                    return JSON.stringify({ id: 1 });
                }
                return null;
            }
        },
        sessionStorage: {
            getItem() {
                return null;
            },
            removeItem(key) {
                removedKeys.push(key);
            }
        },
        alert(message) {
            alerts.push(message);
        },
        async fetch(url, options) {
            requests.push({ url, options });

            return {
                ok: false,
                status: 404,
                async json() {
                    return {
                        error: "Selected items not found"
                    };
                }
            };
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    vm.runInContext("selectedOrderIds = [12, 15]", context);

    await vm.runInContext("handleCheckout()", context);

    assert.equal(requests.length, 1);

    assert.deepEqual(
        alerts,
        ["Selected items not found"]
    );

    assert.equal(
        context.window.location.href,
        "/checkout/"
    );

    assert.deepEqual(removedKeys, []);

    assert.equal(button.disabled, false);
});

test("checkout prevents immediate retry after uncertain network failure", async () => {
    const requests = [];
    const alerts = [];
    const removedKeys = [];
    const button = { disabled: false };

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                Authorization: "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "",
                href: "/checkout/"
            }
        },
        document: {
            getElementById(id) {
                if (id === "place-order-btn") {
                    return button;
                }
                return {};
            },
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") {
                    return "mock-jwt-token";
                }
                if (key === "user") {
                    return JSON.stringify({ id: 1 });
                }
                return null;
            }
        },
        sessionStorage: {
            getItem() {
                return null;
            },
            removeItem(key) {
                removedKeys.push(key);
            }
        },
        alert(message) {
            alerts.push(message);
        },
        async fetch(url, options) {
            requests.push({ url, options });

            // Simulate a connection failure after submission.
            throw new Error("Network connection lost");
        },
        console: {
            error() {}
        }
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    vm.runInContext("selectedOrderIds = [12, 15]", context);

    // First checkout attempt.
    await vm.runInContext("handleCheckout()", context);

    assert.equal(requests.length, 1);

    assert.deepEqual(alerts, [
        "Unable to confirm your order. Please check your order history before trying again."
    ]);

    assert.equal(button.disabled, true);

    assert.equal(context.window.location.href, "/checkout/");

    assert.deepEqual(removedKeys, []);

    // Simulate another attempt from the same page.
    await vm.runInContext("handleCheckout()", context);

    // No second API request should be sent.
    assert.equal(requests.length, 1);

    assert.equal(button.disabled, true);
});

test("Buy Now rejects null product response without creating an order", async () => {
    const requests = [];

    const button = { disabled: true };

    const container = {
        innerHTML: "",
        textContent: ""
    };

    const totalAmount = {
        innerText: "",
        textContent: ""
    };

    const context = {
        URLSearchParams,
        PRODUCT_URL: "",
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            getElementById(id) {
                if (id === "place-order-btn") {
                    return button;
                }

                if (id === "checkout-items") {
                    return container;
                }

                if (id === "total-amount") {
                    return totalAmount;
                }

                return {};
            },
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") {
                    return "mock-jwt-token";
                }

                return null;
            }
        },
        sessionStorage: {
            getItem() {
                return null;
            },
            removeItem() {}
        },
        alert() {},
        async fetch(url, options) {
            requests.push({ url, options });

            if (url === "/api/products/5/") {
                return {
                    ok: true,
                    status: 200,
                    async json() {
                        return null;
                    }
                };
            }

            throw new Error("Unexpected API request");
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    await vm.runInContext("loadCheckout()", context);

    assert.equal(
        container.textContent,
        "Invalid product information."
    );

    assert.equal(button.disabled, true);

    assert.equal(requests.length, 1);

    assert.equal(
        requests[0].url,
        "/api/products/5/"
    );

    assert.equal(
        requests[0].options,
        undefined
    );
});

test("Buy Now marks valid product preview ready without placing an order", async () => {
    const requests = [];
    const button = { disabled: true };

    const container = {
        innerHTML: "",
        textContent: ""
    };

    const totalAmount = {
        innerText: "",
        textContent: ""
    };

    const context = {
        URLSearchParams,
        PRODUCT_URL: "",
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            getElementById(id) {
                if (id === "place-order-btn") return button;
                if (id === "checkout-items") return container;
                if (id === "total-amount") return totalAmount;
                return {};
            },
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                return key === "access" ? "mock-jwt-token" : null;
            }
        },
        sessionStorage: {
            getItem() { return null; },
            removeItem() {}
        },
        alert() {},
        async fetch(url, options) {
            requests.push({ url, options });

            if (url !== "/api/products/5/") {
                throw new Error("Unexpected API request");
            }

            return {
                ok: true,
                status: 200,
                async json() {
                    return {
                        id: 5,
                        name: "Office Chair",
                        price: "149.99",
                        description: "Ergonomic office chair",
                        image_url: "/media/chair.jpg"
                    };
                }
            };
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    await vm.runInContext("loadCheckout()", context);

    assert.equal(
        vm.runInContext("buyNowProductReady", context),
        true
    );

    assert.equal(
        vm.runInContext("total", context),
        149.99
    );

    assert.equal(button.disabled, true);

    assert.match(container.innerHTML, /Office Chair/);
    assert.match(container.innerHTML, /149\.99/);

    assert.equal(totalAmount.innerText, "Total: €149.99");

    assert.equal(requests.length, 1);
    assert.equal(requests[0].url, "/api/products/5/");
    assert.equal(requests[0].options, undefined);
});

test("Buy Now refuses submission when product preview is not ready", async () => {
    const requests = [];
    const alerts = [];

    // Enabled deliberately to exercise the readiness guard directly.
    const button = { disabled: false };

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            getElementById(id) {
                if (id === "place-order-btn") return button;
                return {};
            },
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return '{"id":1}';
                return null;
            }
        },
        alert(message) {
            alerts.push(message);
        },
        async fetch(url, options) {
            requests.push({ url, options });
            throw new Error("Unexpected API request");
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    await vm.runInContext("handleCheckout()", context);

    assert.equal(
        vm.runInContext("buyNowProductReady", context),
        false
    );

    assert.deepEqual(alerts, [
        "Product information is not ready. Please try again."
    ]);

    assert.equal(requests.length, 0);
});

test("Buy Now ready product remains blocked until order integration", async () => {
    const requests = [];
    const alerts = [];

    // Enabled deliberately to test the existing submission guard.
    const button = { disabled: false };

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            getElementById(id) {
                if (id === "place-order-btn") return button;
                return {};
            },
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return '{"id":1}';
                return null;
            }
        },
        alert(message) {
            alerts.push(message);
        },
        async fetch(url, options) {
            requests.push({ url, options });
            throw new Error("Unexpected API request");
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    // Simulate a successfully validated product preview.
    vm.runInContext("buyNowProductReady = true", context);

    await vm.runInContext("handleCheckout()", context);

    assert.equal(
        vm.runInContext("buyNowProductReady", context),
        true
    );

    assert.deepEqual(alerts, [
        "Buy Now checkout is not yet available."
    ]);

    assert.equal(requests.length, 0);
});

test("Buy Now blocks retry when order creation outcome is uncertain", async () => {
    const requests = [];
    const alerts = [];

    // Enabled deliberately to exercise the uncertainty guard.
    const button = { disabled: false };

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            getElementById(id) {
                if (id === "place-order-btn") return button;
                return {};
            },
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return '{"id":1}';
                return null;
            }
        },
        alert(message) {
            alerts.push(message);
        },
        async fetch(url, options) {
            requests.push({ url, options });
            throw new Error("Unexpected API request");
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    // Simulate an uncertain previous order-creation outcome.
    vm.runInContext("buyNowProductReady = true", context);
    vm.runInContext("buyNowCreationUncertain = true", context);

    await vm.runInContext("handleCheckout()", context);

    assert.equal(
        vm.runInContext("buyNowCreationUncertain", context),
        true
    );

    assert.deepEqual(alerts, [
        "Unable to confirm whether an order was created. " +
        "Please check your cart and order history before trying again."
    ]);

    assert.equal(requests.length, 0);
});


test("Buy Now idempotency key survives page refresh", () => {
    const values = new Map();
    let generated = 0;

    const storage = {
        getItem(key) {
            return values.has(key) ? values.get(key) : null;
        },
        setItem(key, value) {
            values.set(key, value);
        }
    };

    const cryptoMock = {
        randomUUID() {
            generated++;
            return "123e4567-e89b-42d3-a456-426614174000";
        }
    };

    function createPage() {
        const context = {
            URLSearchParams,
            window: {
                location: {
                    search: "?product_id=5",
                    href: "/checkout/?product_id=5"
                }
            },
            document: {
                addEventListener() {}
            },
            sessionStorage: storage,
            crypto: cryptoMock,
            console
        };

        vm.createContext(context);
        vm.runInContext(checkoutScript, context);
        return context;
    }

    const firstPage = createPage();
    const firstKey = vm.runInContext(
        "prepareBuyNowIdempotencyKey(10, 5)", firstPage
    );

    const refreshedPage = createPage();
    const secondKey = vm.runInContext(
        "prepareBuyNowIdempotencyKey(10, 5)", refreshedPage
    );

    assert.equal(firstKey, secondKey);
    assert.equal(generated, 1);

    const stored = JSON.parse(values.get("buyNowIdempotencyAttempt"));
    assert.deepEqual(stored, {
        userId: 10,
        productId: 5,
        key: firstKey
    });
});

test("Buy Now idempotency key rejects another user or product", () => {
    const values = new Map();
    const context = {
        URLSearchParams,
        window: {
            location: {
                search: "?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        sessionStorage: {
            getItem(key) {
                return values.get(key) ?? null;
            },
            setItem(key, value) {
                values.set(key, value);
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    vm.runInContext("prepareBuyNowIdempotencyKey(10, 5)", context);

    assert.throws(
        () => vm.runInContext(
            "prepareBuyNowIdempotencyKey(11, 5)", context
        ),
        /different or invalid checkout attempt/
    );

    assert.throws(
        () => vm.runInContext(
            "prepareBuyNowIdempotencyKey(10, 6)", context
        ),
        /different or invalid checkout attempt/
    );
});

test("Buy Now idempotency key requires secure storage and UUID generation", () => {
    const context = {
        URLSearchParams,
        window: {
            location: {
                search: "?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    assert.throws(
        () => vm.runInContext(
            "prepareBuyNowIdempotencyKey(10, 5)", context
        ),
        /Secure checkout storage is unavailable/
    );

    context.sessionStorage = {
        getItem() {
            return null;
        },
        setItem() {}
    };

    assert.throws(
        () => vm.runInContext(
            "prepareBuyNowIdempotencyKey(10, 5)", context
        ),
        /Secure checkout key generation is unavailable/
    );
});

test("Buy Now clears a completed checkout attempt only for its owner and product", () => {
    const values = new Map();
    let generated = 0;

    const context = {
        URLSearchParams,
        window: {
            location: {
                search: "?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        sessionStorage: {
            getItem(key) {
                return values.get(key) ?? null;
            },
            setItem(key, value) {
                values.set(key, String(value));
            },
            removeItem(key) {
                values.delete(key);
            }
        },
        crypto: {
            randomUUID() {
                generated++;
                return generated === 1
                    ? "123e4567-e89b-42d3-a456-426614174000"
                    : "123e4567-e89b-42d3-a456-426614174001";
            }
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    const firstKey = vm.runInContext(
        "prepareBuyNowIdempotencyKey(10, 5)", context
    );

    assert.throws(
        () => vm.runInContext(
            "completeBuyNowCheckoutAttempt(11, 5)", context
        ),
        /different checkout attempt/
    );

    assert.equal(
        JSON.parse(values.get("buyNowIdempotencyAttempt")).key,
        firstKey
    );

    assert.throws(
        () => vm.runInContext(
            "completeBuyNowCheckoutAttempt(10, 6)", context
        ),
        /different checkout attempt/
    );

    assert.equal(
        JSON.parse(values.get("buyNowIdempotencyAttempt")).key,
        firstKey
    );

    const storedAttempt = JSON.parse(
        values.get("buyNowIdempotencyAttempt")
    );

    values.set("buyNowIdempotencyAttempt", JSON.stringify({
        ...storedAttempt,
        state: "confirmed",
        orderId: 42
    }));

    vm.runInContext(
        "completeBuyNowCheckoutAttempt(10, 5)", context
    );

    assert.equal(values.has("buyNowIdempotencyAttempt"), false);

    const secondKey = vm.runInContext(
        "prepareBuyNowIdempotencyKey(10, 5)", context
    );

    assert.notEqual(firstKey, secondKey);
    assert.equal(generated, 2);
});

test("Buy Now completion refuses unconfirmed or invalid order attempts", () => {
    const storageKey = "buyNowIdempotencyAttempt";
    const key = "123e4567-e89b-42d3-a456-426614174000";
    const values = new Map();

    const context = {
        URLSearchParams,
        window: {
            location: {
                search: "?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        sessionStorage: {
            getItem(name) {
                return values.get(name) ?? null;
            },
            setItem(name, value) {
                values.set(name, String(value));
            },
            removeItem(name) {
                values.delete(name);
            }
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    const attempts = [
        { userId: 10, productId: 5, key },
        { userId: 10, productId: 5, key, state: "prepared" },
        { userId: 10, productId: 5, key, state: "pending" },
        { userId: 10, productId: 5, key, state: "confirmed" },
        { userId: 10, productId: 5, key, state: "confirmed", orderId: 0 },
        { userId: 10, productId: 5, key, state: "confirmed", orderId: -1 },
        { userId: 10, productId: 5, key, state: "confirmed", orderId: "42" }
    ];

    for (const attempt of attempts) {
        const stored = JSON.stringify(attempt);
        values.set(storageKey, stored);

        assert.throws(
            () => vm.runInContext(
                "completeBuyNowCheckoutAttempt(10, 5)", context
            ),
            /confirmed Buy Now order/,
            `Invalid attempt was accepted: ${stored}`
        );

        assert.equal(
            values.get(storageKey),
            stored,
            "An unconfirmed or invalid attempt must remain stored."
        );
    }

    values.set(storageKey, JSON.stringify({
        userId: 10,
        productId: 5,
        key,
        state: "confirmed",
        orderId: 42
    }));

    vm.runInContext(
        "completeBuyNowCheckoutAttempt(10, 5)", context
    );

    assert.equal(values.has(storageKey), false);
});

test("Buy Now order creation rejects invalid product ID", async () => {
    const requests = [];

    const context = {
        URLSearchParams,
        window: {
            location: {
                search: "?product_id=invalid",
                href: "/checkout/?product_id=invalid"
            }
        },
        document: {
            addEventListener() {}
        },
        async fetch(url, options) {
            requests.push({ url, options });
            throw new Error("Unexpected API request");
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    // Even with a ready preview, an invalid product ID must be rejected.
    vm.runInContext("buyNowProductReady = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Invalid Buy Now product ID."
        }
    );

    assert.equal(requests.length, 0);
});

test("Buy Now order creation rejects unready product preview", async () => {
    const requests = [];

    const context = {
        URLSearchParams,
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        async fetch(url, options) {
            requests.push({ url, options });
            throw new Error("Unexpected API request");
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    // Confirm the preview starts in the unready state.
    assert.equal(
        vm.runInContext("buyNowProductReady", context),
        false
    );

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Buy Now product information is not ready."
        }
    );

    assert.equal(requests.length, 0);
});

test("Buy Now order creation rejects uncertain previous outcome", async () => {
    const requests = [];

    const context = {
        URLSearchParams,
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        async fetch(url, options) {
            requests.push({ url, options });
            throw new Error("Unexpected API request");
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    // Simulate a valid product preview.
    vm.runInContext("buyNowProductReady = true", context);

    // Simulate an uncertain previous order-creation attempt.
    vm.runInContext("buyNowCreationUncertain = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "The previous order-creation outcome is uncertain."
        }
    );

    assert.equal(
        vm.runInContext("buyNowCreationUncertain", context),
        true
    );

    assert.equal(requests.length, 0);
});

test("Buy Now refuses order creation with an invalid user session", async () => {
    const requests = [];

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                Authorization: "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 0 });
                return null;
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });
            throw new Error("Order API must not be called");
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);
    vm.runInContext("buyNowProductReady = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Invalid user session. Please log in again."
        }
    );

    assert.equal(requests.length, 0);
});

test("Buy Now refuses order creation without secure session storage", async () => {
    const requests = [];

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                Authorization: "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 10 });
                return null;
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });
            throw new Error("Order API must not be called");
        },
        console
    };

    // sessionStorage is deliberately unavailable.

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);
    vm.runInContext("buyNowProductReady = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Secure checkout storage is unavailable."
        }
    );

    assert.equal(requests.length, 0);
});

test("Buy Now creates one order and reuses the returned order ID", async () => {
    const requests = [];

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                "Authorization": "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 10 });
                return null;
            }
        },
        sessionStorage: {
            values: new Map(),
            getItem(key) {
                return this.values.has(key) ? this.values.get(key) : null;
            },
            setItem(key, value) {
                this.values.set(key, String(value));
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });

            if (url !== "/api/orders/") {
                throw new Error("Unexpected API request");
            }

            return {
                ok: true,
                status: 200,
                async json() {
                    return {
                        message: "Item added to cart",
                        order_id: 123
                    };
                }
            };
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    vm.runInContext("buyNowProductReady = true", context);

    const firstOrderId = await vm.runInContext(
        "createBuyNowOrder()", context
    );

    assert.equal(firstOrderId, 123);

    assert.equal(
        vm.runInContext("buyNowOrderId", context),
        123
    );

    assert.equal(
        vm.runInContext("buyNowCreationUncertain", context),
        false
    );

    assert.equal(requests.length, 1);
    assert.equal(requests[0].url, "/api/orders/");
    assert.equal(requests[0].options.method, "POST");

    assert.deepEqual(
        JSON.parse(requests[0].options.body),
        {
            product_id: 5,
            quantity: 1
        }
    );

    assert.equal(
        requests[0].options.headers.Authorization,
        "Bearer mock-jwt-token"
    );

    // The order request must include the persistent idempotency key.
    const expectedKey = "123e4567-e89b-42d3-a456-426614174000";

    assert.equal(
        requests[0].options.headers["Idempotency-Key"],
        expectedKey
    );

    const storedAttempt = JSON.parse(
        context.sessionStorage.getItem("buyNowIdempotencyAttempt")
    );

    assert.deepEqual(storedAttempt, {
        userId: 10,
        productId: 5,
        key: expectedKey,
        state: "confirmed",
        orderId: 123
    });

    assert.equal(
        vm.runInContext("prepareBuyNowIdempotencyKey(10, 5)", context),
        expectedKey
    );

    // Calling again must reuse the existing order ID.
    const secondOrderId = await vm.runInContext(
        "createBuyNowOrder()", context
    );

    assert.equal(secondOrderId, 123);

    // No second POST request should be made.
    assert.equal(requests.length, 1);
});

test("Buy Now persists pending state before sending an order request", async () => {
    const values = new Map();
    const requests = [];

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                Authorization: "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 10 });
                return null;
            }
        },
        sessionStorage: {
            getItem(key) {
                return values.get(key) ?? null;
            },
            setItem(key, value) {
                values.set(key, String(value));
            },
            removeItem(key) {
                values.delete(key);
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });

            const attempt = JSON.parse(
                values.get("buyNowIdempotencyAttempt")
            );

            assert.equal(attempt.userId, 10);
            assert.equal(attempt.productId, 5);
            assert.equal(attempt.state, "pending");
            assert.equal(
                attempt.key,
                options.headers["Idempotency-Key"]
            );

            return {
                ok: true,
                status: 200,
                async json() {
                    return { order_id: 123 };
                }
            };
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);
    vm.runInContext("buyNowProductReady = true", context);

    const orderId = await vm.runInContext(
        "createBuyNowOrder()", context
    );

    assert.equal(orderId, 123);
    assert.equal(requests.length, 1);
});

test("Buy Now blocks a pending attempt after page refresh", async () => {
    const storedAttempt = {
        userId: 10,
        productId: 5,
        key: "123e4567-e89b-42d3-a456-426614174000",
        state: "pending"
    };

    const values = new Map([
        ["buyNowIdempotencyAttempt", JSON.stringify(storedAttempt)]
    ]);

    const requests = [];

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                Authorization: "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 10 });
                return null;
            }
        },
        sessionStorage: {
            getItem(key) {
                return values.get(key) ?? null;
            },
            setItem(key, value) {
                values.set(key, String(value));
            },
            removeItem(key) {
                values.delete(key);
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });
            throw new Error("No order request should be sent");
        },
        console
    };

    // A new JavaScript context represents a refreshed checkout page.
    vm.createContext(context);
    vm.runInContext(checkoutScript, context);
    vm.runInContext("buyNowProductReady = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message:
                "A previous Buy Now attempt must be resolved before retrying."
        }
    );

    assert.equal(requests.length, 0);

    assert.deepEqual(
        JSON.parse(values.get("buyNowIdempotencyAttempt")),
        storedAttempt
    );
});

test("Buy Now restores a confirmed order after page refresh", async () => {
    const storedAttempt = {
        userId: 10,
        productId: 5,
        key: "123e4567-e89b-42d3-a456-426614174000",
        state: "confirmed",
        orderId: 123
    };

    const values = new Map([
        ["buyNowIdempotencyAttempt", JSON.stringify(storedAttempt)]
    ]);

    const requests = [];

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                Authorization: "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 10 });
                return null;
            }
        },
        sessionStorage: {
            getItem(key) {
                return values.get(key) ?? null;
            },
            setItem(key, value) {
                values.set(key, String(value));
            },
            removeItem(key) {
                values.delete(key);
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });
            throw new Error("No order request should be sent");
        },
        console
    };

    // A new JavaScript context represents a refreshed checkout page.
    vm.createContext(context);
    vm.runInContext(checkoutScript, context);
    vm.runInContext("buyNowProductReady = true", context);

    const orderId = await vm.runInContext(
        "createBuyNowOrder()", context
    );

    assert.equal(orderId, 123);
    assert.equal(requests.length, 0);

    assert.equal(
        vm.runInContext("buyNowOrderId", context),
        123
    );

    assert.deepEqual(
        JSON.parse(values.get("buyNowIdempotencyAttempt")),
        storedAttempt
    );
});

test("Buy Now rejects invalid confirmed order IDs after refresh", async () => {
    const invalidOrderIds = [
        0,
        -1,
        "123",
        null,
        1.5,
        Number.MAX_SAFE_INTEGER + 1
    ];

    for (const invalidOrderId of invalidOrderIds) {
        const storedAttempt = {
            userId: 10,
            productId: 5,
            key: "123e4567-e89b-42d3-a456-426614174000",
            state: "confirmed",
            orderId: invalidOrderId
        };

        const values = new Map([
            ["buyNowIdempotencyAttempt", JSON.stringify(storedAttempt)]
        ]);

        const requests = [];

        const context = {
            URLSearchParams,
            ORDER_URL: "",
            authHeaders() {
                return {
                    "Content-Type": "application/json",
                    Authorization: "Bearer mock-jwt-token"
                };
            },
            window: {
                location: {
                    search: "?product_id=5",
                    href: "/checkout/?product_id=5"
                }
            },
            document: {
                addEventListener() {}
            },
            localStorage: {
                getItem(key) {
                    if (key === "access") return "mock-jwt-token";
                    if (key === "user") {
                        return JSON.stringify({ id: 10 });
                    }
                    return null;
                }
            },
            sessionStorage: {
                getItem(key) {
                    return values.get(key) ?? null;
                },
                setItem(key, value) {
                    values.set(key, String(value));
                },
                removeItem(key) {
                    values.delete(key);
                }
            },
            crypto: {
                randomUUID() {
                    return "123e4567-e89b-42d3-a456-426614174000";
                }
            },
            async fetch(url, options) {
                requests.push({ url, options });
                throw new Error("No order request should be sent");
            },
            console
        };

        vm.createContext(context);
        vm.runInContext(checkoutScript, context);
        vm.runInContext("buyNowProductReady = true", context);

        await assert.rejects(
            vm.runInContext("createBuyNowOrder()", context),
            {
                message:
                    "The stored confirmed Buy Now order ID is invalid."
            }
        );

        assert.equal(
            requests.length,
            0,
            `Unexpected request for order ID ${invalidOrderId}`
        );

        assert.deepEqual(
            JSON.parse(values.get("buyNowIdempotencyAttempt")),
            storedAttempt
        );
    }
});

test("Buy Now rejects corrupted checkout storage without sending an order", async () => {
    const values = new Map([
        ["buyNowIdempotencyAttempt", "{invalid-json"]
    ]);

    const requests = [];

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                Authorization: "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") {
                    return JSON.stringify({ id: 10 });
                }
                return null;
            }
        },
        sessionStorage: {
            getItem(key) {
                return values.get(key) ?? null;
            },
            setItem(key, value) {
                values.set(key, String(value));
            },
            removeItem(key) {
                values.delete(key);
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });
            throw new Error("No order request should be sent");
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);
    vm.runInContext("buyNowProductReady = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Stored checkout attempt is invalid."
        }
    );

    assert.equal(requests.length, 0);
    assert.equal(
        values.get("buyNowIdempotencyAttempt"),
        "{invalid-json"
    );
});

test("Buy Now refuses order creation when pending state cannot be saved", async () => {
    const values = new Map();
    const requests = [];
    let pendingWriteAttempts = 0;

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                Authorization: "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") {
                    return JSON.stringify({ id: 10 });
                }
                return null;
            }
        },
        sessionStorage: {
            getItem(key) {
                return values.get(key) ?? null;
            },
            setItem(key, value) {
                const attempt = JSON.parse(value);

                if (attempt.state === "pending") {
                    pendingWriteAttempts++;
                    throw new Error("Simulated pending storage failure");
                }

                values.set(key, String(value));
            },
            removeItem(key) {
                values.delete(key);
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });
            throw new Error("No order request should be sent");
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);
    vm.runInContext("buyNowProductReady = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Simulated pending storage failure"
        }
    );

    assert.equal(pendingWriteAttempts, 1);
    assert.equal(requests.length, 0);
    assert.equal(vm.runInContext("buyNowOrderId", context), null);

    const storedAttempt = JSON.parse(
        values.get("buyNowIdempotencyAttempt")
    );

    assert.equal(storedAttempt.userId, 10);
    assert.equal(storedAttempt.productId, 5);
    assert.equal(
        storedAttempt.key,
        "123e4567-e89b-42d3-a456-426614174000"
    );
    assert.equal(storedAttempt.state, undefined);
});

test("Buy Now blocks retries when confirmed state cannot be saved", async () => {
    const values = new Map();
    const requests = [];
    let confirmationWriteAttempts = 0;

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                Authorization: "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") {
                    return JSON.stringify({ id: 10 });
                }
                return null;
            }
        },
        sessionStorage: {
            getItem(key) {
                return values.get(key) ?? null;
            },
            setItem(key, value) {
                const attempt = JSON.parse(value);

                if (attempt.state === "confirmed") {
                    confirmationWriteAttempts++;
                    throw new Error("Simulated confirmation storage failure");
                }

                values.set(key, String(value));
            },
            removeItem(key) {
                values.delete(key);
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });

            return {
                ok: true,
                status: 201,
                async json() {
                    return { order_id: 123 };
                }
            };
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);
    vm.runInContext("buyNowProductReady = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Unable to save the confirmed Buy Now order."
        }
    );

    assert.equal(requests.length, 1);
    assert.equal(confirmationWriteAttempts, 1);

    assert.equal(
        vm.runInContext("buyNowCreationUncertain", context),
        true
    );

    assert.equal(
        vm.runInContext("buyNowOrderId", context),
        null
    );

    const storedAttempt = JSON.parse(
        values.get("buyNowIdempotencyAttempt")
    );

    assert.equal(storedAttempt.state, "pending");
    assert.equal(storedAttempt.userId, 10);
    assert.equal(storedAttempt.productId, 5);
    assert.equal(
        storedAttempt.key,
        requests[0].options.headers["Idempotency-Key"]
    );

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "The previous order-creation outcome is uncertain."
        }
    );

    assert.equal(requests.length, 1);
    assert.equal(confirmationWriteAttempts, 1);
});

test("Buy Now rejects silently lost confirmed state and blocks retries", async () => {
    const values = new Map();
    const requests = [];
    let confirmationWriteAttempts = 0;

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                Authorization: "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 10 });
                return null;
            }
        },
        sessionStorage: {
            getItem(key) {
                return values.get(key) ?? null;
            },
            setItem(key, value) {
                const attempt = JSON.parse(value);

                if (attempt.state === "confirmed") {
                    confirmationWriteAttempts++;
                    return;
                }

                values.set(key, String(value));
            },
            removeItem(key) {
                values.delete(key);
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });

            return {
                ok: true,
                status: 201,
                async json() {
                    return { order_id: 123 };
                }
            };
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);
    vm.runInContext("buyNowProductReady = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Unable to verify the confirmed Buy Now order."
        }
    );

    assert.equal(requests.length, 1);
    assert.equal(confirmationWriteAttempts, 1);

    assert.equal(
        vm.runInContext("buyNowCreationUncertain", context),
        true
    );

    assert.equal(
        vm.runInContext("buyNowOrderId", context),
        null
    );

    const storedAttempt = JSON.parse(
        values.get("buyNowIdempotencyAttempt")
    );

    assert.equal(storedAttempt.state, "pending");
    assert.equal(storedAttempt.userId, 10);
    assert.equal(storedAttempt.productId, 5);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "The previous order-creation outcome is uncertain."
        }
    );

    assert.equal(requests.length, 1);
    assert.equal(confirmationWriteAttempts, 1);
});

test("Buy Now rejects unexpected stored checkout states without creating orders", async () => {
    const invalidStates = [
        "failed",
        "cancelled",
        "completed",
        "",
        null,
        123,
        false
    ];

    for (const state of invalidStates) {
        const storedAttempt = {
            userId: 10,
            productId: 5,
            key: "123e4567-e89b-42d3-a456-426614174000",
            state
        };

        const originalValue = JSON.stringify(storedAttempt);
        const values = new Map([
            ["buyNowIdempotencyAttempt", originalValue]
        ]);

        const requests = [];

        const context = {
            URLSearchParams,
            ORDER_URL: "",
            authHeaders() {
                return {
                    "Content-Type": "application/json",
                    Authorization: "Bearer mock-jwt-token"
                };
            },
            window: {
                location: {
                    search: "?product_id=5",
                    href: "/checkout/?product_id=5"
                }
            },
            document: {
                addEventListener() {}
            },
            localStorage: {
                getItem(key) {
                    if (key === "access") return "mock-jwt-token";
                    if (key === "user") {
                        return JSON.stringify({ id: 10 });
                    }
                    return null;
                }
            },
            sessionStorage: {
                getItem(key) {
                    return values.get(key) ?? null;
                },
                setItem(key, value) {
                    values.set(key, String(value));
                },
                removeItem(key) {
                    values.delete(key);
                }
            },
            crypto: {
                randomUUID() {
                    return "123e4567-e89b-42d3-a456-426614174000";
                }
            },
            async fetch(url, options) {
                requests.push({ url, options });
                throw new Error("No order request should be sent");
            },
            console
        };

        vm.createContext(context);
        vm.runInContext(checkoutScript, context);
        vm.runInContext("buyNowProductReady = true", context);

        await assert.rejects(
            vm.runInContext("createBuyNowOrder()", context),
            {
                message:
                    "A previous Buy Now attempt must be resolved before retrying."
            }
        );

        assert.equal(
            requests.length,
            0,
            `Unexpected API request for state ${JSON.stringify(state)}`
        );

        assert.equal(
            values.get("buyNowIdempotencyAttempt"),
            originalValue
        );
    }
});

test("Buy Now blocks order creation when pending state silently fails to persist", async () => {
    const values = new Map();
    const requests = [];
    let pendingWriteAttempts = 0;

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                Authorization: "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") {
                    return JSON.stringify({ id: 10 });
                }
                return null;
            }
        },
        sessionStorage: {
            getItem(key) {
                return values.get(key) ?? null;
            },
            setItem(key, value) {
                const attempt = JSON.parse(value);

                if (attempt.state === "pending") {
                    pendingWriteAttempts++;
                    return;
                }

                values.set(key, String(value));
            },
            removeItem(key) {
                values.delete(key);
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });
            throw new Error("No order request should be sent");
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);
    vm.runInContext("buyNowProductReady = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Unable to verify the pending Buy Now checkout attempt."
        }
    );

    assert.equal(pendingWriteAttempts, 1);
    assert.equal(requests.length, 0);
    assert.equal(
        vm.runInContext("buyNowOrderId", context),
        null
    );

    const storedAttempt = JSON.parse(
        values.get("buyNowIdempotencyAttempt")
    );

    assert.equal(storedAttempt.userId, 10);
    assert.equal(storedAttempt.productId, 5);
    assert.equal(storedAttempt.state, undefined);
});

test("Buy Now network failure blocks another order-creation attempt", async () => {
    const requests = [];

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                "Authorization": "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 10 });
                return null;
            }
        },
        sessionStorage: {
            values: new Map(),
            getItem(key) {
                return this.values.has(key) ? this.values.get(key) : null;
            },
            setItem(key, value) {
                this.values.set(key, String(value));
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });

            // Simulate a lost connection after the request was sent.
            throw new Error("Simulated network failure");
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    vm.runInContext("buyNowProductReady = true", context);

    // First attempt: network failure.
    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Unable to confirm whether the Buy Now order was created."
        }
    );

    assert.equal(
        vm.runInContext("buyNowCreationUncertain", context),
        true
    );

    assert.equal(
        vm.runInContext("buyNowOrderId", context),
        null
    );

    assert.equal(requests.length, 1);
    assert.equal(requests[0].url, "/api/orders/");
    assert.equal(requests[0].options.method, "POST");

    // Second attempt must be rejected before another API request.
    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "The previous order-creation outcome is uncertain."
        }
    );

    // Still exactly one request.
    assert.equal(requests.length, 1);
});

test("Buy Now HTTP 500 marks creation uncertain and blocks retry", async () => {
    const requests = [];

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                "Authorization": "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 10 });
                return null;
            }
        },
        sessionStorage: {
            values: new Map(),
            getItem(key) {
                return this.values.has(key) ? this.values.get(key) : null;
            },
            setItem(key, value) {
                this.values.set(key, String(value));
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });

            if (url !== "/api/orders/") {
                throw new Error("Unexpected API request");
            }

            return {
                ok: false,
                status: 500
            };
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    vm.runInContext("buyNowProductReady = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Unable to confirm whether the Buy Now order was created."
        }
    );

    assert.equal(
        vm.runInContext("buyNowCreationUncertain", context),
        true
    );

    assert.equal(
        vm.runInContext("buyNowOrderId", context),
        null
    );

    assert.equal(requests.length, 1);
    assert.equal(requests[0].url, "/api/orders/");
    assert.equal(requests[0].options.method, "POST");

    // A second attempt must not send another request.
    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "The previous order-creation outcome is uncertain."
        }
    );

    assert.equal(requests.length, 1);
});

test("Buy Now HTTP 400 preserves pending state and blocks retries", async () => {
    const requests = [];

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                "Authorization": "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 10 });
                return null;
            }
        },
        sessionStorage: {
            values: new Map(),
            getItem(key) {
                return this.values.has(key) ? this.values.get(key) : null;
            },
            setItem(key, value) {
                this.values.set(key, String(value));
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });

            if (url !== "/api/orders/") {
                throw new Error("Unexpected API request");
            }

            return {
                ok: false,
                status: 400
            };
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    vm.runInContext("buyNowProductReady = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Unable to create the Buy Now order."
        }
    );

    assert.equal(
        vm.runInContext("buyNowCreationUncertain", context),
        false
    );

    assert.equal(
        vm.runInContext("buyNowOrderId", context),
        null
    );

    assert.equal(requests.length, 1);
    assert.equal(requests[0].url, "/api/orders/");
    assert.equal(requests[0].options.method, "POST");

    // A second attempt must not send another request.
    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "A previous Buy Now attempt must be resolved before retrying."
        }
    );

    assert.equal(requests.length, 1);

    const pending = JSON.parse(
        context.sessionStorage.getItem("buyNowIdempotencyAttempt")
    );

    assert.equal(pending.state, "pending");
    assert.equal(pending.userId, 10);
    assert.equal(pending.productId, 5);

    // Recreate the checkout script context to simulate a page refresh.
    const refreshed = {
        ...context,
        sessionStorage: context.sessionStorage
    };

    vm.createContext(refreshed);
    vm.runInContext(checkoutScript, refreshed);
    vm.runInContext("buyNowProductReady = true", refreshed);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", refreshed),
        {
            message: "A previous Buy Now attempt must be resolved before retrying."
        }
    );

    assert.equal(requests.length, 1);
});

test("Buy Now HTTP 409 conflict preserves pending state and blocks retries", async () => {
    const requests = [];

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                "Authorization": "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 10 });
                return null;
            }
        },
        sessionStorage: {
            values: new Map(),
            getItem(key) {
                return this.values.has(key) ? this.values.get(key) : null;
            },
            setItem(key, value) {
                this.values.set(key, String(value));
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });

            if (url !== "/api/orders/") {
                throw new Error("Unexpected API request");
            }

            return {
                ok: false,
                status: 409
            };
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    vm.runInContext("buyNowProductReady = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Unable to create the Buy Now order."
        }
    );

    assert.equal(
        vm.runInContext("buyNowCreationUncertain", context),
        false
    );

    assert.equal(
        vm.runInContext("buyNowOrderId", context),
        null
    );

    assert.equal(requests.length, 1);
    assert.equal(requests[0].url, "/api/orders/");
    assert.equal(requests[0].options.method, "POST");

    // A second attempt must not send another request.
    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "A previous Buy Now attempt must be resolved before retrying."
        }
    );

    assert.equal(requests.length, 1);

    const pending = JSON.parse(
        context.sessionStorage.getItem("buyNowIdempotencyAttempt")
    );

    assert.equal(pending.state, "pending");
    assert.equal(pending.userId, 10);
    assert.equal(pending.productId, 5);

    // Recreate the checkout script context to simulate a page refresh.
    const refreshed = {
        ...context,
        sessionStorage: context.sessionStorage
    };

    vm.createContext(refreshed);
    vm.runInContext(checkoutScript, refreshed);
    vm.runInContext("buyNowProductReady = true", refreshed);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", refreshed),
        {
            message: "A previous Buy Now attempt must be resolved before retrying."
        }
    );

    assert.equal(requests.length, 1);
});

test("Buy Now HTTP 401 unauthorized preserves pending state and blocks retries", async () => {
    const requests = [];

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                "Authorization": "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 10 });
                return null;
            }
        },
        sessionStorage: {
            values: new Map(),
            getItem(key) {
                return this.values.has(key) ? this.values.get(key) : null;
            },
            setItem(key, value) {
                this.values.set(key, String(value));
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });

            if (url !== "/api/orders/") {
                throw new Error("Unexpected API request");
            }

            return {
                ok: false,
                status: 401
            };
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    vm.runInContext("buyNowProductReady = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Unable to create the Buy Now order."
        }
    );

    assert.equal(
        vm.runInContext("buyNowCreationUncertain", context),
        false
    );

    assert.equal(
        vm.runInContext("buyNowOrderId", context),
        null
    );

    assert.equal(requests.length, 1);
    assert.equal(requests[0].url, "/api/orders/");
    assert.equal(requests[0].options.method, "POST");

    // A second attempt must not send another request.
    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "A previous Buy Now attempt must be resolved before retrying."
        }
    );

    assert.equal(requests.length, 1);

    const pending = JSON.parse(
        context.sessionStorage.getItem("buyNowIdempotencyAttempt")
    );

    assert.equal(pending.state, "pending");
    assert.equal(pending.userId, 10);
    assert.equal(pending.productId, 5);

    // Recreate the checkout script context to simulate a page refresh.
    const refreshed = {
        ...context,
        sessionStorage: context.sessionStorage
    };

    vm.createContext(refreshed);
    vm.runInContext(checkoutScript, refreshed);
    vm.runInContext("buyNowProductReady = true", refreshed);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", refreshed),
        {
            message: "A previous Buy Now attempt must be resolved before retrying."
        }
    );

    assert.equal(requests.length, 1);
});

test("Buy Now HTTP 403 forbidden preserves pending state and blocks retries", async () => {
    const requests = [];

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                "Authorization": "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 10 });
                return null;
            }
        },
        sessionStorage: {
            values: new Map(),
            getItem(key) {
                return this.values.has(key) ? this.values.get(key) : null;
            },
            setItem(key, value) {
                this.values.set(key, String(value));
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });

            if (url !== "/api/orders/") {
                throw new Error("Unexpected API request");
            }

            return {
                ok: false,
                status: 403
            };
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    vm.runInContext("buyNowProductReady = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Unable to create the Buy Now order."
        }
    );

    assert.equal(
        vm.runInContext("buyNowCreationUncertain", context),
        false
    );

    assert.equal(
        vm.runInContext("buyNowOrderId", context),
        null
    );

    assert.equal(requests.length, 1);
    assert.equal(requests[0].url, "/api/orders/");
    assert.equal(requests[0].options.method, "POST");

    // A second attempt must not send another request.
    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "A previous Buy Now attempt must be resolved before retrying."
        }
    );

    assert.equal(requests.length, 1);

    const pending = JSON.parse(
        context.sessionStorage.getItem("buyNowIdempotencyAttempt")
    );

    assert.equal(pending.state, "pending");
    assert.equal(pending.userId, 10);
    assert.equal(pending.productId, 5);

    // Recreate the checkout script context to simulate a page refresh.
    const refreshed = {
        ...context,
        sessionStorage: context.sessionStorage
    };

    vm.createContext(refreshed);
    vm.runInContext(checkoutScript, refreshed);
    vm.runInContext("buyNowProductReady = true", refreshed);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", refreshed),
        {
            message: "A previous Buy Now attempt must be resolved before retrying."
        }
    );

    assert.equal(requests.length, 1);
});

test("Buy Now invalid order ID marks creation uncertain and blocks retry", async () => {
    const requests = [];

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                "Authorization": "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 10 });
                return null;
            }
        },
        sessionStorage: {
            values: new Map(),
            getItem(key) {
                return this.values.has(key) ? this.values.get(key) : null;
            },
            setItem(key, value) {
                this.values.set(key, String(value));
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });

            if (url !== "/api/orders/") {
                throw new Error("Unexpected API request");
            }

            return {
                ok: true,
                status: 200,
                async json() {
                    return {
                        message: "Item added to cart",
                        order_id: null
                    };
                }
            };
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    vm.runInContext("buyNowProductReady = true", context);

    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Invalid Buy Now order ID returned by the server."
        }
    );

    assert.equal(
        vm.runInContext("buyNowCreationUncertain", context),
        true
    );

    assert.equal(
        vm.runInContext("buyNowOrderId", context),
        null
    );

    assert.equal(requests.length, 1);
    assert.equal(requests[0].url, "/api/orders/");
    assert.equal(requests[0].options.method, "POST");

    // A second attempt must not create another order.
    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "The previous order-creation outcome is uncertain."
        }
    );

    assert.equal(requests.length, 1);
});

test("Buy Now malformed JSON marks creation uncertain and blocks retry", async () => {
    const requests = [];

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                "Authorization": "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 10 });
                return null;
            }
        },
        sessionStorage: {
            values: new Map(),
            getItem(key) {
                return this.values.has(key) ? this.values.get(key) : null;
            },
            setItem(key, value) {
                this.values.set(key, String(value));
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });

            if (url !== "/api/orders/") {
                throw new Error("Unexpected API request");
            }

            return {
                ok: true,
                status: 200,
                async json() {
                    throw new SyntaxError("Unexpected end of JSON input");
                }
            };
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    vm.runInContext("buyNowProductReady = true", context);

    // First attempt receives an unreadable response.
    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "Unable to confirm the created Buy Now order ID."
        }
    );

    assert.equal(
        vm.runInContext("buyNowCreationUncertain", context),
        true
    );

    assert.equal(
        vm.runInContext("buyNowOrderId", context),
        null
    );

    assert.equal(requests.length, 1);
    assert.equal(requests[0].url, "/api/orders/");
    assert.equal(requests[0].options.method, "POST");

    // A second attempt must be blocked.
    await assert.rejects(
        vm.runInContext("createBuyNowOrder()", context),
        {
            message: "The previous order-creation outcome is uncertain."
        }
    );

    // No duplicate POST request.
    assert.equal(requests.length, 1);
});

test("Buy Now simultaneous calls share one order-creation request", async () => {
    const requests = [];

    let releaseResponse;

    const responseGate = new Promise(resolve => {
        releaseResponse = resolve;
    });

    const context = {
        URLSearchParams,
        ORDER_URL: "",
        authHeaders() {
            return {
                "Content-Type": "application/json",
                "Authorization": "Bearer mock-jwt-token"
            };
        },
        window: {
            location: {
                search: "?product_id=5",
                href: "/checkout/?product_id=5"
            }
        },
        document: {
            addEventListener() {}
        },
        localStorage: {
            getItem(key) {
                if (key === "access") return "mock-jwt-token";
                if (key === "user") return JSON.stringify({ id: 10 });
                return null;
            }
        },
        sessionStorage: {
            values: new Map(),
            getItem(key) {
                return this.values.has(key) ? this.values.get(key) : null;
            },
            setItem(key, value) {
                this.values.set(key, String(value));
            }
        },
        crypto: {
            randomUUID() {
                return "123e4567-e89b-42d3-a456-426614174000";
            }
        },
        async fetch(url, options) {
            requests.push({ url, options });

            if (url !== "/api/orders/") {
                throw new Error("Unexpected API request");
            }

            // Keep the first request pending.
            await responseGate;

            return {
                ok: true,
                status: 200,
                async json() {
                    return {
                        message: "Item added to cart",
                        order_id: 123
                    };
                }
            };
        },
        console
    };

    vm.createContext(context);
    vm.runInContext(checkoutScript, context);

    vm.runInContext("buyNowProductReady = true", context);

    // Start two calls before the first response arrives.
    const first = vm.runInContext("createBuyNowOrder()", context);
    const second = vm.runInContext("createBuyNowOrder()", context);

    // Both calls must share exactly the same promise.
    assert.strictEqual(first, second);

    // Only one POST request should have started.
    assert.equal(requests.length, 1);
    assert.equal(requests[0].url, "/api/orders/");
    assert.equal(requests[0].options.method, "POST");

    // Release the mocked server response.
    releaseResponse();

    const results = await Promise.all([first, second]);

    assert.deepEqual(results, [123, 123]);

    assert.equal(
        vm.runInContext("buyNowOrderId", context),
        123
    );

    assert.equal(
        vm.runInContext("buyNowCreationUncertain", context),
        false
    );

    // Still only one POST request.
    assert.equal(requests.length, 1);

    // A later call must reuse the stored order ID.
    const third = await vm.runInContext(
        "createBuyNowOrder()", context
    );

    assert.equal(third, 123);
    assert.equal(requests.length, 1);
});
