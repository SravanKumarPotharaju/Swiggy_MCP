// SmartFlow API Client
const API_BASE = '/api/v1';

const api = {
  async getInitialState() {
    const res = await fetch(`${API_BASE}/agent/initial-state`);
    return await res.json();
  },

  async sendChatMessage(message, userPhone = 'user_web') {
    const res = await fetch(`${API_BASE}/agent/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, user_phone: userPhone }),
    });
    return await res.json();
  },

  async getCart() {
    const res = await fetch(`${API_BASE}/cart`);
    return await res.json();
  },

  async updateCart(items, restaurantId = '288893', restaurantName = 'Meghana Foods') {
    const res = await fetch(`${API_BASE}/cart`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        restaurant_id: restaurantId,
        restaurant_name: restaurantName,
        items: items,
      }),
    });
    return await res.json();
  },

  async clearCart() {
    const res = await fetch(`${API_BASE}/cart`, { method: 'DELETE' });
    return await res.json();
  },

  async getCartSummary() {
    const res = await fetch(`${API_BASE}/cart/summary`);
    return await res.json();
  },

  async getPaymentOptions() {
    const res = await fetch(`${API_BASE}/payments/options`);
    return await res.json();
  },

  async checkout(paymentMethod = 'UPI', generateUPIQR = true, note = '') {
    const res = await fetch(`${API_BASE}/orders/checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        payment_method: paymentMethod,
        generate_upi_qr: generateUPIQR,
        note_to_restaurant: note,
      }),
    });
    return await res.json();
  },

  async checkPaymentStatus(paasId, orderId) {
    const res = await fetch(`${API_BASE}/payments/${paasId}/status?order_id=${orderId || ''}`);
    return await res.json();
  },

  async confirmOrder(orderId) {
    const res = await fetch(`${API_BASE}/orders/${orderId}/confirm`, {
      method: 'POST',
    });
    return await res.json();
  },

  async getOrders(count = 5) {
    const res = await fetch(`${API_BASE}/orders?count=${count}`);
    return await res.json();
  },

  async getFrequentOrders() {
    const res = await fetch(`${API_BASE}/orders/frequent`);
    return await res.json();
  },

  async trackOrder(orderId = '') {
    const url = orderId ? `${API_BASE}/orders/${orderId}/track` : `${API_BASE}/orders/249475187182313/track`;
    const res = await fetch(url);
    return await res.json();
  },

  async triggerAutomatedCall(phoneNumber = null, message = null) {
    const res = await fetch(`${API_BASE}/agent/call-user`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone_number: phoneNumber, message }),
    });
    return await res.json();
  },

  async setActiveAddress(address) {
    const res = await fetch(`${API_BASE}/agent/address`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ address }),
    });
    return await res.json();
  },

  // --- SWIGGY INSTAMART GROCERY APIS ---
  async searchInstamartProducts(query, addressId = null, limit = 8) {
    let url = `${API_BASE}/instamart/products?query=${encodeURIComponent(query)}&limit=${limit}`;
    if (addressId) url += `&address_id=${encodeURIComponent(addressId)}`;
    const res = await fetch(url);
    return await res.json();
  },

  async getInstamartGoToItems(addressId = null) {
    let url = `${API_BASE}/instamart/go-to-items`;
    if (addressId) url += `?address_id=${encodeURIComponent(addressId)}`;
    const res = await fetch(url);
    return await res.json();
  },

  async getInstamartCart() {
    const res = await fetch(`${API_BASE}/instamart/cart`);
    return await res.json();
  },

  async updateInstamartCart(items, addressId = null) {
    const res = await fetch(`${API_BASE}/instamart/cart`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items, address_id: addressId }),
    });
    return await res.json();
  },

  async addOrUpdateInstamartItem(spinId, quantityDelta = null, quantity = null) {
    const res = await fetch(`${API_BASE}/instamart/cart/item`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ spinId, quantity_delta: quantityDelta, quantity }),
    });
    return await res.json();
  },

  async clearInstamartCart() {
    const res = await fetch(`${API_BASE}/instamart/cart`, { method: 'DELETE' });
    return await res.json();
  },

  async checkoutInstamart(paymentMethod = 'UPI', userConfirmed = true) {
    const res = await fetch(`${API_BASE}/instamart/checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        payment_method: paymentMethod,
        user_confirmed: userConfirmed,
      }),
    });
    return await res.json();
  },

  async confirmInstamartOrder(orderId) {
    const res = await fetch(`${API_BASE}/instamart/orders/${orderId}/confirm`, {
      method: 'POST',
    });
    return await res.json();
  },

  async trackInstamartOrder(orderId) {
    const res = await fetch(`${API_BASE}/instamart/orders/${orderId}/track`);
    return await res.json();
  },

  async getAuthStatus() {
    const res = await fetch(`${API_BASE}/auth/status`);
    return await res.json();
  },

  async loginSwiggy() {
    const res = await fetch(`${API_BASE}/auth/login`);
    return await res.json();
  },

  async sendSwiggyOtp(phone, countryCode = "+91") {
    const res = await fetch(`${API_BASE}/auth/send-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, country_code: countryCode })
    });
    return await res.json();
  },

  async verifySwiggyOtp(phone, otp) {
    const res = await fetch(`${API_BASE}/auth/verify-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, otp })
    });
    return await res.json();
  },
};
