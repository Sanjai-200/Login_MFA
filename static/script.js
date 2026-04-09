import { auth } from "/static/firebase.js";

import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword
} from "https://www.gstatic.com/firebasejs/12.11.0/firebase-auth.js";

import { doc, setDoc, getDoc } from "https://www.gstatic.com/firebasejs/12.11.0/firebase-firestore.js";

// ROUTES
window.goSignup = () => window.location = "/signup";
window.goLogin = () => window.location = "/";

// DEVICE
function getDevice() {
  if (
    navigator.userAgentData?.mobile ||
    /Android|iPhone|iPad|iPod/i.test(navigator.userAgent) ||
    window.innerWidth <= 768
  ) return "Mobile";

  return "Laptop";
}

// ✅ SINGLE CLEAN LOCATION FUNCTION
async function getLocation() {
  try {
    const res = await fetch("https://ipwho.is/?t=" + Date.now(), { cache: "no-store" });
    const data = await res.json();
    if (data.success && data.country) return data.country;
  } catch {}

  try {
    const ipRes = await fetch("https://api.ipify.org?format=json");
    const ipData = await ipRes.json();

    const res = await fetch(`https://ipapi.co/${ipData.ip}/json/`);
    const data = await res.json();

    if (data.country_name) return data.country_name;
  } catch {}

  return "Unknown";
}

// ================= SIGNUP =================
window.signup = async () => {
  const username = document.getElementById("username").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  try {
    const user = await createUserWithEmailAndPassword(auth, email, password);

    const { db } = await import("/static/firebase.js");
    await setDoc(doc(db, "users", user.user.uid), { username, email });

    alert("Account created successfully!");
    window.location = "/";

  } catch (e) {
    document.getElementById("msg").innerText = e.message;
  }
};

// ================= LOGIN =================
window.login = async () => {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  let failedAttempts = parseInt(localStorage.getItem(email + "_failedAttempts")) || 0;

  try {
    const userCred = await signInWithEmailAndPassword(auth, email, password);

    localStorage.setItem("uid", userCred.user.uid);
    localStorage.setItem("email", userCred.user.email);

    const device = getDevice();
    const location = await getLocation();
    const time = new Date().toLocaleTimeString();

    const { db } = await import("/static/firebase.js");

    const ref = doc(db, "activity", userCred.user.uid);
    const snap = await getDoc(ref);

    let loginCount = 1;
    let totalFailed = failedAttempts;

    if (snap.exists()) {
      const old = snap.data();

      // ✅ FIX loginCount
      loginCount = (old.loginCount || 0) + 1;

      // ✅ FIX failedAttempts accumulation
      totalFailed = (old.failedAttempts || 0) + failedAttempts;
    }

    // ML CALL
    const response = await fetch("/predict", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        device,
        location,
        loginCount,
        failedAttempts,
        time
      })
    });

    const result = await response.json();

    if (result.prediction === 0) {

      // ✅ STORE FINAL VALUES (NO DUPLICATE LOGIC)
      await setDoc(ref, {
        email,
        location,
        device,
        date: new Date().toISOString().split("T")[0],
        time,
        loginCount,
        failedAttempts: totalFailed
      });

      // ✅ RESET AFTER SUCCESS
      localStorage.setItem(email + "_failedAttempts", 0);

      window.location = "/home";

    } else {
      localStorage.setItem(email + "_finalFailedAttempts", failedAttempts);

      const otp = Math.floor(100000 + Math.random() * 900000).toString();

      localStorage.setItem("otp", otp);
      localStorage.setItem("otpTime", Date.now());

      // ✅ KEEP YOUR OTP EMAIL SYSTEM
      await fetch("/send-otp", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          email: userCred.user.email,
          otp: otp
        })
      });

      window.location = "/otp";
    }

  } catch {
    failedAttempts++;
    localStorage.setItem(email + "_failedAttempts", failedAttempts);

    document.getElementById("msg").innerText =
      "Login failed ❌ (" + failedAttempts + ")";
  }
};

// ================= OTP =================
async function verifyOTP() {
  const entered = document.getElementById("otpInput").value.trim();
  const otp = localStorage.getItem("otp");

  if (entered === otp) {
    window.location = "/home";
  } else {
    document.getElementById("msg").innerText = "Wrong OTP ❌";
  }
}

async function resendOTP() {
  const newOtp = Math.floor(100000 + Math.random() * 900000).toString();
  localStorage.setItem("otp", newOtp);

  const email = localStorage.getItem("email");

  await fetch("/send-otp", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      email,
      otp: newOtp
    })
  });

  document.getElementById("msg").innerText = "New OTP sent 📩";
}

// EVENTS
document.getElementById("verifyBtn")?.addEventListener("click", verifyOTP);
document.getElementById("resendBtn")?.addEventListener("click", resendOTP);
