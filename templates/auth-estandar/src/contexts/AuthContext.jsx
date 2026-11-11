import { createContext, useContext, useState, useCallback, useEffect, useRef } from "react";
import { getMsalInstance, loginRequest } from "../config/msal";
import { aadstsDeErrorMsal, causaProbable } from "../auth/erroresEntra";

// Contexto de autenticación estándar de AGP: mismo comportamiento que el login de la Mesa (restauración silenciosa de sesión, login con ventana
// emergente, id_token vigente para la API), sin lo propio de la Mesa (equipos de IT, vista previa, búsqueda en el directorio).
// Expone: currentUser {email, name}, roles (claim `roles` del token: «Admin» / «Usuario» los asigna IT desde la Mesa), isAdmin, authChecking,
// loginError, loginLoading, login(), logout(), getAuthToken().

// acquireTokenSilent puede devolver un idToken ya vencido: como la API usa el idToken como credencial Bearer, se verifica su «exp» a mano.
function isExpiredOrExpiringSoon(idToken, bufferSeconds = 60) {
  try {
    const payload = idToken.split(".")[1];
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    const { exp } = JSON.parse(json);
    return !exp || exp * 1000 < Date.now() + bufferSeconds * 1000;
  } catch (_) {
    return true; // si no se puede leer el token, mejor pedir uno nuevo que arriesgarse
  }
}

// Mensaje claro por código de error de MSAL (el popup de MSAL 5 falla de formas distintas; «Error al iniciar sesión» a secas no dice qué hacer).
// Nunca se muestra el texto libre del error del proveedor (puede traer datos de la respuesta OAuth): solo el código AADSTS y su causa probable.
export function mensajeDeErrorLogin(e) {
  const codigo = e?.errorCode || "";
  if (codigo === "interaction_in_progress") return "Ya hay una ventana de Microsoft abierta. Completa ese acceso.";
  if (codigo === "monitor_popup_timeout" || codigo === "hash_empty_error") {
    return "Microsoft no pudo devolver el acceso a la aplicación. Cierra la ventana de acceso e intenta de nuevo; si persiste, avisa a TI (revisa la página puente /auth/redirect).";
  }
  if (codigo === "popup_window_error") return "El navegador bloqueó la ventana de Microsoft. Permite ventanas emergentes para esta aplicación.";
  // Error de Entra: solo la causa y el código AADSTS, nunca el texto libre del proveedor.
  const aadsts = aadstsDeErrorMsal(e);
  const causa = causaProbable({ error: codigo || e?.subError || "", aadsts });
  if (causa || aadsts) return `${causa || "Microsoft rechazó el acceso."}${aadsts ? ` (${aadsts})` : ""}`;
  return "Error al iniciar sesión. Intenta de nuevo.";
}

function esCancelacion(e) {
  return e?.errorCode === "user_cancelled" || Boolean(e?.message?.includes("user_cancelled"));
}

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [roles, setRoles] = useState([]);
  const [loginError, setLoginError] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);
  // Arranca en true: mientras se restaura la sesión en silencio se muestra «cargando» y no la pantalla de login (si no, cada recarga la mostraría).
  const [authChecking, setAuthChecking] = useState(true);
  const accountRef = useRef(null);
  const loginEnCurso = useRef(false);   // dos clics seguidos abren UNA sola ventana de Microsoft (si no, MSAL falla con interaction_in_progress)

  // Camino único para el login interactivo y la restauración silenciosa: nunca se desincronizan.
  const applyAccount = useCallback((account) => {
    const email = account.username.toLowerCase();
    accountRef.current = account;
    setCurrentUser({ email, name: account.name || email.split("@")[0] });
    setRoles(Array.isArray(account.idTokenClaims?.roles) ? account.idTokenClaims.roles : []);
  }, []);

  // Si MSAL ya tiene una cuenta en caché y el token se puede renovar, se entra directo. Si no, se queda deslogueado y aparece LoginScreen;
  // no se abre un popup automático al cargar porque los navegadores lo bloquean si no viene de un clic.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const msal = getMsalInstance();
      const account = msal.getActiveAccount() || msal.getAllAccounts()[0];
      if (!account) {
        if (!cancelled) setAuthChecking(false);
        return;
      }
      try {
        const result = await msal.acquireTokenSilent({ ...loginRequest, account });
        msal.setActiveAccount(result.account);
        if (!cancelled) applyAccount(result.account);
      } catch (_) {
        // sesión no recuperable en silencio: LoginScreen resuelve el resto
      } finally {
        if (!cancelled) setAuthChecking(false);
      }
    })();
    return () => { cancelled = true; };
  }, [applyAccount]);

  const login = useCallback(async () => {
    if (loginEnCurso.current) return;
    loginEnCurso.current = true;
    setLoginError("");
    setLoginLoading(true);
    try {
      const msal = getMsalInstance();
      const result = await msal.loginPopup(loginRequest);
      msal.setActiveAccount(result.account);
      applyAccount(result.account);
    } catch (e) {
      if (!esCancelacion(e)) setLoginError(mensajeDeErrorLogin(e));
    } finally {
      loginEnCurso.current = false;
      setLoginLoading(false);
    }
  }, [applyAccount]);

  const logout = useCallback(() => {
    accountRef.current = null;
    setCurrentUser(null);
    setRoles([]);
    try { getMsalInstance().logoutPopup(); } catch (_) {}
  }, []);

  // id_token vigente para el encabezado Authorization: Bearer de la API (silencioso; solo vuelve a mostrar el popup si la sesión no es recuperable).
  const getAuthToken = useCallback(async () => {
    const msal = getMsalInstance();
    const account = accountRef.current || msal.getActiveAccount() || msal.getAllAccounts()[0];
    if (!account) return null;
    try {
      let result = await msal.acquireTokenSilent({ ...loginRequest, account });
      if (isExpiredOrExpiringSoon(result.idToken)) {
        result = await msal.acquireTokenSilent({ ...loginRequest, account, forceRefresh: true });
      }
      return result.idToken;
    } catch (_) {
      try {
        const result = await msal.acquireTokenPopup({ ...loginRequest, account });
        return result.idToken;
      } catch (_e) {
        return null;
      }
    }
  }, []);

  return (
    <AuthContext.Provider value={{
      currentUser, roles, isAdmin: roles.includes("Admin"), authChecking, loginError, loginLoading,
      login, logout, getAuthToken,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
