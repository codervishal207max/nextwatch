// Ends the session completely: nothing of the previous user stays in the browser.
export function logout(navigate) {
  localStorage.removeItem("nw_token");
  localStorage.removeItem("nw_auth");
  sessionStorage.clear();
  // stop Google from silently signing the previous account back in
  window.google?.accounts?.id?.disableAutoSelect?.();
  navigate("/login", { replace: true });
}